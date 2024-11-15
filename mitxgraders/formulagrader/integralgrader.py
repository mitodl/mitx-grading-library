"""
integralgrader.py

Contains IntegralGrader, a class for grading an integral problem, consisting of lower
and upper limits, and integration variable, and an integrand.
"""
from functools import wraps
from numpy import real, imag
from abc import abstractproperty
from numbers import Number

from voluptuous import Required, Any, Extra

from mitxgraders.baseclasses import AbstractGrader
from mitxgraders.comparers import equality_comparer
from mitxgraders.exceptions import (InvalidInput, ConfigError,
                                    StudentFacingError, MissingInput, MITxError)
from mitxgraders.helpers.validatorfuncs import Positive, NonNegative, PercentageString
from mitxgraders.helpers.math_helpers import MathMixin
from mitxgraders.helpers.calc import evaluator, DEFAULT_VARIABLES, parse
from mitxgraders.helpers.calc.mathfuncs import merge_dicts


__all__ = ['IntegralGrader', 'SumGrader']

def is_valid_variable_name(varname):
    """
    Tests if a variable name is valid.

    Variable names must:
        - begin with an alphabetic character
    Variable names can:
        - contain arbitrarily many single quotes as their final characters
            x or x' or x''' but not x''yz
        - contain any sequence of alphanumeric characters and underscores between
            their first character and ending single quotes

    Usage:
    >>> is_valid_variable_name('x')
    True
    >>> is_valid_variable_name('x_')
    True
    >>> is_valid_variable_name('_x')
    False
    >>> is_valid_variable_name('df_1')
    True
    >>> is_valid_variable_name("cat''")
    True
    >>> is_valid_variable_name("cat''dog")
    False
    """
    varname_pieces = varname.split("'")
    if len(varname_pieces) > 1:
        if not all(piece == "" for piece in varname_pieces[1:]):
            return False
    front = varname_pieces[0]
    return front[0].isalpha() and front.replace("_", "").isalnum()


def transform_list_to_dict(thelist, thedefaults, key_to_index_map):
    """
    Transform thelist into a dict with keys according to key_map and defaults
    from thedefaults.
    """
    return {
        key: thelist[key_to_index_map[key]]
        if key_to_index_map[key] is not None else thedefaults[key]
        for key in key_to_index_map
    }

class IntegrationError(StudentFacingError):
    """Represents an error associated with integration"""

class SummationError(StudentFacingError):
    """Represents an error associated with summation"""

def check_output_is_real(func, error, message):
    """Decorate a function to check that its output is real or raise error with specifed message."""

    @wraps(func)
    def wrapper(x):
        output = func(x)
        if not isinstance(output, float):
            raise error(message)
        return output

    return wrapper

