"""
math_helpers.py

Various helper routines for math graders.
Also includes MathMixin, a mixin class for math graders.
"""
from __future__ import print_function, division, absolute_import, unicode_literals

import itertools
import six
import re
import pprint
from numbers import Number
from collections import namedtuple

from voluptuous import Schema, Required, Any, All, Length, Coerce

from mitxgraders.baseclasses import ItemGrader
from mitxgraders.exceptions import InvalidInput, ConfigError, MissingInput
from mitxgraders.comparers import CorrelatedComparer
from mitxgraders.sampling import (VariableSamplingSet, RealInterval, DiscreteSet, DependentSampler,
                                  gen_symbols_samples, construct_functions,
                                  construct_constants, construct_suffixes,
                                  schema_user_functions,
                                  validate_user_constants)
from mitxgraders.helpers.calc import (DEFAULT_VARIABLES, DEFAULT_FUNCTIONS, DEFAULT_SUFFIXES,
                                      MathArray, parse, within_tolerance)
from mitxgraders.helpers.validatorfuncs import (Positive, NonNegative, all_unique,
                                                PercentageString, text_string)


def validate_blacklist_whitelist_config(default_funcs, blacklist, whitelist):
    """Validates the whitelist/blacklist configuration.

    Arguments:
        default_funcs: an iterable whose elements are are function names
            Examples: {'func1':..., 'func2':..., ...} or ['func1', 'func2']
        blacklist ([str]): a list of function names
        whitelist ([str]): a list of function names

    Notes: Voluptuous should already have type-checked blacklist and whitelist.
    Now check:
    1. whitelist/blacklist are not both used
    2. All whitelist/blacklist functions actually exist in default_funcs
    """
    if blacklist and whitelist:
        raise ConfigError("Cannot whitelist and blacklist at the same time")
    for func in blacklist:
        # no need to check user_functions too ... if you don't want student to
        # use one of the user_functions, just don't add it in the first place.
        if func not in default_funcs:
            raise ConfigError("Unknown function in blacklist: {func}".format(func=func))

    if whitelist == [None]:
        return

    for func in whitelist:
        if func not in default_funcs:
            raise ConfigError("Unknown function in whitelist: {func}".format(func=func))

