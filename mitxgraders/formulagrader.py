"""
formulagrader.py

Contains classes for numerical and formula graders
* NumericalGrader
* FormulaGrader
"""
from __future__ import division
from numbers import Number
from collections import namedtuple
from pprint import PrettyPrinter
import re
import itertools
from voluptuous import Schema, Required, Any, All, Extra, Invalid, Length
from mitxgraders.sampling import (VariableSamplingSet, FunctionSamplingSet, RealInterval,
                                  DiscreteSet, gen_symbols_samples, construct_functions,
                                  construct_constants, construct_suffixes)
from mitxgraders.baseclasses import ItemGrader, InvalidInput, ConfigError, StudentFacingError
from mitxgraders.helpers.calc import CalcError, evaluator, parsercache
from mitxgraders.helpers.validatorfuncs import (Positive, NonNegative, is_callable,
                                                PercentageString, is_callable_with_args, all_unique)
from mitxgraders.helpers.mathfunc import within_tolerance, DEFAULT_FUNCTIONS, DEFAULT_VARIABLES

# Set the objects to be imported from this grader
__all__ = [
    "NumericalGrader",
    "FormulaGrader",
    "CalcError"
]

# Some of these validators are useful to other classes, e.g., IntegralGrader
def validate_blacklist_whitelist_config(blacklist, whitelist):
    """Validates the whitelist/blacklist configuration.

    Voluptuous should already have type-checked blacklist and whitelist. Now check:
    1. They are not both used
    2. All whitelist/blacklist functions actually exist
    """
    if blacklist and whitelist:
        raise ConfigError("Cannot whitelist and blacklist at the same time")
    for func in blacklist:
        # no need to check user_functions too ... if you don't want student to
        # use one of the user_functions, just don't add it in the first place.
        if func not in DEFAULT_FUNCTIONS:
            raise ConfigError("Unknown function in blacklist: {func}".format(func=func))

    if whitelist == [None]:
        return

    for func in whitelist:
        if func not in DEFAULT_FUNCTIONS:
            raise ConfigError("Unknown function in whitelist: {func}".format(func=func))

def validate_forbidden_strings_not_used(expr, forbidden_strings, forbidden_msg):
    """
    Ignoring whitespace, checking that expr does not contain any forbidden_strings.
    Usage
    =====
    Passes validation if no forbidden strings used:
    >>> validate_forbidden_strings_not_used(
    ... '2*sin(x)*cos(x)',
    ... ['*x', '+ x', '- x'],
    ... 'A forbidden string was used!'
    ... )
    True

    Fails validation if any forbidden string is used:
    >>> validate_forbidden_strings_not_used(
    ... 'sin(x+x)',
    ... ['*x', '+ x', '- x'],
    ... 'A forbidden string was used!'
    ... )
    Traceback (most recent call last):
    InvalidInput: A forbidden string was used!
    """
    stripped_expr = expr.replace(' ', '')
    for forbidden in forbidden_strings:
        check_for = forbidden.replace(' ', '')
        if check_for in stripped_expr:
            # Don't give away the specific string that is being checked for!
            raise InvalidInput(forbidden_msg)
    return True

def validate_only_permitted_functions_used(used_funcs, permitted_functions):
    """
    Check that the used_funcs contains only permitted_functions
    Arguments:
        used_functions ({str}): set of used function names
        permitted_functions ({str}): set of permitted function names
    Usage
    =====
    >>> validate_only_permitted_functions_used(
    ... set(['f', 'sin']),
    ... set(['f', 'g', 'sin', 'cos'])
    ... )
    True
    >>> validate_only_permitted_functions_used(
    ... set(['f', 'Sin', 'h']),
    ... set(['f', 'g', 'sin', 'cos'])
    ... )
    Traceback (most recent call last):
    InvalidInput: Invalid Input: function(s) 'h', 'Sin' not permitted in answer
    """
    used_not_permitted = [f for f in used_funcs if f not in permitted_functions]
    if used_not_permitted:
        func_names = ", ".join(["'{f}'".format(f=f) for f in used_not_permitted])
        message = "Invalid Input: function(s) {} not permitted in answer".format(func_names)
        raise InvalidInput(message)
    return True