class SummationGraderBase(AbstractGrader, MathMixin):
    """
    Abstract base class that incorporates the common components of IntegralGrader and SumGrader.
    """
    default_variables = merge_dicts(DEFAULT_VARIABLES, {'infty': float('inf')})

    @abstractproperty
    @property
    def wording(self):
        """Returns a dictionary with keys 'noun' and 'adjective' that describe the function of this class"""
    
    def __init__(self, config=None, **kwargs):
        super(SummationGraderBase, self).__init__(config, **kwargs)
    
        # Validate input positions
        self.true_input_positions = self.validate_input_positions(self.config['input_positions'])
    
        # Perform standard math validation
        self.validate_math_config()

    @staticmethod
    def validate_input_positions(input_positions):
        """
        Ensure that the provided student input positions are valid.
        """
        used_positions_list = [input_positions[key] for key in input_positions
                               if input_positions[key] is not None]
        used_positions_set = set(used_positions_list)
        
        # Ensure no position is used twice
        if len(used_positions_list) > len(used_positions_set):
            raise ConfigError("Key input_positions has repeated indices.")
        
        # Ensure positions are sequential, starting at 1
        if used_positions_set != set(range(1, len(used_positions_set) + 1)):
            msg = "Key input_positions values must be consecutive positive integers starting at 1"
            raise ConfigError(msg)
        
        return {
            key: input_positions[key] - 1  # Turn 1-based indexing into 0-based indexing
            if input_positions[key] is not None else None
            for key in input_positions
        }

    def get_limits_and_funcs(self, expression, lower_str, upper_str, varscope, funcscope):
        """
        Evals lower/upper limits and gets the functions used in limits and integrand/summand.
        """
        lower, lower_used = evaluator(lower_str,
                                      variables=varscope,
                                      functions=funcscope,
                                      suffixes=self.suffixes,
                                      allow_inf=True)
        upper, upper_used = evaluator(upper_str,
                                      variables=varscope,
                                      functions=funcscope,
                                      suffixes=self.suffixes,
                                      allow_inf=True)
        expression_used = parse(expression)
        
        used_funcs = lower_used.functions_used.union(upper_used.functions_used, expression_used.functions_used)
        
        return lower, upper, used_funcs

    def structure_and_validate_input(self, student_input):
        """Validates and structures the received input against the expected input based on the configuration"""
        used_inputs = [key for key in self.true_input_positions
                       if self.true_input_positions[key] is not None]
        if len(used_inputs) != len(student_input):
            # This is a ConfigError because it should only be trigged if author
            # included wrong number of inputs in the <customresponse> problem.
            sorted_inputs = sorted(used_inputs, key=lambda x: self.true_input_positions[x])
            msg = ("Expected {expected} student inputs but found {found}. "
                   "Inputs should  appear in order {order}.")
            raise ConfigError(msg.format(expected=len(used_inputs),
                                         found=len(student_input),
                                         order=sorted_inputs)
                              )

        structured_input = transform_list_to_dict(student_input,
                                                  self.config['answers'],
                                                  self.true_input_positions)

        return structured_input

    def validate_user_dummy_variable(self, varname):
        """Check the dummy variable has no other meaning and is a valid variable name"""
        if varname in self.functions or varname in self.random_funcs or varname in self.constants:
            msg = ("Cannot use {varname} as {adj} variable; it is already has "
                   "another meaning in this problem.")
            raise InvalidInput(msg.format(varname=varname, adj=self.wording['adjective']))

        if not is_valid_variable_name(varname):
            msg = ("{adj} variable {varname} is an invalid variable name."
                   "Variable name should begin with a letter and contain alphanumeric"
                   "characters or underscores thereafter, but may end in single quotes.")
            raise InvalidInput(msg.format(varname=varname, adj=self.wording['adjective'].title()))

    def check(self, answers, student_input, **kwargs):
        """Validates and cleans student_input, then checks response and handles errors"""
        answers = self.config['answers'] if answers is None else answers

        # If only a single input has been provided, wrap it in a list
        # This is possible if only the integrand/summand is required from the student
        if not isinstance(student_input, list):
            student_input = [student_input]

        # Validate the input
        structured_input = self.structure_and_validate_input(student_input)
        for key in structured_input:
            if structured_input[key] == '':
                msg = "Please enter a value for {key}, it cannot be empty."
                raise MissingInput(msg.format(key=key))
        self.validate_user_dummy_variable(structured_input[self.wording['adjective'] + '_variable'])

        # Now perform the computations
        try:
            return self.check_math_response(answers, structured_input)
        except IntegrationError as error:
            msg = "There appears to be an error with the {} you entered: {}"
            raise IntegrationError(msg.format(self.wording['noun'], str(error)))

    def raw_check(self, answer, student_input, **kwargs):
        """Perform the numerical check of student_input vs answer"""
        # This is a simpler version of the raw_check function from FormulaGrader,
        # which is complicated by sibling variables and comparers
        
        # Generate samples
        var_samples, func_samples = self.gen_var_and_func_samples(answer, student_input)
        
        # Evaluate integrals/sums
        (instructor_evals,
         student_evals,
         functions_used) = self.gen_evaluations(answer, student_input, var_samples, func_samples)
        
        # Compare results
        results = self.compare_evaluations(instructor_evals, student_evals,
                                           equality_comparer, self.get_comparer_utils())
        
        # Consolidate results across multiple samples
        consolidated = self.consolidate_results(results, None, self.config['failable_evals'])
        
        return consolidated, functions_used

