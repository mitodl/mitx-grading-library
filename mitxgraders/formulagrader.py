"""
formulagrader.py

Contains classes for numerical and formula graders
* NumericalGrader
* FormulaGrader
"""
from __future__ import division
from numbers import Number
from collections import namedtuple
from mitxgraders.sampling import (VariableSamplingSet, FunctionSamplingSet, RealInterval,
                                  DiscreteSet, gen_symbols_samples, construct_functions,
                                  construct_constants, construct_suffixes)
from mitxgraders.baseclasses import ItemGrader, InvalidInput
from mitxgraders.voluptuous import Schema, Required, Any, All, Extra, Invalid
from mitxgraders.helpers.calc import CalcError, evaluator
from mitxgraders.helpers.validatorfuncs import (Positive, NonNegative, is_callable,
                                                PercentageString, is_callable_with_args)
from mitxgraders.helpers.mathfunc import within_tolerance

# Set the objects to be imported from this grader
__all__ = [
    "NumericalGrader",
    "FormulaGrader",
    "CalcError"
]

def casify(thestring, case_sensitive):
    """Converts a string to lowercase if not case_sensitive"""
    return thestring if case_sensitive else thestring.lower()

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

        answers (str | dict): A string, dictionary, or tuple thereof. If a string is supplied,
            it represents the correct answer and is compared to student input for equality.

            If a dictionary is supplied, it needs keys:
                - comparer_params: a list of strings to be numerically sampled and passed to the
                    comparer function.
                - comparer: a function with signature `comparer(comparer_params_evals, student_eval,
                    utils)` that compares student and comparer_params after evaluation.
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
            Required('tolerance', default='0.01%'): Any(PercentageString, NonNegative(Number)),
            Required('case_sensitive', default=True): bool,
            Required('metric_suffixes', default=False): bool,
            Required('samples', default=5): Positive(int),
            Required('variables', default=[]): [str],
            Required('sample_from', default={}): dict,
            Required('failable_evals', default=0): NonNegative(int)
        })

    Utils = namedtuple('Utils', ['tolerance', 'within_tolerance'])

    def get_comparer_utils(self):
        """Get the utils for comparer function."""
        def _within_tolerance(x, y):
            return within_tolerance(x, y, self.config['tolerance'])
        return self.Utils(tolerance=self.config['tolerance'],
                          within_tolerance=_within_tolerance)

    @staticmethod
    def default_comparer(comparer_params, student_input, utils):
        """
        Default comparer function.

        Assumes comparer_params is just the single expected answer wrapped in a list.
        """
        return utils.within_tolerance(comparer_params[0], student_input)

    schema_expect = Schema({
        Required('comparer_params'): [str],
        # Functions seem not to be usable as default values, so the default comparer is added later.
        # https://github.com/alecthomas/voluptuous/issues/340
        Required('comparer'): is_callable_with_args(3)
    })

    @classmethod
    def validate_expect(cls, expect):
        """
        Validate the answers's expect key.

        >>> result = FormulaGrader.validate_expect('mc^2')
        >>> expected = {
        ... 'comparer_params': ['mc^2'],
        ... 'comparer': FormulaGrader.default_comparer
        ... }
        >>> result == expected
        True
        """
        if isinstance(expect, str):
            return cls.schema_expect({
                'comparer': cls.default_comparer,
                'comparer_params': [expect]
                })

        try:
            return cls.schema_expect(expect)
        except Invalid:
            # Only raise the detailed error message if author is trying to use comparer.
            if isinstance(expect, dict) and 'comparer' in expect:
                raise
            # Otherwise, be generic.
            else:
                raise Invalid("Something's wrong with grader's 'answers' configuration key. "
                              "Please see documentation for accepted formats.")

    def __init__(self, config=None, **kwargs):
        """
        Validate the Formulagrader's configuration.
        First, we allow the ItemGrader initializer to construct the function list.
        We then construct the lists of functions, suffixes and constants.
        Finally, we refine the sample_from entry.
        """
        super(FormulaGrader, self).__init__(config, **kwargs)

        # store the comparer utils
        self.comparer_utils = self.get_comparer_utils()

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

        # Now perform the computations
        try:
            result = self.raw_check(answer, student_input)
            if result['ok'] is True or result['ok'] == 'partial':
                self.validate_forbidden_strings_not_used(student_input,
                                                         self.config['forbidden_strings'],
                                                         self.config['forbidden_message'],
                                                         self.config['case_sensitive'])
            return result
        except (CalcError, InvalidInput):
            # These errors have been vetted already
            raise
        except Exception:  # pragma: no cover
            # If debug mode is on, give the full stack trace
            if self.config["debug"]:
                raise
            else:
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

        # Get the comparer function
        comparer = answer['expect']['comparer']

        num_failures = 0
        for i in range(self.config['samples']):
            # Update the functions and variables listings with this sample
            funclist.update(func_samples[i])
            varlist.update(var_samples[i])

            # Compute expressions
            comparer_params_eval = [
                evaluator(formula=param,
                          case_sensitive=self.config['case_sensitive'],
                          variables=varlist,
                          functions=funclist,
                          suffixes=self.suffixes)[0]
                for param in answer['expect']['comparer_params']
                ]

            student_eval, used_funcs = evaluator(student_input,
                                                 case_sensitive=self.config['case_sensitive'],
                                                 variables=varlist,
                                                 functions=funclist,
                                                 suffixes=self.suffixes)

            # Check that the required functions are used
            # But only the first time!
            if i == 0:
                self.validate_required_functions_used(used_funcs,
                                                      self.config['required_functions'],
                                                      self.config['case_sensitive'])

            # Check if expressions agree
            if not comparer(comparer_params_eval, student_eval, self.comparer_utils):
                num_failures += 1
                if num_failures > self.config["failable_evals"]:
                    return {'ok': False, 'grade_decimal': 0, 'msg': ''}

        # This response appears to agree with the expected answer
        return {
            'ok': answer['ok'],
            'grade_decimal': answer['grade_decimal'],
            'msg': answer['msg']
        }

    @staticmethod
    def validate_required_functions_used(used_funcs, required_funcs, case_sensitive):
        """
        Raise InvalidInput error if used_funcs does not contain all required_funcs

        Examples:
        >>> FormulaGrader.validate_required_functions_used(
        ... ['sin', 'cos', 'f', 'g'],
        ... ['cos', 'f'],
        ... True
        ... )
        True
        >>> FormulaGrader.validate_required_functions_used(
        ... ['sin', 'cos', 'F', 'g'],
        ... ['cos', 'f'],
        ... True
        ... )
        Traceback (most recent call last):
        InvalidInput: Invalid Input: Answer must contain the function f

        Case insensitive:
        >>> FormulaGrader.validate_required_functions_used(
        ... ['sin', 'Cos', 'F', 'g'],
        ... ['cos', 'f'],
        ... False
        ... )
        True
        """
        for func in required_funcs:
            func = casify(func, case_sensitive)
            used_funcs = [casify(f, case_sensitive) for f in used_funcs]
            if func not in used_funcs:
                msg = "Invalid Input: Answer must contain the function {}"
                raise InvalidInput(msg.format(func))
        return True

    @staticmethod
    def validate_forbidden_strings_not_used(expr, forbidden_strings, forbidden_msg, case_sensitive):
        """
        Ignoring whitespace, checking that expr does not contain any forbidden_strings.

        Usage
        =====

        Passes validation if no forbidden strings used:
        >>> FormulaGrader.validate_forbidden_strings_not_used(
        ... '2*sin(x)*cos(x)',
        ... ['*x', '+ x', '- x'],
        ... 'A forbidden string was used!',
        ... True
        ... )
        True

        Fails validation if any forbidden string is used:
        >>> FormulaGrader.validate_forbidden_strings_not_used(
        ... 'sin(x+x)',
        ... ['*x', '+ x', '- x'],
        ... 'A forbidden string was used!',
        ... True
        ... )
        Traceback (most recent call last):
        InvalidInput: A forbidden string was used!
        """
        stripped_expr = casify(expr, case_sensitive).replace(' ', '')

        for forbidden in forbidden_strings:
            check_for = casify(forbidden, case_sensitive).replace(' ', '')
            if check_for in stripped_expr:
                # Don't give away the specific string that is being checked for!
                raise InvalidInput(forbidden_msg)
        return True


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