def validate_forbidden_strings_not_used(expr, forbidden_strings, forbidden_msg):
    """
    Ignoring whitespace, checking that expr does not contain any forbidden_strings.
    expr can be a string, dictionary, or a list of strings.

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
    >>> try:
    ...     validate_forbidden_strings_not_used(
    ...         'sin(x+x)',
    ...         ['*x', '+ x', '- x'],
    ...         'A forbidden string was used!')
    ... except InvalidInput as error:
    ...     print(error)
    A forbidden string was used!

    Works on lists of strings:
    >>> try:
    ...     validate_forbidden_strings_not_used(
    ...         ['x', 'x^2'],
    ...         ['*x', '+ x', '- x'],
    ...         'A forbidden string was used!')
    ... except InvalidInput as error:
    ...     print(error)
    True

    And also dicts:
    >>> try:
    ...     validate_forbidden_strings_not_used(
    ...         {'upper': 'x', 'lowerl': 'x^2', 'integrand': 'x + x'},
    ...         ['*x', '+ x', '- x'],
    ...         'A forbidden string was used!')
    ... except InvalidInput as error:
    ...     print(error)
    A forbidden string was used!
    """
    if isinstance(expr, dict):
        expr = [v for k, v in expr.items()]
    elif not isinstance(expr, list):
        expr = [expr]
    for expression in expr:
        stripped_expr = expression.replace(' ', '')
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
    >>> try:
    ...     validate_only_permitted_functions_used(
    ...         set(['f', 'Sin', 'h']),
    ...         set(['f', 'g', 'sin', 'cos']))
    ... except InvalidInput as error:
    ...     print(error)
    Invalid Input: function(s) 'Sin', 'h' not permitted in answer
    """
    used_not_permitted = sorted([f for f in used_funcs if f not in permitted_functions])
    if used_not_permitted:
        func_names = ", ".join(["'{f}'".format(f=f) for f in used_not_permitted])
        message = "Invalid Input: function(s) {} not permitted in answer".format(func_names)
        raise InvalidInput(message)
    return True

def get_permitted_functions(default_funcs, whitelist, blacklist, always_allowed):
    """
    Constructs a set of functions whose usage is permitted.

    Arguments:
        default_funcs: an iterable whose elements are are function names
            Examples: {'func1':..., 'func2':..., ...} or ['func1', 'func2']
        blacklist ([str]): function names to remove from default_funcs
        whitelist ([str]): function names to keep from default_funcs
        always_allowed: an iterable whose elements are function names that
            are always allowed.

    Note: whitelist and blacklist cannot both be non-empty

    Usage
    =====
    Whitelist some functions:
    >>> default_funcs = {'sin': None, 'cos': None, 'tan': None}
    >>> always_allowed = {'f1': None, 'f2': None}
    >>> get_permitted_functions(
    ...     default_funcs,
    ...     ['sin', 'cos'],
    ...     [],
    ...     always_allowed
    ... ) == set(['sin', 'cos', 'f1', 'f2'])
    True

    If whitelist=[None], all defaults are disallowed:
    >>> default_funcs = {'sin': None, 'cos': None, 'tan': None}
    >>> always_allowed = {'f1': None, 'f2': None}
    >>> get_permitted_functions(
    ...     default_funcs,
    ...     [None],
    ...     [],
    ...     always_allowed
    ... ) == set(['f1', 'f2'])
    True

    Blacklist some functions:
    >>> default_funcs = {'sin': None, 'cos': None, 'tan': None}
    >>> always_allowed = {'f1': None, 'f2': None}
    >>> get_permitted_functions(
    ...     default_funcs,
    ...     [],
    ...     ['sin', 'cos'],
    ...     always_allowed
    ... ) == set(['tan', 'f1', 'f2'])
    True

    Blacklist and whitelist cannot be simultaneously used:
    >>> default_funcs = {'sin': None, 'cos': None, 'tan': None}
    >>> always_allowed = {'f1': None, 'f2': None}
    >>> try:
    ...     get_permitted_functions(
    ...         default_funcs,
    ...         ['sin'],
    ...         ['cos'],
    ...         always_allowed)
    ... except ValueError as error:
    ...     print(error)
    whitelist and blacklist cannot both be non-empty
    """
    # should never trigger except in doctest above,
    # Grader's config validation should raise an error first
    if whitelist and blacklist:
        raise ValueError('whitelist and blacklist cannot both be non-empty')
    if whitelist == []:
        permitted_functions = set(always_allowed).union(
            set(default_funcs)
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
    >>> try:
    ...     validate_required_functions_used(
    ...     ['sin', 'cos', 'F', 'g'],
    ...     ['cos', 'f'])
    ... except InvalidInput as error:
    ...     print(error)
    Invalid Input: Answer must contain the function f
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
    regexp = (r"^((" + head_list + ")"  # Start and match any head (capture full string, head)
              r"_{"  # match _{
              r"(?:[-]?[1-9]\d*|0)"  # match number pattern
              r"})$")  # match closing }, close group, and end of string
    return re.compile(regexp)

def validate_no_collisions(config, keys):
    """
    Validates no collisions between iterable config fields specified by keys.

    Usage
    =====

    Duplicate entries raise a ConfigError:
    >>> keys = ['variables', 'user_constants', 'numbered_vars']
    >>> try:
    ...     validate_no_collisions({
    ...         'variables':['a', 'b', 'c', 'x', 'y'],
    ...         'user_constants':{'x': 5, 'y': 10},
    ...         'numbered_vars':['phi', 'psi']
    ...         }, keys)
    ... except ConfigError as error:
    ...     print(error)
    'user_constants' and 'variables' contain duplicate entries: ['x', 'y']

    >>> try:
    ...     validate_no_collisions({
    ...         'variables':['a', 'psi', 'phi', 'X', 'Y'],
    ...         'user_constants':{'x': 5, 'y': 10},
    ...         'numbered_vars':['phi', 'psi']
    ...         }, keys)
    ... except ConfigError as error:
    ...     print(error)
    'numbered_vars' and 'variables' contain duplicate entries: ['phi', 'psi']

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
    >>> defaults = {'cat': 1, 'pi': 2}
    >>> try:
    ...     warn_if_override(config, 'vars', defaults) # doctest: +ELLIPSIS
    ... except ConfigError as error:
    ...     print(error)
    Warning: 'vars' contains entries 'cat', 'pi' ...

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
        text_dups = ', '.join(sorted(("'{}'".format(dup) for dup in duplicates)))
        msg = ("Warning: '{key}' contains entries {duplicates} which will override default "
               "values. If you intend to override defaults, you may suppress "
               "this warning by adding 'suppress_warnings=True' to the grader configuration.")
        raise ConfigError(msg.format(key=key, duplicates=text_dups))
    return config