class IntegralGrader(SummationGraderBase):
    """
    Grades a student-entered integral by comparing numerically with
    an author-specified integral.

    WARNINGS
    ========
    This grader numerically evaluates the student- and instructor-specified
    integrals using scipy.integrate.quad. This quadrature-based integration
    technique is efficient and flexible. It handles many integrals with
    poles in the integrand and can integrate over infinite domains.

    However, some integrals may behave badly. These include, but are not limited to,
    the following:

        - integrals with highly oscillatory integrands
        - integrals that evaluate analytically to zero

    In some cases, problems might be avoided by using the integrator_options
    configuration key to provide extra instructions to scipy.integrate.quad.

    Additionally, take care that the integration limits are real-valued.
    For example, if sqrt(1-a^2) is an integration limit, the sampling range
    for variable 'a' must guarantee that the limit sqrt(1-a^2) is real. By
    default, variables sample from the real interval [1,3].

    Configuration Options
    =====================
        answers (dict, required): Specifies author's answer. Has required keys lower,
            upper, integrand, integration_variable, which each take string values.

        complex_integrand (bool): Specifies whether the integrand is allowed to
            be complex-valued. Defaults to False.

        input_positions (dict): Specifies which integration parameters the student
            is required to enter. The default value of input_positions is:

                input_positions = {
                    'lower': 1,
                    'upper': 2,
                    'integrand': 3,
                    'integration_variable': 4
                }

            and requires students to enter all four parameters in the indicated
            order.

            If the author overrides the default input_positions value, any subset
            of the keys ('lower', 'upper', 'integrand', 'integration_variable')
            may be specified. Key values should be

                - continuous integers starting at 1, or
                - (default) None, indicating that the parameter is not entered by student

            For example,

                input_positions = {
                    'lower': 1,
                    'upper': 2,
                    'integrand': 3
                }

            indicates that the problem has 3 input boxes which represent the
            lower limit, upper limit, and integrand in that order. The
            integration_variable is NOT entered by student and is instead the
            value specified by author in 'answers'.

        integrator_options (dict): A dictionary of keyword-arguments that are passed
            directly to scipy.integrate.quad. See
            https://docs.scipy.org/doc/scipy-0.16.1/reference/generated/scipy.integrate.quad.html
            for more information.

    Additional Configuration Options
    ================================
    The configuration keys below are the same as used by FormulaGrader and
    have the same defaults, except where specified
        user_constants: same as FormulaGrader, but with additional default 'infty'
        whitelist
        blacklist
        tolerance
        samples (default: 1)
        variables
        sample_from
        failable_evals
        numbered_vars
        instructor_vars
        forbidden_strings
        forbidden_message
        required_functions
        metric_suffixes
    """

    @property
    def wording(self):
        return {
            'noun': 'integral',
            'adjective': 'integration'
        }

    @property
    def schema_config(self):
        """Define the configuration options for IntegralGrader"""
        # Construct the default AbstractGrader schema
        schema = super(IntegralGrader, self).schema_config
        # Apply the default math schema
        schema = schema.extend(self.math_config_options)
        # Append IntegralGrader-specific options
        default_input_positions = {
            'lower': 1,
            'upper': 2,
            'integrand': 3,
            'integration_variable': 4
        }
        return schema.extend({
            Required('answers'): {
                Required('lower'): str,
                Required('upper'): str,
                Required('integrand'): str,
                Required('integration_variable'): str
            },
            Required('input_positions', default=default_input_positions): {
                Required('lower', default=None): Any(None, Positive(int)),
                Required('upper', default=None): Any(None, Positive(int)),
                Required('integrand', default=None): Any(None, Positive(int)),
                Required('integration_variable', default=None): Any(None, Positive(int)),
            },
            Required('integrator_options', default={'full_output': 1}): {
                Required('full_output', default=1): 1,
                Extra: object
            },
            Required('complex_integrand', default=False): bool,
            Required('samples', default=1): Positive(int),  # default changed to 1
        })

    debug_appendix_eval_template = (
        "\n"
        "==============================================\n"
        "Integration Data for Sample Number {sample_num} of {samples_total}\n"
        "==============================================\n"
        "Variables: {variables}\n"
        "\n"
        "========== Student Integration Data, Real Part\n"
        "Numerical Value: {student_re_eval}\n"
        "Error Estimate: {student_re_error}\n"
        "Number of integrand evaluations: {student_re_neval}\n"
        "========== Student Integration Data, Imaginary Part\n"
        "Numerical Value: {student_im_eval}\n"
        "Error Estimate: {student_im_error}\n"
        "Number of integrand evaluations: {student_im_neval}\n"
        "\n"
        "========== Author Integration Data, Real Part\n"
        "Numerical Value: {author_re_eval}\n"
        "Error Estimate: {author_re_error}\n"
        "Number of integrand evaluations: {author_re_neval}\n"
        "========== Author Integration Data, Imaginary Part\n"
        "Numerical Value: {author_im_eval}\n"
        "Error Estimate: {author_im_error}\n"
        "Number of integrand evaluations: {author_im_neval}\n"
        ""
    )

    def gen_evaluations(self, answer, student_input, var_samples, func_samples, **kwargs):
        """
        Evaluate the comparer parameters and student inputs for the given samples.

        Returns:
            A tuple (list, list, set). The first two lists are instructor_evals
            and student_evals. These have length equal to number of samples specified
            in config. The set is a record of mathematical functions used in the
            student's input.
        """
        # Similar to FormulaGrader, but specialized to IntegralGrader
        funclist = self.functions.copy()
        varlist = {}

        instructor_evals = []
        student_evals = []

        # Create a list of instructor variables to remove from student evaluation
        var_blacklist = []
        for var in self.config['instructor_vars']:
            if var in var_samples[0]:
                var_blacklist.append(var)

        for i in range(self.config['samples']):
            # Update the functions and variables listings with this sample
            funclist.update(func_samples[i])
            varlist.update(var_samples[i])

            # Evaluate integrals. Error handling here is in two parts because
            # 1. custom error messages we've added
            # 2. scipy's warnings re-raised as error messages
            try:
                expected_re, expected_im, _ = self.evaluate_int(
                    answer['integrand'],
                    answer['lower'],
                    answer['upper'],
                    answer['integration_variable'],
                    varscope=varlist,
                    funcscope=funclist
                )
            except IntegrationError as error:
                msg = "Integration Error with author's stored answer: {}"
                raise ConfigError(msg.format(str(error)))

            # Before performing student evaluation, scrub the instructor
            # variables so that students can't use them
            for key in var_blacklist:
                del varlist[key]

            student_re, student_im, used_funcs = self.evaluate_int(
                student_input['integrand'],
                student_input['lower'],
                student_input['upper'],
                student_input['integration_variable'],
                varscope=varlist,
                funcscope=funclist
                )

            # scipy raises integration warnings when things go wrong,
            # except they aren't really warnings, they're just printed to stdout
            # so we use quad's full_output option to catch the messages, and then raise errors.
            # The 4th component only exists when its warning message is non-empty
            if len(student_re) == 4:
                raise IntegrationError(student_re[3])
            if len(expected_re) == 4:
                raise ConfigError(expected_re[3])
            if len(student_im) == 4:
                raise IntegrationError(student_im[3])
            if len(expected_im) == 4:
                raise ConfigError(expected_im[3])

            # Save results
            expected = expected_re[0] + (expected_im[0] or 0)*1j
            student = student_re[0] + (student_im[0] or 0)*1j
            instructor_evals.append(expected)
            student_evals.append(student)

            # Put the instructor variables back in for the debug output
            varlist.update(var_samples[i])
            self.log_eval_info(i, varlist, funclist,
                               student_re_eval=student_re[0],
                               student_re_error=student_re[1],
                               student_re_neval=student_re[2]['neval'],
                               student_im_eval=student_im[0],
                               student_im_error=student_im[1],
                               student_im_neval=student_im[2]['neval'],
                               author_re_eval=expected_re[0],
                               author_re_error=expected_re[1],
                               author_re_neval=expected_re[2]['neval'],
                               author_im_eval=expected_im[0],
                               author_im_error=expected_im[1],
                               author_im_neval=expected_im[2]['neval'])

        return instructor_evals, student_evals, used_funcs

    def evaluate_int(self, integrand_str, lower_str, upper_str, integration_var,
                     varscope=None, funcscope=None):
        varscope = {} if varscope is None else varscope
        funcscope = {} if funcscope is None else funcscope

        # It is possible that the integration variable might appear in the limits.
        # Some consider this bad practice, but many students do it and Mathematica allows it.
        # We're going to edit the varscope below to contain the integration variable.
        # Let's store the integration variable's initial value in case it has one.
        int_var_initial = varscope[integration_var] if integration_var in varscope else None

        lower, upper, used_funcs = self.get_limits_and_funcs(integrand_str, lower_str, upper_str, varscope, funcscope)

        if isinstance(lower, complex) or isinstance(upper, complex):
            raise IntegrationError('Integration limits must be real but have evaluated '
                                   'to complex numbers.')

        def raw_integrand(x):
            varscope[integration_var] = x
            value, _ = evaluator(integrand_str,
                                 variables=varscope,
                                 functions=funcscope,
                                 suffixes=self.suffixes)
            return value

        # lazy load this module for performance reasons
        from scipy import integrate

        if self.config['complex_integrand']:
            integrand_re = lambda x: real(raw_integrand(x))
            integrand_im = lambda x: imag(raw_integrand(x))
            result_re = integrate.quad(integrand_re, lower, upper, **self.config['integrator_options'])
            result_im = integrate.quad(integrand_im, lower, upper, **self.config['integrator_options'])
        else:
            errmsg = "Integrand has evaluated to complex number but must evaluate to a real."
            integrand = check_output_is_real(raw_integrand, IntegrationError, errmsg)
            result_re = integrate.quad(integrand, lower, upper, **self.config['integrator_options'])
            result_im = (None, None, {'neval': None})

        # Restore the integration variable's initial value now that we are done integrating
        if int_var_initial is not None:
            varscope[integration_var] = int_var_initial

        return result_re, result_im, used_funcs

