"""
formulagrader.py
"""
from __future__ import print_function, division, absolute_import, unicode_literals

from numbers import Number
import numpy as np
import six
from voluptuous import Schema, Required, Any, All, Invalid, Length
from mitxgraders.comparers import equality_comparer
from mitxgraders.sampling import schema_user_functions_no_random
from mitxgraders.exceptions import MissingInput
from mitxgraders.baseclasses import ItemGrader
from mitxgraders.helpers.calc import evaluator, DEFAULT_VARIABLES
from mitxgraders.helpers.validatorfuncs import NonNegative, PercentageString, is_callable_with_args, text_string
from mitxgraders.helpers.math_helpers import MathMixin
from mitxgraders.helpers.calc.mathfuncs import merge_dicts

class FormulaGrader(ItemGrader, MathMixin):
    """
    Grades mathematical expressions, like edX FormulaResponse. Note that comparison will
    always be performed in a case-sensitive nature, unlike edX, which allows for a
    case-insensitive comparison.

    Configuration options:
        user_functions (dict): A dictionary of user-defined functions that students can
            use in their solutions (default {}). Eg: {'f': lambda x:x**2}. Can also point
            a function name to a list of functions, from which one will be chosen randomly,
            or a FunctionSamplingSet, eg, RandomFunction().

        user_constants (dict): A dictionary of user-defined constants that students can
            use in their solutions (default {}). Eg: {'c': 3e10}

        blacklist ([str]): A list of functions that students may not use in their solutions
            (default []). Eg: ['cos', 'sin']

        whitelist ([str or None]): A list of the only functions that students may use in
            their solutions (default []). Eg: ['cos', 'sin']. To disallow all functions,
            use [None].

        forbidden_strings ([str]): A list of strings that are forbidden from student
            solutions (default []). Do not put spaces in these strings. This will match
            against student input with spaces stripped. For example, if you want to ask
            for the expansion of sin(2*theta) and expect 2*sin(theta)*cos(theta), you may
            set this to:
            ['*theta', 'theta*', 'theta/', '+theta', 'theta+', '-theta', 'theta-']
            so that students can't just enter 'sin(2*theta)'. Students receive the error
            message in forbidden_message if they attempt to use these strings in their
            solution.

        forbidden_message (str): Error message displayed to students when they use forbidden
            input (default "Invalid Input: This particular answer is forbidden")

        required_functions ([str]): A list of functions that must be used by the students
            in their solutions (default []). Eg: ['sin', 'cos']

        tolerance (number or PercentageString): Tolerance with which answers are compared to
            the solutions. Can be expressed as an absolute number (eg, 0.1), or as a string
            percentage (default '0.01%'). Must be positive or zero.

        metric_suffixes (bool): Should metric affixes be available to students to modify
            answers (default False). If true, then "2m" == 0.002, for example.

        samples (int): The number of times to sample random variables (default 5)

        variables ([str]): A list of variable names (default [])

        numbered_vars ([str]): A list of numbered variable names, which can only occur
            with a number attached to the end. For example, ['numvar'] will allow students
            to write `numvar_{0}`, `numvar_{5}` or `numvar_{-2}`. Any integer will be
            accepted. Use a sample_from entry for `numvar`. Note that a specifically-named
            variable will take priority over a numbered variable. (default [])

        sample_from (dict): A dictionary of VariableSamplingSets for specific variables. By
            default, each variable samples from RealInterval([1, 5]) (default {}). Will
            also accept a list with two values [a, b] to sample from the real interval
            between a and b. Will also accept a tuple of discrete values to sample from.

        failable_evals (int): The number of samples that may disagree before the student's
            answer is marked incorrect (default 0). Ignored by correlated comparers.

        answers: A single "expect" value, a dictionary, or a tuple thereof, as
            described in the documentation for ItemGraders.

            The expect value can be a string, or can itself be a dictionary.

            If the expect value is a string, it represents the correct
            answer and is compared to student input for equality.

            If the expect value is a dictionary, it needs keys:
                - comparer_params: a list of strings to be numerically sampled and passed to the
                    comparer function.
                - comparer: a function with signature comparer(comparer_params_eval, student_eval,
                    utils) that compares student and comparer_params after evaluation. This function
                    should return True, False, 'partial', or a dictionary with required key
                    'grade_decimal' and optional key 'msg'. Comparer messages are ignored
                    when comparison succeeds (result['ok'] is True).

        instructor_vars ([str]): A list of variable/constant names that cannot be used by
            students. This can be useful in constructing DependentSampler expressions or
            blacklisting constants. Note that this list is not validated against the list
            of constants/variables.
    """

    # Comparer functionality
    # Default comparer for FormulaGrader
    default_comparer = staticmethod(equality_comparer)

    @classmethod
    def set_default_comparer(cls, comparer):
        """
        Used to set the default comparer of FormulaGrader class.

        Note: This class method exists primarily to ensure that
        FormulaGrader.default_comparer is a static method. If the staticmethod
        decorator is not used,

            FormulaGrader.default_grader = equality_comparer
            grader = FormulaGrader()

        then grader.default_grader will be a bound method. That's bad, since
        comparer functions do not expect self as the first argument.
        """
        cls.default_comparer = staticmethod(comparer)

    @classmethod
    def reset_default_comparer(cls):
        """
        Resets the default_comparer to equality_comparer.
        """
        cls.set_default_comparer(equality_comparer)

    @staticmethod
    def eval_and_validate_comparer_params(scoped_eval, comparer_params, siblings_eval):
        """
        Evaluate the comparer_params, and make sure they contain no references
        to empty siblings.

        Arguments
        =========
        - scoped_eval (func): a unary function to evaluate math expressions.
            Same keyword arguments as calc's evaluator, but with appropriate
            default variables, functions, suffixes
        - comparer_params ([str]): unevaluated expressions
        - siblings_eval (dict): evaluated expressions
        """

        results = [scoped_eval(param, max_array_dim=float('inf'))
                   for param in comparer_params]
        # results is a list of (value, EvalMetaData) pairs
        comparer_params_eval = [value for value, _ in results]
        used_variables = set().union(*[used.variables_used for _, used in results])

        for variable in used_variables:
            if variable in siblings_eval and np.isnan(siblings_eval[variable]):
                raise MissingInput('Cannot grade answer, a required input is missing.')

        return comparer_params_eval

    # Configuration

    @property
    def schema_config(self):
        """Define the configuration options for FormulaGrader"""
        # Construct the default ItemGrader schema
        schema = super(FormulaGrader, self).schema_config
        # Apply the default math schema
        schema = schema.extend(self.math_config_options)
        # Append FormulaGrader-specific options
        return schema.extend({
            Required('allow_inf', default=False): bool,
            Required('max_array_dim', default=0): NonNegative(int)  # Do not use this; use MatrixGrader instead
        })

    schema_expect = Schema({
        Required('comparer_params'): [text_string],
        # Functions seem not to be usable as default values, so the default comparer is added later.
        # https://github.com/alecthomas/voluptuous/issues/340
        Required('comparer'): is_callable_with_args(3)
    })

    def validate_expect(self, expect):
        """
        Validate the answers's expect key.

        >>> result = FormulaGrader().validate_expect('mc^2')
        >>> expected = {
        ... 'comparer_params': ['mc^2'],
        ... 'comparer': equality_comparer
        ... }
        >>> result == expected
        True
        """
        if isinstance(expect, six.string_types):
            return self.schema_expect({
                'comparer': self.default_comparer,
                'comparer_params': [expect]
                })

        try:
            return self.schema_expect(expect)
        except Invalid:
            # Only raise the detailed error message if author is trying to use comparer.
            if isinstance(expect, dict) and 'comparer' in expect:
                raise
            # Otherwise, be generic.
            else:
                raise Invalid("Something's wrong with grader's 'answers' configuration key. "
                              "Please see documentation for accepted formats.")

    debug_appendix_eval_template = (
        "\n"
        "==========================================\n"
        "Evaluation Data for Sample Number {sample_num} of {samples_total}\n"
        "==========================================\n"
        "Variables:\n"
        "{variables}\n"
        "Student Eval: {student_eval}\n"
        "Compare to:  {comparer_params_eval}\n"
        ""
    )

    def __init__(self, config=None, **kwargs):
        """
        Validate the FormulaGrader's configuration.
        First, we allow the ItemGrader initializer to construct the function list.
        We then construct the lists of functions, suffixes and constants.
        Finally, we refine the sample_from entry.
        """
        super(FormulaGrader, self).__init__(config, **kwargs)

        # If we are allowing infinities, add this to the default constants.
        # Note that this is done before variable validation.
        if self.config['allow_inf']:
            # Make a new copy, so we don't change this for all FormulaGraders
            self.default_variables = merge_dicts(DEFAULT_VARIABLES, {'infty': float('inf')})

        # Store the comparer utils
        self.comparer_utils = self.get_comparer_utils()

        # Perform standard math validation
        self.validate_math_config()

    def check_response(self, answer, student_input, **kwargs):
        """Check the student response against a given answer"""
        return self.check_math_response(answer, student_input, **kwargs)

    @staticmethod
    def sibling_varname(index):
        """Generate name for sibling variables"""
        return 'sibling_{}'.format(index + 1)

    @staticmethod
    def get_sibling_formulas(siblings, required_siblings):
        """
        Returns a dict containing sibling formula inputs.

        Arguments:
            siblings ([dict]): each sibling dict has keys 'grader' and 'input'
            required_siblings (set): Only include siblings whose varnames are
                included in this set

        Note: siblings are present when a grader is used inside a ListGrader.
        """
        if siblings is None:
            return {}
        formula_siblings = [(i, sibling['input']) for i, sibling
                            in enumerate(siblings)
                            if isinstance(sibling['grader'], FormulaGrader)]
        return {
            FormulaGrader.sibling_varname(i): sibling_input
            for i, sibling_input in formula_siblings
            if FormulaGrader.sibling_varname(i) in required_siblings
        }

    def gen_evaluations(self, comparer_params, student_input, sibling_formulas,
                        var_samples, func_samples):
        """
        Evaluate the comparer parameters and student inputs for the given samples.

        Returns:
            A tuple (list, list, set). The first two lists are comparer_params_evals
            and student_evals. These have length equal to number of samples specified
            in config. The set is a record of mathematical functions used in the
            student's input.
        """
        funclist = self.functions.copy()
        varlist = {}

        comparer_params_evals = []
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

            def scoped_eval(expression,
                            variables=varlist,
                            functions=funclist,
                            suffixes=self.suffixes,
                            max_array_dim=self.config['max_array_dim']):
                return evaluator(expression, variables, functions, suffixes, max_array_dim,
                                 allow_inf=self.config['allow_inf'])

            # Compute the sibling values, and add them to varlist
            siblings_eval = {
                key: scoped_eval(sibling_formulas[key])[0]
                for key in sibling_formulas
            }
            varlist.update(siblings_eval)

            # Compute expressions
            comparer_params_eval = self.eval_and_validate_comparer_params(
                scoped_eval, comparer_params, siblings_eval)
            comparer_params_evals.append(comparer_params_eval)

            # Before performing student evaluation, scrub the sibling and instructor
            # variables so that students can't use them
            for key in siblings_eval:
                del varlist[key]
            for key in var_blacklist:
                del varlist[key]

            student_eval, meta = scoped_eval(student_input)
            student_evals.append(student_eval)

            # TODO: Remove this if statement
            if self.config['debug']:
                # Put the siblings and instructor variables back in for the debug output
                varlist.update(var_samples[i])
                varlist.update(siblings_eval)
                self.log_eval_info(i, varlist, funclist,
                                   comparer_params_eval=comparer_params_eval,
                                   student_eval=student_eval)

        return comparer_params_evals, student_evals, meta.functions_used

    def raw_check(self, answer, student_input, **kwargs):
        """Perform the numerical check of student_input vs answer"""

        # Extract sibling formulas to allow for sampling
        siblings = kwargs.get('siblings', None)
        comparer_params = answer['expect']['comparer_params']
        required_siblings = self.get_used_vars(comparer_params)
        # required_siblings might include some extra variable names, but no matter
        sibling_formulas = self.get_sibling_formulas(siblings, required_siblings)

        # Generate samples, using student input, sibling formulas and any comparer
        # parameters (including answers) as the list of expressions to check
        var_samples, func_samples = self.gen_var_and_func_samples(student_input,
                                                                  sibling_formulas,
                                                                  comparer_params)

        (comparer_params_evals,
         student_evals,
         functions_used) = self.gen_evaluations(comparer_params, student_input,
                                                sibling_formulas, var_samples, func_samples)

        # Get the comparer function
        comparer = answer['expect']['comparer']
        results = self.compare_evaluations(comparer_params_evals, student_evals,
                                           comparer, self.get_comparer_utils())

        # Comparer function results might assign partial credit.
        # But the answer we're testing against might only merit partial credit.
        for result in results:
            result['grade_decimal'] *= answer['grade_decimal']
        consolidated = self.consolidate_results(results, answer, self.config['failable_evals'])

        return consolidated, functions_used