def get_permitted_functions(whitelist, blacklist, always_allowed):
    """
    Constructs a set of functions whose usage is permitted.
    Arguments:
        whitelist ([str] | [None]): List of allowed function names
            [None] disallows all except always_allowed
            [] uses DEFAULT_FUNCTIONS.keys()
        blacklist ([str]): List of disallowed function names
        always_allowed (dict): dict whose keys are always-allowed as function names
    Usage
    =====
    Whitelist some functions:
    >>> always_allowed = {'f1': None, 'f2': None} # values unimportant
    >>> get_permitted_functions(['sin', 'cos'], [], always_allowed) == set([
    ... 'sin', 'cos', 'f1', 'f2'
    ... ])
    True

    [None] disallows all defaults:
    >>> always_allowed = {'f1': None, 'f2': None} # values unimportant
    >>> get_permitted_functions([None], [], always_allowed) == set([
    ... 'f1', 'f2'
    ... ])
    True

    Blacklist some functions:
    >>> get_permitted_functions([], ['sin', 'cos'], always_allowed) == set(
    ... DEFAULT_FUNCTIONS).union(['f1', 'f2']).difference(set(['sin', 'cos']))
    True

    Blacklist and whitelist cannot be simultaneously used:
    >>> get_permitted_functions(['sin'], ['cos'], always_allowed)
    Traceback (most recent call last):
    ValueError: whitelist and blacklist cannot be simultaneously truthy
    """
    # should never trigger except in doctest above,
    # Grader's config validation should raise an error first
    if whitelist and blacklist:
        raise ValueError('whitelist and blacklist cannot be simultaneously truthy')
    if whitelist == []:
        permitted_functions = set(always_allowed).union(
            set(DEFAULT_FUNCTIONS)
            ).difference(set(blacklist))
    elif whitelist == [None]:
        permitted_functions = set(always_allowed)
    else:
        permitted_functions = set(always_allowed).union(whitelist)
    return permitted_functions

def validate_required_functions_used(used_funcs, required_funcs):
    """
    Raise InvalidInput error if used_funcs does not contain all required_funcs

    Examples:
    >>> validate_required_functions_used(
    ... ['sin', 'cos', 'f', 'g'],
    ... ['cos', 'f']
    ... )
    True
    >>> validate_required_functions_used(
    ... ['sin', 'cos', 'F', 'g'],
    ... ['cos', 'f']
    ... )
    Traceback (most recent call last):
    InvalidInput: Invalid Input: Answer must contain the function f
    """
    for func in required_funcs:
        if func not in used_funcs:
            msg = "Invalid Input: Answer must contain the function {}"
            raise InvalidInput(msg.format(func))
    return True

def numbered_vars_regexp(numbered_vars):
    """
    Creates a regexp to match numbered variables. Catches the full string and the head.

    Arguments:
        numbered_vars ([str]): a list of variable heads

    Usage
    =====

    Matches numbered variables:
    >>> regexp = numbered_vars_regexp(['b', 'c', 'Cat'])
    >>> regexp.match('b_{12}').groups()
    ('b_{12}', 'b')
    >>> regexp.match('b_{-3}').groups()
    ('b_{-3}', 'b')
    >>> regexp.match('b_{0}').groups()
    ('b_{0}', 'b')

    Other variables match, too, in case-sensitive fashion:
    >>> regexp.match('Cat_{17}').groups()
    ('Cat_{17}', 'Cat')

    Stuff that shouldn't match does not match:
    >>> regexp.match('b') == None
    True
    >>> regexp.match('b_{05}') == None
    True
    >>> regexp.match('b_{-05}') == None
    True
    >>> regexp.match('B_{0}') == None
    True
    """
    head_list = '|'.join(map(re.escape, numbered_vars))
    regexp = (r"^((" + head_list + ")" # Start and match any head (capture full string, head)
              r"_{" # match _{
              r"(?:[-]?[1-9]\d*|0)" # match number pattern
              r"})$") # match closing }, close group, and end of string
    return re.compile(regexp)