class SumGrader(SummationGraderBase):
    """
    Grades a student-entered summation by comparing numerically with
    an author-specified summation.

    WARNINGS
    ========
    This grader performs numerical evaluation of the two sums for comparison.
    This works fine for finite sums, but fails for infinite sums. When asked to
    do an infinite sum, it treats infinity as "some large number". It is up to
    the author to ensure that the sums will converge sufficiently by this
    large number (typically by ensuring that variables are sampled from a
    sufficiently small domain). Because infinite sums can always be rewritten
    by combining terms into different counting units, some tolerance must be
    allowed for infinite sums, as it will be common for different numbers of
    effective terms to be summed. Also beware of sums that may sum exactly to
    zero; these may have significant numerical roundoff accumulation.
    
    When sums are performed over large numbers of terms, it's very easy for
    numerical error to creep in. Make sure that your tolerance is sufficiently
    large to satisfy such situations. When in doubt, use debug mode to view
    what the sums are actually evaluating to.
    
    Configuration Options
    =====================
        answers (dict, required): Specifies author's answer. Has required keys lower,
            upper, summand, summation_variable, which each take string values.

        input_positions (dict): Specifies which summation parameters the student
            is required to enter. The default value of input_positions is:

                input_positions = {
                    'lower': 1,
                    'upper': 2,
                    'summand': 3,
                    'summation_variable': 4
                }

            and requires students to enter all four parameters in the indicated
            order.

            If the author overrides the default input_positions value, any subset
            of the keys ('lower', 'upper', 'summand', 'summation_variable')
            may be specified. Key values should be

                - continuous integers starting at 1, or
                - (default) None, indicating that the parameter is not entered by student

            For example,

                input_positions = {
                    'lower': 1,
                    'upper': 2,
                    'summand': 3
                }

            indicates that the problem has 3 input boxes which represent the
            lower limit, upper limit, and summand in that order. The
            summation_variable is NOT entered by student and is instead the
            value specified by author in 'answers'.

        infty_val (int): Specifies a large number to be used in place of infinity in limits (default 1e3).
                         Large values may cause timeouts.

        infty_val_fact (int): Specifies a number to be used in place of infinity in limits when factorials
                              are involved (default 80). Note that (2*80)! ~ 10^284, which should be enough
                              for most purposes!

        even_odd (int): Choose to sum every number (0), every odd number (1) or every even number (2).

    Additional Configuration Options
    ================================
    The configuration keys below are the same as used by FormulaGrader and
    have the same defaults, except where specified
        user_constants: same as FormulaGrader, but with additional default 'infty'
        whitelist
        blacklist
        tolerance (default changed to 1e-12)
        samples (default changed to 2)
        variables
        sample_from
        failable_evals
        numbered_vars
        instructor_vars
        forbidden_strings
        forbidden_message
        required_functions
        metric_suffixes
    """

    @property
    def wording(self):
        return {
            'noun': 'sum',
            'adjective': 'summation'
        }

    @property
    def schema_config(self):
        """Define the configuration options for SumGrader"""
        # Construct the default AbstractGrader schema
        schema = super(SumGrader, self).schema_config
        # Apply the default math schema
        schema = schema.extend(self.math_config_options)
        # Append SumGrader-specific options
        default_input_positions = {
            'lower': 1,
            'upper': 2,
            'summand': 3,
            'summation_variable': 4
        }
        return schema.extend({
            Required('answers'): {
                Required('lower'): str,
                Required('upper'): str,
                Required('summand'): str,
                Required('summation_variable'): str
            },
            Required('input_positions', default=default_input_positions): {
                Required('lower', default=None): Any(None, Positive(int)),
                Required('upper', default=None): Any(None, Positive(int)),
                Required('summand', default=None): Any(None, Positive(int)),
                Required('summation_variable', default=None): Any(None, Positive(int)),
            },
            Required('infty_val', default=1e3): Positive(Number),
            Required('infty_val_fact', default=80): Positive(Number),
            Required('even_odd', default=0): Any(0, 1, 2),
            Required('samples', default=2): Positive(int),  # default changed to 2
            Required('tolerance', default=1e-12): Any(PercentageString, NonNegative(Number)),  # default changed to 1e-12
        })

    debug_appendix_eval_template = (
        "\n"
        "==============================================\n"
        "Summation Data for Sample Number {sample_num} of {samples_total}\n"
        "==============================================\n"
        "Variables: {variables}\n"
        "\n"
        "Student Value: {student_eval}\n"
        "Instructor Value: {instructor_eval}\n"
        ""
    )

    def gen_evaluations(self, answer, student_input, var_samples, func_samples, **kwargs):
        """
        Evaluate the comparer parameters and student inputs for the given samples.

        Returns:
            A tuple (list, list, set). The first two lists are instructor_evals
            and student_evals. These have length equal to number of samples specified
            in config. The set is a record of mathematical functions used in the
            student's input.
        """
        # Similar to FormulaGrader, but specialized to SumGrader
        funclist = self.functions.copy()
        varlist = {}

        instructor_evals = []
        student_evals = []

        # Create a list of instructor variables to remove from student evaluation
        var_blacklist = []
        for var in self.config['instructor_vars']:
            if var in var_samples[0]:
                var_blacklist.append(var)

        for i in range(self.config['samples']):
            # Update the functions and variables listings with this sample
            funclist.update(func_samples[i])
            varlist.update(var_samples[i])

            # Evaluate sums. Error handling here is to catch author errors.
            try:
                expected_eval, _ = self.evaluate_sum(
                    answer['summand'],
                    answer['lower'],
                    answer['upper'],
                    answer['summation_variable'],
                    varscope=varlist,
                    funcscope=funclist
                )
            except MITxError as error:
                msg = "Summation Error with author's stored answer: {}"
                raise ConfigError(msg.format(str(error)))

            # Before performing student evaluation, scrub the instructor
            # variables so that students can't use them
            for key in var_blacklist:
                del varlist[key]
                
            # Evaluate sums.
            student_eval, used_funcs = self.evaluate_sum(
                student_input['summand'],
                student_input['lower'],
                student_input['upper'],
                student_input['summation_variable'],
                varscope=varlist,
                funcscope=funclist
            )

            # Save results
            instructor_evals.append(expected_eval)
            student_evals.append(student_eval)

            # Put the instructor variables back in for the debug output
            varlist.update(var_samples[i])
            self.log_eval_info(i, varlist, funclist,
                               student_eval=student_eval,
                               instructor_eval=expected_eval)

        return instructor_evals, student_evals, used_funcs

    def evaluate_sum(self, summand_str, lower_str, upper_str, summation_var,
                     varscope=None, funcscope=None):
        varscope = {} if varscope is None else varscope
        funcscope = {} if funcscope is None else funcscope

        # Unlike integration, we do not allow the summation variable to appear in
        # the limits of the sum. Make sure the summation variable is not defined
        # in the varscope. Note that this means that i and j cannot be used as
        # summation variables.
        if summation_var in varscope:
            msg = 'Summation variable {} conflicts with another previously-defined variable.'
            raise SummationError(msg.format(summation_var))

        # Evaluate the limits, and find the functions that will be used.
        lower, upper, used_funcs = self.get_limits_and_funcs(summand_str, lower_str, upper_str, varscope, funcscope)

        # Check to ensure that sum limits are not complex.
        if isinstance(lower, complex) or isinstance(upper, complex):
            raise SummationError('Summation limits must be real but have evaluated '
                                 'to complex numbers.')

        # Check to ensure that sum limits are integers or infinite
        if abs(lower) != float('inf') and int(lower) != lower:
            raise SummationError('Lower summation limit does not evaluate to an integer.')
        if abs(upper) != float('inf') and int(upper) != upper:
            raise SummationError('Upper summation limit does not evaluate to an integer.')

        def eval_summand(x):
            """
            Helper function to evaluate the summand at the given value of the
            summation variable.
            """
            varscope[summation_var] = x
            value, _ = evaluator(summand_str,
                                 variables=varscope,
                                 functions=funcscope,
                                 suffixes=self.suffixes)
            del varscope[summation_var]
            return value

        # Check if used_funcs includes a factorial function
        if 'fact' in used_funcs or 'factorial' in used_funcs:
            infty_val = self.config['infty_val_fact']
        else:
            infty_val = self.config['infty_val']

        # Compute the sum
        result = self.perform_summation(eval_summand, lower, upper, self.config['even_odd'], infty_val)
        
        # Return results
        return result, used_funcs

    @staticmethod
    def perform_summation(eval_summand, lower, upper, even_odd, infty_val=1e3):
        """
        Compute the value of a summation. Note that unlike integration, exchanging lower and upper doesn't
        change the value of a summation.
        
        Arguments:
            eval_summand (function): Function of a single argument (summation
                                     variable) to evaluate summand
            lower (int or +-infty): Lower limit on summation
            upper (int or +-infty): Upper limit on summation
            even_odd (int): Sum over all integers in the range (0), all odd integers in
                            the range (1) or all even integers in the range (2)
            infty_val (int): Value to use for infinity in limits (default 1e4)
            
        Returns:
            The result of the sum, in whatever format the eval_summand is provided. Note
            that this may be an integer, float, complex, vector, matrix, or tensor.
        """
        # Sort the limits
        if lower > upper:
            lower, upper = upper, lower
            
        # Handle infinities
        if lower == -float('inf'):
            lower = -infty_val
        if upper == float('inf'):
            upper = infty_val
        if upper == -float('inf'):
            # Only occurs if both upper and lower are both -inf
            raise SummationError('Cannot sum from -infty to -infty.')
        if lower == float('inf'):
            # Only occurs if both upper and lower are both inf
            raise SummationError('Cannot sum from infty to infty.')
            
        # Handle even/odd numbers only
        if even_odd == 1:
            # Odd numbers only
            delta = 2
            if abs(lower % 2) != 1:
                lower += 1
        elif even_odd == 2:
            # Even numbers only
            delta = 2
            if abs(lower % 2) != 0:
                lower += 1
        else:
            delta = 1

        # Because the summand can be a vector/matrix/tensor and can also contain
        # user-defined functions, we can't just use numpy vector math here. Have
        # to for-loop it the old-fashioned way, and hope it's not too slow...
        # Note that we need to convert floats to integers for range.
        evals = [eval_summand(n) for n in range(int(lower), int(upper + 1), delta)]
        result = sum(evals)

        return result