class NumericalGrader(FormulaGrader):
    """
    Grades mathematical expressions without random functions or variables.

    This is a convenience class built on top of FormulaGrader that sets a number of
    default values to be more amenable to grading numerical input. It is set up to mimic
    NumericalResponse graders in edX.

    Configuration options as per FormulaGrader, except:
        user_functions (dict): A dictionary of user-defined functions that students can
            use in their solutions (default {}). Cannot have random functions, unlike
            FormulaGrader. Eg: {'f': lambda x:x**2}

        tolerance (number or PercentageString): As in FormulaGrader (default '5%')

        samples (int): Will always be 1

        variables ([str]): Will always be an empty list

        numbered_vars ([str]): Will always be an empty list

        sample_from (dict): Will always be an empty dictionary

        failable_evals (int): Will always be 0
    """

    # Default comparer for NumericalGrader (independent of FormulaGrader)
    default_comparer = staticmethod(equality_comparer)

    @property
    def schema_config(self):
        """Define the configuration options for NumericalGrader"""
        # Construct the default FormulaGrader schema
        schema = super(NumericalGrader, self).schema_config
        # Modify the default FormulaGrader options
        return schema.extend({
            Required('user_functions', default={}): schema_user_functions_no_random,
            Required('tolerance', default='5%'): Any(PercentageString, NonNegative(Number)),
            Required('samples', default=1): 1,
            Required('variables', default=[]): All(Length(max=0), []),
            Required('numbered_vars', default=[]): All(Length(max=0), []),
            Required('sample_from', default={}): {},
            Required('failable_evals', default=0): 0
        })