def validate_no_collisions(config, keys):
    """
    Validates no collisions between iterable config fields specified by keys.

    Usage
    =====

    Duplicate entries raise a ConfigError:
    >>> keys = ['variables', 'user_constants', 'numbered_vars']
    >>> validate_no_collisions({
    ...     'variables':['a', 'b', 'c', 'x', 'y'],
    ...     'user_constants':{'x': 5, 'y': 10},
    ...     'numbered_vars':['phi', 'psi']
    ... }, keys)
    Traceback (most recent call last):
    ConfigError: 'user_constants' and 'variables' contain duplicate entries: ['x', 'y']

    >>> validate_no_collisions({
    ...     'variables':['a', 'psi', 'phi', 'X', 'Y'],
    ...     'user_constants':{'x': 5, 'y': 10},
    ...     'numbered_vars':['phi', 'psi']
    ... }, keys)
    Traceback (most recent call last):
    ConfigError: 'numbered_vars' and 'variables' contain duplicate entries: ['phi', 'psi']

    Without duplicates, return True
    >>> validate_no_collisions({
    ...     'variables':['a', 'b', 'c', 'F', 'G'],
    ...     'user_constants':{'x': 5, 'y': 10},
    ...     'numbered_vars':['phi', 'psi']
    ... }, keys)
    True
    """
    dict_of_sets = {k: set(config[k]) for k in keys}
    msg = "'{iter1}' and '{iter2}' contain duplicate entries: {duplicates}"

    for k1, k2 in itertools.combinations(dict_of_sets, r=2):
        k1, k2 = sorted([k1, k2])
        duplicates = dict_of_sets[k1].intersection(dict_of_sets[k2])
        if duplicates:
            sorted_dups = list(sorted(duplicates))
            raise ConfigError(msg.format(iter1=k1, iter2=k2, duplicates=sorted_dups))
    return True

def warn_if_override(config, key, defaults):
    """
    Raise an error if config[key] overlaps with defaults unless config['suppress_warnings'] is True.

    Notes:
        - config[key] and defaults must both be iterable.

    Usage
    =====

    >>> config = {'vars': ['a', 'b', 'cat', 'psi', 'pi']}
    >>> warn_if_override(
    ... config,
    ... 'vars',
    ... {'cat': 1, 'pi': 2}
    ... ) # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ConfigError: Warning: 'vars' contains entries '['cat', 'pi']' ...

    >>> config = {'vars': ['a', 'b', 'cat', 'psi', 'pi'], 'suppress_warnings': True}
    >>> warn_if_override(
    ... config,
    ... 'vars',
    ... {'cat': 1, 'pi': 2}
    ... ) == config
    True

    """
    duplicates = set(defaults).intersection(set(config[key]))
    if duplicates and not config.get('suppress_warnings', False):
        sorted_dups = list(sorted(duplicates))
        msg = ("Warning: '{key}' contains entries '{duplicates}' which will override default "
               "values. If you intend to override to override defaults, you may suppress "
               "this warning by adding 'suppress_warnings=True' to the grader configuration.")
        raise ConfigError(msg.format(key=key, duplicates=sorted_dups))
    return config

