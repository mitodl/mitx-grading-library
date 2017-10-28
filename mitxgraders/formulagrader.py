"""
formulagrader.py

Contains classes for numerical and formula graders
* NumericalGrader
* FormulaGrader
"""
from __future__ import division
from numbers import Number
from sampling import VariableSamplingSet, FunctionSamplingSet, RealInterval, DiscreteSet
from mitxgraders.baseclasses import ItemGrader, InvalidInput
from mitxgraders.voluptuous import Schema, Required, Any, All, Extra
from mitxgraders.helpers.calc import (UndefinedVariable, UndefinedFunction,
                                  UnmatchedParentheses, evaluator)
from mitxgraders.helpers.validatorfuncs import (Positive, NonNegative, PercentageString, is_callable)
from mitxgraders.helpers.mathfunc import (construct_functions, construct_constants,
                                      construct_suffixes, within_tolerance, gen_symbols_samples)

# Set the objects to be imported from this grader
__all__ = [
    "NumericalGrader",
    "FormulaGrader",
    "UndefinedVariable",
    "UndefinedFunction",
    "UnmatchedParentheses"
]

class FormulaGrader(ItemGrader):
    """
    Grades mathematical expressions, like edX FormulaResponse.

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
            percentage (default '0.1%'). Must be positive or zero.

        case_sensitive (bool): Should comparison of variable and function names be performed
            in a case sensitive manner? (default True)

        metric_suffixes (bool): Should metric affixes be available to students to modify
            answers (default False). If true, then "2m" == 0.002, for example.

        samples (int): The number of times to sample random variables (default 5)

        variables ([str]): A list of variable names (default [])

        sample_from (dict): A dictionary of VariableSamplingSets for specific variables. By
            default, each variable samples from RealInterval([1, 5]) (default {}). Will
            also accept a list with two values [a, b] to sample from the real interval
            between a and b. Will also accept a tuple of discrete values to sample from.

        failable_evals (int): The number of samples that may disagree before the student's
            answer is marked incorrect (default 0)
    """
    @property
    def schema_config(self):
        """Define the configuration options for FormulaGrader"""
        # Construct the default ItemGrader schema
        schema = super(FormulaGrader, self).schema_config
        # Append options
        forbidden_default = "Invalid Input: This particular answer is forbidden"
        return schema.extend({
            Required('user_functions', default={}):
                {Extra: Any(is_callable, [is_callable], FunctionSamplingSet)},
            Required('user_constants', default={}): {Extra: Number},
            Required('blacklist', default=[]): [str],
            Required('whitelist', default=[]): [Any(str, None)],
            Required('forbidden_strings', default=[]): [str],
            Required('forbidden_message', default=forbidden_default): str,
            Required('required_functions', default=[]): [str],
            Required('tolerance', default='0.1%'): Any(PercentageString, NonNegative(Number)),
            Required('case_sensitive', default=True): bool,
            Required('metric_suffixes', default=False): bool,
            Required('samples', default=5): Positive(int),
            Required('variables', default=[]): [str],
            Required('sample_from', default={}): dict,
            Required('failable_evals', default=0): NonNegative(int)
        })

    def __init__(self, config=None, **kwargs):
        """
        Validate the Formulagrader's configuration.
        First, we allow the ItemGrader initializer to construct the function list.
        We then construct the lists of functions, suffixes and constants.
        Finally, we refine the sample_from entry.
        """
        super(FormulaGrader, self).__init__(config, **kwargs)

        # Set up the various lists we use
        self.functions, self.random_funcs = construct_functions(self.config["whitelist"],
                                                                self.config["blacklist"],
                                                                self.config["user_functions"])
        self.constants = construct_constants(self.config["user_constants"])
        self.suffixes = construct_suffixes(self.config["metric_suffixes"])

        # Construct the schema for sample_from
        # First, accept all VariableSamplingSets
        # Then, accept any list that RealInterval can interpret
        # Finally, single numbers or tuples of numbers will be handled by DiscreteSet
        schema_sample_from = Schema({
            Required(varname, default=RealInterval()):
                Any(VariableSamplingSet,
                    All(list, lambda pair: RealInterval(pair)),
                    lambda tup: DiscreteSet(tup))
            for varname in self.config['variables']
        })
        self.config['sample_from'] = schema_sample_from(self.config['sample_from'])
        # Note that voluptuous ensures that there are no orphaned entries in sample_from

    def check_response(self, answer, student_input):
        """Check the student response against a given answer"""
        # First, check for forbidden strings
        # Remove whitespace so that students can't trick this check by adding any
        check = student_input if self.config["case_sensitive"] else student_input.lower()
        check = "".join([char for char in check if char != " "])
        for x in self.config["forbidden_strings"]:
            forbid = x if self.config["case_sensitive"] else x.lower()
            if forbid in check:
                # Don't give away the specific string that is being checked for!
                raise InvalidInput(self.config["forbidden_message"])

        # Now perform the computations
        try:
            return self.raw_check(answer, student_input)

        # And now for all of the things that could possibly have gone wrong...
        except UndefinedVariable as e:
            message = "Invalid Input: {varname} not permitted in answer as a variable"
            raise UndefinedVariable(message.format(varname=str(e)))

        except UndefinedFunction as e:
            funcnames = e.args[0]
            valid_var = e.args[1]
            message = "Invalid Input: {varname} not permitted in answer as a function"
            if valid_var:
                message += " (did you forget to use * for multiplication?)"
            raise UndefinedFunction(message.format(varname=funcnames))

        except UnmatchedParentheses:
            # The error message is already written for this error
            raise

        except ValueError as err:
            if 'factorial' in err.message:
                # This is thrown when fact() or factorial() is used
                # that tests on negative and/or non-integer inputs
                # err.message will be: `factorial() only accepts integral values` or
                # `factorial() not defined for negative values`
                raise InvalidInput("Error evaluating factorial() or fact() in input. "
                                   "These functions can only be used on positive integers.")
            elif self.config["debug"]:
                # Check if debug mode is on
                raise
            else:
                # Otherwise, give a generic error message
                msg = "Invalid Input: Could not parse '{}' as a formula"
                raise InvalidInput(msg.format(student_input))

        except Exception as err:
            # Reraise InvalidInput messages
            if isinstance(err, InvalidInput):
                raise
            # Check if debug mode is on
            if self.config["debug"]:
                raise
            # Otherwise, give a generic error message
            msg = "Invalid Input: Could not parse '{}' as a formula"
            raise InvalidInput(msg.format(student_input))

    def raw_check(self, answer, student_input):
        """Perform the numerical check of student_input vs answer"""
        var_samples = gen_symbols_samples(self.config['variables'],
                                          self.config['samples'],
                                          self.config['sample_from'])

        func_samples = gen_symbols_samples(self.random_funcs.keys(),
                                           self.config['samples'],
                                           self.random_funcs)

        # Make a copy of the functions and variables lists
        # We'll add the sampled functions/variables in
        funclist = self.functions.copy()
        varlist = self.constants.copy()

        num_failures = 0
        for i in range(self.config['samples']):
            # Update the functions and variables listings with this sample
            funclist.update(func_samples[i])
            varlist.update(var_samples[i])

            # Compute expressions
            expected, _ = evaluator(formula=answer['expect'],
                                    case_sensitive=self.config['case_sensitive'],
                                    variables=varlist,
                                    functions=funclist,
                                    suffixes=self.suffixes)

            student, used_funcs = evaluator(student_input,
                                            case_sensitive=self.config['case_sensitive'],
                                            variables=varlist,
                                            functions=funclist,
                                            suffixes=self.suffixes)

            # Check that the required functions are used
            # But only the first time!
            if i == 0:
                for f in self.config["required_functions"]:
                    ftest = f
                    if not self.config['case_sensitive']:
                        ftest = f.lower()
                        used_funcs = [x.lower() for x in used_funcs]
                    if ftest not in used_funcs:
                        msg = "Invalid Input: Answer must contain the function {}"
                        raise InvalidInput(msg.format(f))

            # Check if expressions agree
            if not within_tolerance(expected, student, self.config['tolerance']):
                num_failures += 1
                if num_failures > self.config["failable_evals"]:
                    return {'ok': False, 'grade_decimal': 0, 'msg': ''}

        # This response appears to agree with the expected answer
        return {
            'ok': answer['ok'],
            'grade_decimal': answer['grade_decimal'],
            'msg': answer['msg']
        }


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

        sample_from (dict): Will always be an empty dictionary

        failable_evals (int): Will always be 0
    """

    @property
    def schema_config(self):
        """Define the configuration options for NumericalGrader"""
        # Construct the default FormulaGrader schema
        schema = super(NumericalGrader, self).schema_config
        # Modify the default FormulaGrader options
        return schema.extend({
            Required('user_functions', default={}): {Extra: is_callable},
            Required('tolerance', default='5%'): Any(PercentageString, NonNegative(Number)),
            Required('samples', default=1): 1,
            Required('variables', default=[]): [],
            Required('sample_from', default={}): {},
            Required('failable_evals', default=0): 0
        })