class MathMixin(object):
    """This is a mixin class that provides generic math handling capabilities"""
    # Set up a bunch of defaults
    default_variables = DEFAULT_VARIABLES.copy()
    default_functions = DEFAULT_FUNCTIONS.copy()
    default_suffixes = DEFAULT_SUFFIXES.copy()
    
    # Set up some debugging templates
    debug_appendix_eval_header_template = (
        "\n"
        "==============================================================\n"
        "{grader} Debug Info\n"
        "==============================================================\n"
        "Functions available during evaluation and allowed in answer:\n"
        "{functions_allowed}\n"
        "Functions available during evaluation and disallowed in answer:\n"
        "{functions_disallowed}\n"
    )
    debug_appendix_comparison_template = (
        "\n"
        "==========================================\n"
        "Comparison Data for All {samples_total} Samples\n"
        "==========================================\n"
        "Comparer Function: {comparer}\n"
        "Comparison Results:\n"
        "{comparer_results}\n"
        ""
    )
    
    # Set up the comparison utilities
    Utils = namedtuple('Utils', ['tolerance', 'within_tolerance'])
    
    def get_comparer_utils(self):
        """Get the utils for comparer function."""
        
        def _within_tolerance(x, y):
            return within_tolerance(x, y, self.config['tolerance'])
        
        return self.Utils(tolerance=self.config['tolerance'],
                          within_tolerance=_within_tolerance)
    
    # Set up a bunch of configuration options
    math_config_options = {
        Required('user_functions', default={}): schema_user_functions,
        Required('user_constants', default={}): validate_user_constants(Number, MathArray),
        # Blacklist/Whitelist have additional validation that can't happen here, because
        # their validation is correlated with each other
        Required('blacklist', default=[]): [text_string],
        Required('whitelist', default=[]): Any(
            All([None], Length(min=1, max=1)),
            [text_string]
        ),
        Required('tolerance', default='0.01%'): Any(PercentageString, NonNegative(Number)),
        Required('samples', default=5): Positive(int),
        Required('variables', default=[]): All([text_string], all_unique),
        Required('numbered_vars', default=[]): All([text_string], all_unique),
        Required('sample_from', default={}): dict,
        Required('failable_evals', default=0): NonNegative(int),
        Required('forbidden_strings', default=[]): [text_string],
        Required('forbidden_message', default="Invalid Input: This particular answer is forbidden"): text_string,
        Required('metric_suffixes', default=False): bool,
        Required('required_functions', default=[]): [text_string],
        Required('instructor_vars', default=[]): [text_string],
    }
    
    def validate_math_config(self):
        """Performs generic math configuration validation"""
        validate_blacklist_whitelist_config(self.default_functions,
                                            self.config['blacklist'],
                                            self.config['whitelist'])
        
        # Make a copy of self.default_variables, so we don't change the base version
        self.default_variables = self.default_variables.copy()
        
        # Remove any deleted user constants from self.default_variables
        remove_keys = [key for key in self.config['user_constants'] if self.config['user_constants'][key] is None]
        for entry in remove_keys:
            if entry in self.default_variables:
                del self.default_variables[entry]
            del self.config['user_constants'][entry]
        
        warn_if_override(self.config, 'variables', self.default_variables)
        warn_if_override(self.config, 'numbered_vars', self.default_variables)
        warn_if_override(self.config, 'user_constants', self.default_variables)
        warn_if_override(self.config, 'user_functions', self.default_functions)
        
        validate_no_collisions(self.config, keys=['variables', 'user_constants'])
        
        self.permitted_functions = get_permitted_functions(self.default_functions,
                                                           self.config['whitelist'],
                                                           self.config['blacklist'],
                                                           self.config['user_functions'])
        
        # Set up the various lists we use
        self.functions, self.random_funcs = construct_functions(self.default_functions,
                                                                self.config["user_functions"])
        self.constants = construct_constants(self.default_variables, self.config["user_constants"])
        self.suffixes = construct_suffixes(self.default_suffixes, self.config["metric_suffixes"])
        
        # Construct the schema for sample_from
        # First, accept all VariableSamplingSets
        # Then, accept any list that RealInterval can interpret
        # Finally, single numbers or tuples of numbers will be handled by DiscreteSet
        schema_sample_from = Schema({
            Required(varname, default=RealInterval()):
                Any(VariableSamplingSet,
                    All(list, Coerce(RealInterval)),
                    Coerce(DiscreteSet))
            for varname in (self.config['variables'] + self.config['numbered_vars'])
        })
        self.config['sample_from'] = schema_sample_from(self.config['sample_from'])
        # Note that voluptuous ensures that there are no orphaned entries in sample_from
    
    def check_math_response(self, answer, student_input, **kwargs):
        """Check the student response against a given answer"""
        result, used_funcs = self.raw_check(answer, student_input, **kwargs)
        
        if result['ok'] is True or result['ok'] == 'partial':
            self.post_eval_validation(student_input, used_funcs)
        return result

    def post_eval_validation(self, expr, used_funcs):
        """Runs several post-evaluation validator functions"""
        validate_forbidden_strings_not_used(expr,
                                            self.config['forbidden_strings'],
                                            self.config['forbidden_message'])
        
        validate_required_functions_used(used_funcs, self.config['required_functions'])
        
        validate_only_permitted_functions_used(used_funcs, self.permitted_functions)
    
    @staticmethod
    def get_used_vars(expressions):
        """
        Get the variables used in expressions

        Arguments:
            expressions: an iterable collection of expressions

        Returns:
            vars_used ({str}): set of variables used
        """
        is_empty = lambda x: x is None or x.strip() == ''
        expressions = [expr for expr in expressions if not is_empty(expr)]
        # Pre-parse all expressions (these all get cached)
        parsed_expressions = [parse(expr) for expr in expressions]
        # Create a list of all variables used in the expressions
        vars_used = set().union(*[p.variables_used for p in parsed_expressions])
        return vars_used
    
    def gen_var_and_func_samples(self, *args):
        """
        Generate a list of variable/function sampling dictionaries from the supplied arguments.
        Arguments may be strings, lists of strings, or dictionaries with string values.
        Does not flag any bad variables.
        """
        # Make a list of all expressions to check for variables
        expressions = []
        for entry in args:
            if isinstance(entry, six.text_type):
                expressions.append(entry)
            elif isinstance(entry, list):
                expressions += entry
            elif isinstance(entry, dict):
                expressions += [v for k, v in entry.items()]
        
        # Generate the variable list
        variables, sample_from_dict = self.generate_variable_list(expressions)

        # Check if a dictionary of sibling variables has been provided, and sample those too
        for entry in args:
            if isinstance(entry, dict):
                if all([k.startswith('sibling_') for k in entry]):
                    # This is a sibling dictionary. Add it to the list of variables to sample.
                    for k in entry:
                        variables.append(k)
                        if entry[k] == '':
                            raise MissingInput('Cannot grade answer, a required input is missing.')
                        sample_from_dict[k] = DependentSampler(formula=entry[k])
                    break
        
        # Generate the samples
        var_samples = gen_symbols_samples(variables,
                                          self.config['samples'],
                                          sample_from_dict,
                                          self.functions,
                                          self.suffixes,
                                          self.constants)
        
        func_samples = gen_symbols_samples(list(self.random_funcs.keys()),
                                           self.config['samples'],
                                           self.random_funcs,
                                           self.functions,
                                           self.suffixes,
                                           {})
        
        return var_samples, func_samples
    
    def generate_variable_list(self, expressions):
        """
        Generates the list of variables required to perform a comparison and the
        corresponding sampling dictionary, taking into account any numbered variables.
        Bad variables are not flagged here.

        Returns variable_list, sample_from_dict
        """
        vars_used = self.get_used_vars(expressions)
        
        # Seed the variables list with all allowed variables
        variable_list = list(self.config['variables'])
        # Make a copy of the sample_from dictionary, so we can add numbered variables to it
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
    
    def log_comparison_info(self, comparer, comparer_results):
        """Add sample comparison information to debug log"""
        msg = self.debug_appendix_comparison_template.format(
            samples_total=self.config['samples'],
            comparer=re.sub(r"0x[0-9a-fA-F]+", "0x...", six.text_type(comparer)),
            comparer_results=pprint.pformat(comparer_results)
        )
        msg = msg.replace("<", "&lt;").replace(">", "&gt;")
        self.log(msg)
    
    @staticmethod
    def consolidate_results(results, answer, failable_evals):
        """
        Consolidate comparer result(s) into just one result.

        Arguments:
            results: a list of results dicts
            answer (dict): correctness data for the expected answer, or None for all correct
            failable_evals: int
        """
        # Handle an empty answer
        if answer is None:
            answer = {'ok': True, 'grade_decimal': 1, 'msg': ''}
        
        # answer can contain extra keys, so prune them
        pruned_answer = {key: answer[key] for key in ['ok', 'grade_decimal', 'msg']}
        
        # Check each result for correctness
        num_failures = 0
        for result in results:
            if result['ok'] != True:
                num_failures += 1
                if len(results) == 1 or num_failures > failable_evals:
                    return result
        
        # This response appears to agree with the expected answer
        return pruned_answer
    
    def compare_evaluations(self, compare_params_evals, student_evals, comparer, utils):
        """
        Compare the student evaluations to the expected results.
        """
        results = []
        if isinstance(comparer, CorrelatedComparer):
            result = comparer(compare_params_evals, student_evals, utils)
            results.append(ItemGrader.standardize_cfn_return(result))
        else:
            for compare_params_eval, student_eval in zip(compare_params_evals, student_evals):
                result = comparer(compare_params_eval, student_eval, utils)
                results.append(ItemGrader.standardize_cfn_return(result))
        
        # TODO: Take out this if statement - should always work.
        # However, presently doesn't, because subgraders don't have access to the master debuglog.
        if self.config['debug']:
            self.log_comparison_info(comparer, results)
        
        return results
    
    def log_eval_info(self, index, varlist, funclist, **kwargs):
        """Add sample information to debug log"""
        
        if index == 0:
            header = self.debug_appendix_eval_header_template.format(
                grader=self.__class__.__name__,
                # The regexp replaces memory locations, e.g., 0x10eb1e848 -> 0x...
                functions_allowed=pprint.pformat({f: funclist[f] for f in funclist
                                                  if f in self.permitted_functions}),
                functions_disallowed=pprint.pformat({f: funclist[f] for f in funclist
                                                     if f not in self.permitted_functions}),
            )
            header = re.sub(r"0x[0-9a-fA-F]+", "0x...", header)
            header = header.replace('RandomFunction.gen_sample.<locals>.', '')
            header = header.replace("<", "&lt;").replace(">", "&gt;")
            self.log(header)
        msg = self.debug_appendix_eval_template.format(
            sample_num=index + 1,  # to account for 0 index
            samples_total=self.config['samples'],
            variables=pprint.pformat(varlist),
            **kwargs
        )
        msg = msg.replace("<", "&lt;").replace(">", "&gt;")
        self.log(msg)