class FormulaGrader(ItemGrader):
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
            percentage (default '0.1%'). Must be positive or zero.

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
            # Blacklist/Whitelist have additional validation that can't happen here, because
            # their validation is correlated with each other
            Required('blacklist', default=[]): [str],
            Required('whitelist', default=[]): Any(
                All([None], Length(min=1, max=1)),
                [str]
            ),
            Required('forbidden_strings', default=[]): [str],
            Required('forbidden_message', default=forbidden_default): str,
            Required('required_functions', default=[]): [str],
            Required('tolerance', default='0.01%'): Any(PercentageString, NonNegative(Number)),
            Required('metric_suffixes', default=False): bool,
            Required('samples', default=5): Positive(int),
            Required('variables', default=[]): All([str], all_unique),
            Required('numbered_vars', default=[]): All([str], all_unique),
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
    def default_equality_comparer(comparer_params, student_input, utils):
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
        ... 'comparer': FormulaGrader.default_equality_comparer
        ... }
        >>> result == expected
        True
        """
        if isinstance(expect, str):
            return cls.schema_expect({
                'comparer': cls.default_equality_comparer,
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

    debug_appendix_header_template = (
        "\n"
        "==============================================================\n"
        "{grader} Debug Info\n"
        "==============================================================\n"
        "Functions available during evaluation and allowed in answer:\n"
        "{functions_allowed}\n"
        "Functions available during evaluation and disallowed in answer:\n"
        "{functions_disallowed}\n"
    )
    debug_appendix_sample_template = (
        "\n"
        "==========================================\n"
        "Evaluation Data for Sample Number {sample_num} of {samples_total}\n"
        "==========================================\n"
        "Variables:\n"
        "{variables}\n"
        "Student Eval: {student_eval}\n"
        "Compare to:  {compare_parms_eval}\n" # compare_parms_eval is list, so start 1 char earlier
        "Comparer Function: {comparer}\n"
        "Comparison Satisfied: {comparer_result}\n"
        ""
    )

    def __init__(self, config=None, **kwargs):
        """
        Validate the Formulagrader's configuration.
        First, we allow the ItemGrader initializer to construct the function list.
        We then construct the lists of functions, suffixes and constants.
        Finally, we refine the sample_from entry.
        """
        super(FormulaGrader, self).__init__(config, **kwargs)

        # finish validating
        validate_blacklist_whitelist_config(self.config['blacklist'], self.config['whitelist'])
        validate_no_collisions(self.config, keys=['variables', 'user_constants'])
        warn_if_override(self.config, 'variables', DEFAULT_VARIABLES)
        warn_if_override(self.config, 'numbered_vars', DEFAULT_VARIABLES)
        warn_if_override(self.config, 'user_constants', DEFAULT_VARIABLES)
        warn_if_override(self.config, 'user_functions', DEFAULT_FUNCTIONS)

        self.permitted_functions = get_permitted_functions(self.config['whitelist'],
                                                           self.config['blacklist'],
                                                           self.config['user_functions'])

        # store the comparer utils
        self.comparer_utils = self.get_comparer_utils()

        # Set up the various lists we use
        self.functions, self.random_funcs = construct_functions(self.config["user_functions"])
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
            for varname in (self.config['variables'] + self.config['numbered_vars'])
        })
        self.config['sample_from'] = schema_sample_from(self.config['sample_from'])
        # Note that voluptuous ensures that there are no orphaned entries in sample_from

    def check_response(self, answer, student_input):
        """Check the student response against a given answer"""

        # Now perform the computations
        try:
            result, used_funcs = self.raw_check(answer, student_input)
            if result['ok'] is True or result['ok'] == 'partial':
                self.post_eval_validation(student_input, used_funcs)
            return result
        except (StudentFacingError, InvalidInput):
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

    def generate_variable_list(self, answer, student_input):
        """
        Generates the list of variables required to perform a comparison and the
        corresponding sampling dictionary, taking into account any numbered variables.

        Returns variable_list, sample_from_dict
        """
        # Pre-parse all expressions (these all get cached)
        parsers = [
            parsercache.get_parser(expr, self.suffixes)
            for expr in answer['expect']['comparer_params']
            ]
        # If the student input is not empty, parse that too
        if not (student_input is None or student_input.strip() == ""):
            parsers.append(parsercache.get_parser(student_input, self.suffixes))
        # Create a list of all variables used in the expressions
        vars_used = set().union(*[parser.variables_used for parser in parsers])

        # Initiate the variables list and sample_from dictionary
        variable_list = self.config['variables'][:]
        sample_from_dict = self.config['sample_from'].copy()

        # Find all unassigned variables
        bad_vars = set(var for var in vars_used if var not in variable_list)

        # Check to see if any unassigned variables are numbered_vars
        regexp = numbered_vars_regexp(self.config['numbered_vars'])
        for var in bad_vars:
            match = regexp.match(var)  # Returns None if no match
            if match:
                # This variable is a numbered_variable
                # Go and add it to variable_list with the appropriate sampler
                (full_string, head) = match.groups()
                variable_list.append(full_string)
                sample_from_dict[full_string] = sample_from_dict[head]

        return variable_list, sample_from_dict

    def raw_check(self, answer, student_input):
        """Perform the numerical check of student_input vs answer"""
        # Generate samples
        variable_list, sample_from_dict = self.generate_variable_list(answer,
                                                                      student_input)
        var_samples = gen_symbols_samples(variable_list,
                                          self.config['samples'],
                                          sample_from_dict)

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
                          variables=varlist,
                          functions=funclist,
                          suffixes=self.suffixes)[0]
                for param in answer['expect']['comparer_params']
                ]

            student_eval, used_funcs = evaluator(student_input,
                                                 variables=varlist,
                                                 functions=funclist,
                                                 suffixes=self.suffixes)

            # Check if expressions agree
            comparer_result = comparer(comparer_params_eval, student_eval, self.comparer_utils)
            if self.config['debug']:
                self.log_sample_info(i, varlist, funclist, student_eval,
                                     comparer, comparer_params_eval, comparer_result)

            if not comparer_result:
                num_failures += 1
                if num_failures > self.config["failable_evals"]:
                    return {'ok': False, 'grade_decimal': 0, 'msg': ''}, used_funcs

        # This response appears to agree with the expected answer
        return {
            'ok': answer['ok'],
            'grade_decimal': answer['grade_decimal'],
            'msg': answer['msg']
        }, used_funcs

    def log_sample_info(self, index, varlist, funclist, student_eval,
                        comparer, comparer_params_eval, comparer_result):
        """Add sample information to debug log"""
        pp = PrettyPrinter(indent=4)
        if index == 0:
            header = self.debug_appendix_header_template.format(
                grader=self.__class__.__name__,
                # The regexp replaces memory locations, e.g., 0x10eb1e848 -> 0x...
                functions_allowed=pp.pformat({f: funclist[f] for f in funclist
                                              if f in self.permitted_functions}),
                functions_disallowed=pp.pformat({f: funclist[f] for f in funclist
                                                 if f not in self.permitted_functions}),
            )
            self.log(re.sub(r"0x[0-9a-fA-F]+", "0x...", header))
        self.log(self.debug_appendix_sample_template.format(
            sample_num=index + 1, # to account for 0 index
            samples_total=self.config['samples'],
            variables=pp.pformat(varlist),
            student_eval=student_eval,
            comparer=re.sub(r"0x[0-9a-fA-F]+", "0x...", str(comparer)),
            comparer_result=comparer_result,
            compare_parms_eval=pp.pformat(comparer_params_eval)
        ))

    def post_eval_validation(self, expr, used_funcs):
        """Runs several post-evaluation validator functions"""
        validate_forbidden_strings_not_used(expr,
                                            self.config['forbidden_strings'],
                                            self.config['forbidden_message'])

        validate_required_functions_used(used_funcs, self.config['required_functions'])

        validate_only_permitted_functions_used(used_funcs, self.permitted_functions)

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
            Required('numbered_vars', default=[]): [],
            Required('sample_from', default={}): {},
            Required('failable_evals', default=0): 0
        })
