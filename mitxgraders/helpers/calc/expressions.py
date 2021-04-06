r"""
expressions.py

Defines classes to parse and evaluate mathematical expressions. Implements
similar functionality and API as edX's calc.py, but re-written with enhancements
and to better separate parsing and evaluation.

To evaluate a mathematical expression like '2^a + [x, 2]*[y, 4]', we proceed
in two steps:

    1. First, the expression is parsed into a tree

                               /--- NUMBER --- '2'
                 /--- POWER ---
                /              \--- VARIABLE --- 'a'
               /
              /
        SUM --  -- OP -- '+'
              \                                   /--- VARIABLE --- 'x'
               \                    /--- ARRAY ---
                \                  /              \--- NUMBER --- '2'
                 \                /
                  \--- PRODUCT ---  -- OP -- '*'
                                  \
                                   \              /--- VARIABLE --- 'y'
                                    \--- ARRAY ---
                                                  \--- NUMBER --- '4'

    2. Next, the tree is evaluated from the leaves upwards.

This file defines two main classes:

 - MathParser, used to parse mathematical strings into a tree
 - MathExpression, holds the parse tree for a given mathematical expression
   and can be used to evaluate the tree with a given scope.
and a function:

and also:
 - parse: a function that delegates to PARSER.parse
 - evaluator: a convenience function that parses and evaluates strings.

Both `parse` and `evaluator` share a global MathParser instance for caching
purposes.
"""
from __future__ import print_function, division, absolute_import, unicode_literals

import copy
from collections import namedtuple
import numpy as np
import six
from pyparsing import (
    CaselessLiteral,
    Combine,
    Forward,
    Group,
    Literal,
    MatchFirst,
    Optional,
    ParseResults,
    Suppress,
    Word,
    FollowedBy,
    ZeroOrMore,
    alphanums,
    alphas,
    nums,
    stringEnd,
    ParseException,
    delimitedList
)
from mitxgraders.exceptions import StudentFacingError
from mitxgraders.helpers.validatorfuncs import get_number_of_args
from mitxgraders.helpers.calc.math_array import MathArray, is_vector
from mitxgraders.helpers.calc.robust_pow import robust_pow
from mitxgraders.helpers.calc.mathfuncs import (
    DEFAULT_VARIABLES, DEFAULT_FUNCTIONS, DEFAULT_SUFFIXES)
from mitxgraders.helpers.calc.exceptions import (
    CalcError,
    CalcOverflowError,
    CalcZeroDivisionError,
    FunctionEvalError,
    UnableToParse,
    ArgumentError,
    UnbalancedBrackets,
    UndefinedVariable,
    UndefinedFunction
)

# Numpy's default behavior is to raise warnings on div by zero and overflow. Let's change that.
# https://docs.scipy.org/doc/numpy-1.13.0/reference/generated/numpy.seterr.html
# https://docs.scipy.org/doc/numpy-1.13.0/reference/generated/numpy.seterrcall.html#numpy.seterrcall

def handle_np_floating_errors(err, flag):
    """
    Used by np.seterr to handle floating point errors with flag set to 'call'.
    """
    if 'divide by zero' in err:
        raise ZeroDivisionError
    elif 'overflow' in err:
        raise OverflowError
    elif 'value' in err:
        raise ValueError
    else:  # pragma: no cover
        raise Exception(err)

np.seterrcall(handle_np_floating_errors)
np.seterr(divide='call', over='call', invalid='call')

class BracketValidator(object):
    """
    Validates that the square brackets and parentheses in a given expression
    are balanced.

    Usage
    =====

    >>> BV = BracketValidator
    >>> expr = '1 + ( ( x + 1 )^2 + ( + [T_{1'
    >>> try:
    ...     BV.validate(expr)# doctest:                 +NORMALIZE_WHITESPACE
    ... except UnbalancedBrackets as error:
    ...     print(error)
    Invalid Input:
    1 curly brace was opened without being closed (highlighted below)
    2 parentheses were opened without being closed (highlighted below)
    1 square bracket was opened without being closed (highlighted below)
    <code>1 + <mark>(</mark> ( x + 1 )^2 + <mark>(</mark> + <mark>[</mark>T_<mark>{</mark>1</code>

    NOTE: This class only contains class variables and static methods.
    It could just as well be a separate file/module.
    """

    # Stores bracket metadata
    Bracket = namedtuple('Bracket', ['char', 'partner', 'is_closer', 'name', 'plural'])

    # The brackets that we care about
    bracket_registry = {
        '{': Bracket(char='{', partner='}', is_closer=False, name='curly brace', plural='curly braces'),
        '}': Bracket(char='}', partner='{', is_closer=True, name='curly brace', plural='curly braces'),
        '(': Bracket(char='(', partner=')', is_closer=False, name='parenthesis', plural='parentheses'),
        ')': Bracket(char=')', partner='(', is_closer=True, name='parenthesis', plural='parentheses'),
        '[': Bracket(char='[', partner=']', is_closer=False, name='square bracket', plural='square brackets'),
        ']': Bracket(char=']', partner='[', is_closer=True, name='square bracket', plural='square brackets')
    }

    # Stores information about a bracket instance
    StackEntry = namedtuple('StackEntry', ['index', 'bracket'])

    @staticmethod
    def validate(formula):
        """
        Scan through a formula, validating it for unbalanced parentheses.
        """
        BV = BracketValidator
        stack = []
        for index, char in enumerate(formula):
            if char not in BV.bracket_registry:
                continue
            bracket = BV.bracket_registry[char]
            current = BV.StackEntry(index=index, bracket=bracket)
            if bracket.is_closer:
                try:
                    previous = stack.pop()
                except IndexError:  # happens if stack is empty
                    BV.raise_close_without_open(formula, current)
                if bracket.partner != previous.bracket.char:
                    BV.raise_wrong_closing_bracket(formula, current, previous)
            else:
                stack.append(BV.StackEntry(index=index, bracket=bracket))

        if stack:
            BV.raise_open_without_close(formula, stack)

        return formula

    @staticmethod
    def raise_close_without_open(formula, current):
        """
        Called when scan encounters a closing bracket without matching opener,
        for example: "1, 2, 3]".
        - current is the offending StackEntry
        """
        msg = ("Invalid Input: a {current.bracket.name} was closed without ever "
               "being opened, highlighted below.\n{highlight}")

        indices = [current.index]
        highlight = BracketValidator.highlight_formula(formula, indices)
        formatted = msg.format(current=current, highlight=highlight)
        raise UnbalancedBrackets(formatted)

    @staticmethod
    def raise_wrong_closing_bracket(formula, current, previous):
        """
        Called when scan encounters a closing bracket that does not match the
        previous opening bracket, for example: "[(1, 2, 3])"
        - current and previous are the offending StackEntry pairs
        """
        msg = ("Invalid Input: a {previous.bracket.name} was opened and then "
               "closed by a {current.bracket.name}, highlighted below.\n"
               "{highlight}")

        indices = [previous.index, current.index]
        highlight = BracketValidator.highlight_formula(formula, indices)
        formatted = msg.format(current=current, previous=previous, highlight=highlight)
        raise UnbalancedBrackets(formatted)

    @staticmethod
    def raise_open_without_close(formula, stack):
        """
        Called when un-closed opening brackets remain at the end of scan, for
        example: "(1 + 2) + ( 3 + (".
        - stack is the remaining stack
        """
        bracket_registry = BracketValidator.bracket_registry
        still_open = {}
        for key in sorted(bracket_registry):
            if bracket_registry[key].is_closer:
                continue
            num_opened = sum([entry.bracket.char == bracket_registry[key].char for entry in stack])
            if num_opened:
                still_open[key] = num_opened

        # sort so error messages come in definite order, for testing purposes
        sorted_still_open = sorted(still_open.keys(), key=lambda x: bracket_registry[x].name)

        if still_open:
            message = "Invalid Input:\n"
            for key in sorted_still_open:
                if still_open[key] == 1:
                    message += ('{count} {name} was opened without being closed '
                                '(highlighted below)\n'
                                .format(count=still_open[key], name=bracket_registry[key].name))
                else:
                    message += ('{count} {plural} were opened without being closed '
                                '(highlighted below)\n'
                                .format(count=still_open[key], plural=bracket_registry[key].plural))

        indices = [entry.index for entry in stack]
        highlight = BracketValidator.highlight_formula(formula, indices)
        message += highlight
        raise UnbalancedBrackets(message)

    @staticmethod
    def highlight_formula(formula, unsorted_indices):
        indices = sorted(unsorted_indices, reverse=True)
        for index in indices:
            formula = BracketValidator.highlight_index(formula, index)
        #
        return "<code>{}</code>".format(formula)

    @staticmethod
    def highlight_index(formula, index):
        char = formula[index]
        # <mark> is an HTML tag for marking text as important.
        # edX renders it like a highlighter, with yellowish background.
        return formula[:index] + '<mark>{}</mark>'.format(char) + formula[index+1:]

def cast_np_numeric_as_builtin(obj, map_across_lists=False):
    """
    Cast numpy numeric types as builtin python types.

    NOTE: We do this because instances of np.number behave badly with MathArray.
    See https://github.com/mitodl/mitx-grading-library/issues/124

    Examples:
    >>> import numpy as np
    >>> x = 1.0
    >>> x64 = np.float64(x)
    >>> y = 5
    >>> y64 = np.int64(y)
    >>> z = 3 + 2j
    >>> z128 = np.complex128(z)
    >>> examples = [x, x64, y, y64, z, z128]
    >>> [type(cast_np_numeric_as_builtin(ex)).__name__ for ex in examples]
    ['float', 'float', 'int', 'int', 'complex', 'complex']

    Leaves MathArrays alone:
    >>> from mitxgraders.helpers.calc.math_array import MathArray
    >>> A = MathArray([1, 2, 3])
    >>> cast_np_numeric_as_builtin(A)
    MathArray([1, 2, 3])

    Optionally, map across a list:
    >>> target = [np.float64(1.0), np.float64(2.0)]
    >>> result = cast_np_numeric_as_builtin(target, map_across_lists=True)
    >>> [type(item).__name__ for item in result]
    ['float', 'float']

    """
    if isinstance(obj, np.number):
        return obj.item()
    if map_across_lists and isinstance(obj, list):
        return [item.item() if isinstance(item, np.number) else item
                for item in obj]
    return obj

class MathParser(object):
    """
    Parses mathematical expressions into trees and caches the result.
    Expression trees are returned as MathExpression objects, which can then
    be evaluated.

    Usage
    =====
    >>> new_parser = MathParser()
    >>> parsed = new_parser.parse('2*x + 5')
    >>> isinstance(parsed, MathExpression)
    True
    >>> parsed
    <BLANKLINE>
    <sum>
      <product>
        <number>
          <num>2</num>
        </number>
        <op>*</op>
        <variable>
          <varname>x</varname>
        </variable>
      </product>
      <op>+</op>
      <number>
        <num>5</num>
      </number>
    </sum>
    """

    def __init__(self):
        self.cache = {}
        self.grammar = self.get_grammar()

        # Internal storage that is reset at the end of calls to MathParser.parse
        # Needed at the instance level because callbacks during parsing only have
        # access to self
        self.variables_used = set()
        self.functions_used = set()
        self.suffixes_used = set()
        self.max_array_dim_used = 0

    def reset_storage(self):
        self.variables_used = set()
        self.functions_used = set()
        self.suffixes_used = set()

    def variable_parse_action(self, tokens):
        """
        When pyparsing encounters a variable, store it in variables_used
        """
        self.variables_used.add(tokens[0][0])

    def function_parse_action(self, tokens):
        """
        When pyparsing encounters a function, store it in functions_used
        """
        self.functions_used.add(tokens[0][0])

    def suffix_parse_action(self, tokens):
        """
        When pyparsing encounters a suffix, store it in suffixes_used
        """
        self.suffixes_used.add(tokens[0])

    @staticmethod
    def group_if_multiple(name):
        """
        Generates a parse action that groups ParseResults with given name if
        ParseResults has multiple children.
        """
        def _parse_action(tokens):
            """Wrap children in a group if there are multiple"""
            if len(tokens) > 1:
                return ParseResults(toklist=[tokens], name=name)
            return tokens

        return _parse_action

    # TODO: Possibly refactor this into separate pieces;
    # example: accessing the variable name parser could be useful in a few places
    def get_grammar(self):
        """
        Defines our grammar for mathematical expressions.

        Possibly helpful:
            - BNF form of context-free grammar https://en.wikipedia.org/wiki/Backus%E2%80%93Naur_form
            - Some pyparsing docs http://infohost.nmt.edu/~shipman/soft/pyparsing/web/index.html
        """

        # Define + and -
        plus = Literal("+")

        # Also accept unicode emdash
        emdash = Literal("\u2014")
        emdash.setParseAction(lambda: "-")
        
        minus = Literal("-") | emdash
        plus_minus = plus | minus

        # 1 or 1.0 or .1
        number_part = Word(nums)
        inner_number = Combine((number_part + Optional("." + Optional(number_part)))
                               |
                               ("." + number_part))
        # Combine() joints the matching parts together in a single token,
        # and requires that the matching parts be contiguous (no spaces)

        # Define our suffixes
        suffix = Word(alphas + '%')
        suffix.setParseAction(self.suffix_parse_action)

        # Construct number as a group consisting of a text string ("num") and an optional suffix.
        # num can include a decimal number and numerical exponent, and can be
        # converted to a number using float()
        # suffix may contain alphas or %
        # Spaces are ignored inside numbers
        # Group wraps everything up into its own ParseResults object when parsing
        number = Group(
            Combine(
                inner_number +
                Optional(CaselessLiteral("E") + Optional(plus_minus) + number_part),
            )("num")
            + Optional(suffix)("suffix")
        )("number")
        # Note that calling ("name") on the end of a parser is equivalent to calling
        # parser.setResultsName, which is used to pull that result out of a parsed
        # expression like a dictionary.

        # Construct variable and function names
        front = Word(alphas, alphanums)  # must start with alpha
        subscripts = Word(alphanums + '_') + ~FollowedBy('{')  # ~ = not
        lower_indices = Literal("_{") + Optional("-") + Word(alphanums) + Literal("}")
        upper_indices = Literal("^{") + Optional("-") + Word(alphanums) + Literal("}")
        # Construct an object name in either of two forms:
        #   1. front + subscripts + tail
        #   2. front + lower_indices + upper_indices + tail
        # where:
        #   front (required):
        #       starts with alpha, followed by alphanumeric
        #   subscripts (optional):
        #       any combination of alphanumeric and underscores
        #   lower_indices (optional):
        #       Of form "_{(-)<alphanumeric>}"
        #   upper_indices (optional):
        #       Of form "^{(-)<alphanumeric>}"
        #   tail (optional):
        #       any number of primes
        name = Combine(front +
                       Optional(subscripts |
                                (Optional(lower_indices) + Optional(upper_indices))
                                ) +
                       ZeroOrMore("'"))
        # Define a variable as a pyparsing result that contains one object name
        variable = Group(name("varname"))("variable")
        variable.setParseAction(self.variable_parse_action)

        # initialize recursive grammar
        expression = Forward()

        # Construct functions as consisting of funcname and arguments as
        # funcname(arguments)
        # where arguments is a comma-separated list of arguments, returned as a list
        # Must have at least 1 argument
        function = Group(name("funcname") +
                         Suppress("(") +
                         Group(delimitedList(expression))("arguments") +
                         Suppress(")")
                         )("function")
        function.setParseAction(self.function_parse_action)

        # Define parentheses
        parentheses = Group(Suppress("(") +
                            expression +
                            Suppress(")"))('parentheses')

        # Define arrays
        array = Group(Suppress("[") +
                      delimitedList(expression) +
                      Suppress("]"))("array")

        # atomic units evaluate directly to number or array without binary operations
        atom = number | function | variable | parentheses | array

        # Define operations in order of precedence
        # Define exponentiation, possibly including negative powers
        power = atom + ZeroOrMore(Suppress("^") + Optional(minus)("op") + atom)
        power.addParseAction(self.group_if_multiple('power'))

        # Define negation (e.g., in 5*-3 --> we need to evaluate the -3 first)
        # Negation in powers is handled separately
        # This has been arbitrarily assigned a higher precedence than parallel
        negation = Optional(minus)("op") + power
        negation.addParseAction(self.group_if_multiple('negation'))

        # Define the parallel operator 1 || 5 == 1/(1/1 + 1/5)
        pipes = Literal('|') + Literal('|')
        parallel = negation + ZeroOrMore(Suppress(pipes) + negation)
        parallel.addParseAction(self.group_if_multiple('parallel'))

        # Define multiplication and division
        product = parallel + ZeroOrMore((Literal('*') | Literal('/'))("op") + parallel)
        product.addParseAction(self.group_if_multiple('product'))

        # Define sums and differences
        # Note that leading - signs are treated by negation
        sumdiff = Optional(plus) + product + ZeroOrMore(plus_minus("op") + product)
        sumdiff.addParseAction(self.group_if_multiple('sum'))

        # Close the recursion
        expression << sumdiff

        return expression + stringEnd

    def raw_parse(self, expression):
        """
        Try to parse a string and cache the result. ALWAYS clears storage.
        """
        try:
            BracketValidator.validate(expression)
            tree = self.grammar.parseString(expression)[0]
            parsed = MathExpression(expression,
                                    tree,
                                    self.variables_used,
                                    self.functions_used,
                                    self.suffixes_used)
        except:
            raise
        finally:
            self.reset_storage()

        return parsed

    def parse(self, expression):
        """
        If expression is in parser cache, return cached result, otherwise
        delegate to raw_parse.
        """
        expression_no_whitespace = expression.replace(' ', '')
        cache_key = expression_no_whitespace
        if expression_no_whitespace in self.cache:
            return self.cache[cache_key]

        try:
            parsed = self.raw_parse(expression_no_whitespace)
        except ParseException:
            msg = "Invalid Input: Could not parse '{}' as a formula"
            raise UnableToParse(msg.format(expression))

        self.cache[cache_key] = parsed
        return parsed

EvalMetaData = namedtuple('EvalMetaData',
                          ['variables_used',
                           'functions_used',
                           'suffixes_used',
                           'max_array_dim_used'])
class MathExpression(object):
    """
    Holds the parse tree for mathematical expression; returned by MathParser.

    Attributes:
        - expression (str): the original string that generated this parse tree
        - variables_used (set)
        - functions_used (set)
        - suffixes_used (set)

    Methods:
        - eval(variables, functions, suffixes, allow_inf)

    EXAMPLE:
    ========
    >>> new_parser = MathParser()
    >>> expression = new_parser.parse('2^a + [x, 2]*[y, f(2, 3)] + 3%')
    >>> variables = { 'a': 2, 'x': 3, 'y': 4 }
    >>> functions = { 'f': lambda x, y: x**y }
    >>> suffixes = { '%': 0.01 }
    >>> result, meta = expression.eval(variables, functions, suffixes)
    >>> result
    32.03

    """

    def __init__(self, expression, tree, variables_used, functions_used, suffixes_used):
        self.expression = expression
        self.variables_used = variables_used
        self.functions_used = functions_used
        self.suffixes_used = suffixes_used
        self.tree = tree

    def __str__(self):
        return self.tree.asXML()

    def __repr__(self):
        return self.__str__()

    def check_scope(self, variables, functions, suffixes):
        """
        Confirm that all variables, functions, suffixes used in the tree are
        provided. Tries to provide helpful StudentFacingError if not.
        """
        bad_vars = set(var for var in self.variables_used if var not in variables)
        if bad_vars:
            message = "Invalid Input: '{}' not permitted in answer as a variable"
            varnames = "', '".join(sorted(bad_vars))

            # Check to see if there is a different case version of the variable
            caselist = set()
            for var2 in bad_vars:
                for var1 in variables:
                    if var1.lower() == var2.lower():
                        caselist.add(var1)
            if len(caselist) > 0:
                betternames = "', '".join(sorted(caselist))
                message += " (did you mean '" + betternames + "'?)"

            raise UndefinedVariable(message.format(varnames))

        bad_funcs = set(func for func in self.functions_used if func not in functions)
        if bad_funcs:
            funcnames = "', '".join(sorted(bad_funcs))
            message = "Invalid Input: '{}' not permitted in answer as a function"

            # Check to see if there is a corresponding variable name
            if any(func in variables for func in bad_funcs):
                message += " (did you forget to use * for multiplication?)"

            # Check to see if there is a different case version of the function
            caselist = set()
            for func2 in bad_funcs:
                for func1 in functions:
                    if func2.lower() == func1.lower():
                        caselist.add(func1)
            if len(caselist) > 0:
                betternames = "', '".join(sorted(caselist))
                message += " (did you mean '" + betternames + "'?)"

            raise UndefinedFunction(message.format(funcnames))

        bad_suffixes = set(suff for suff in self.suffixes_used if suff not in suffixes)
        if bad_suffixes:
            bad_suff_names = "', '".join(sorted(bad_suffixes))
            message = "Invalid Input: '{}' not permitted directly after a number"

            # Check to see if there is a corresponding variable name
            if any(suff in variables for suff in bad_suffixes):
                message += " (did you forget to use * for multiplication?)"

            # Check to see if there is a different case version of the suffix
            caselist = set()
            for suff2 in bad_suffixes:
                for suff1 in suffixes:
                    if suff2.lower() == suff1.lower():
                        caselist.add(suff1)
            if len(caselist) > 0:
                betternames = "', '".join(sorted(caselist))
                message += " (did you mean '" + betternames + "'?)"

            raise UndefinedFunction(message.format(bad_suff_names))

    def eval(self, variables, functions, suffixes, allow_inf=False):
        """
        Numerically evaluate a MathExpression's tree, returning a tuple of the
        numeric result and evaluation metadata.

        Also recasts some errors as CalcExceptions (which are student-facing).

        Arguments:
            variables (dict): maps variable names to values
            functions (dict): maps function names to values
            suffixes (dict): maps suffix names to values
            allow_inf (bool): If true, any node evaluating to inf will throw
                a CalcOverflowError

        See class-level docstring for example usage.
        """
        self.check_scope(variables, functions, suffixes)

        # metadata_dict['max_array_dim_used'] is updated by eval_array
        metadata_dict = {'max_array_dim_used': 0}
        actions = {
            'number': lambda parse_result: self.eval_number(parse_result, suffixes),
            'variable': lambda parse_result: self.eval_variable(parse_result, variables),
            'arguments': lambda tokens: tokens,
            'function': lambda parse_result: self.eval_function(parse_result, functions),
            'array': lambda parse_result: self.eval_array(parse_result, metadata_dict),
            'power': self.eval_power,
            'negation': self.eval_negation,
            'parallel': self.eval_parallel,
            'product': self.eval_product,
            'sum': self.eval_sum,
            'parentheses': lambda tokens: tokens[0]  # just get the unique child
        }

        # Find the value of the entire tree
        # Catch math errors that may arise
        try:
            result = self.eval_node(self.tree, actions, allow_inf)
            # set metadata after metadata_dict has been mutated
            metadata = EvalMetaData(variables_used=self.variables_used,
                                    functions_used=self.functions_used,
                                    suffixes_used=self.suffixes_used,
                                    max_array_dim_used=metadata_dict['max_array_dim_used'])
        except OverflowError:
            raise CalcOverflowError("Numerical overflow occurred. "
                                    "Does your input generate very large numbers?")
        except ZeroDivisionError:
            raise CalcZeroDivisionError("Division by zero occurred. "
                                        "Check your input's denominators.")

        return result, metadata

    # The following functions define evaluation actions, which are run on lists
    # of results from each parse component. They convert the strings and (previously
    # calculated) numbers into the number that component represents.

    @staticmethod
    def eval_node(node, actions, allow_inf):
        """
        Recursively evaluates a node, calling itself on the node's children.
        Delegates to one of the provided actions, passing evaluated child nodes as arguments.
        """

        if not isinstance(node, ParseResults):
            # We have a leaf, do not recurse. Return it directly.
            # Entry is either a (python) number or a string.
            return cast_np_numeric_as_builtin(node)

        node_name = node.getName()
        if node_name not in actions:  # pragma: no cover
            raise ValueError(u"Unknown branch name '{}'".format(node_name))

        evaluated_children = [MathExpression.eval_node(child, actions, allow_inf) for child in node]

        # Check for nan
        if any(np.isnan(item) for item in evaluated_children if isinstance(item, float)):
            return float('nan')

        # Compute the result of this node
        action = actions[node_name]
        result = action(evaluated_children)

        # All actions convert the input to a number, array, or list.
        # (Only self.actions['arguments'] returns a list.)
        as_list = result if isinstance(result, list) else [result]

        # Check if there were any infinities or nan
        if not allow_inf and any(np.any(np.isinf(r)) for r in as_list):
            raise CalcOverflowError("Numerical overflow occurred. Does your expression "
                                    "generate very large numbers?")
        if any(np.any(np.isnan(r)) for r in as_list):
            return float('nan')

        return cast_np_numeric_as_builtin(result, map_across_lists=True)

    @staticmethod
    def eval_number(parse_result, suffixes):
        """
        Create a float out of the input, applying a suffix if there is one

        Arguments:
            parse_result: A list, [string_number, suffix(optional)]

        Usage
        =====
        >>> MathExpression.eval_number(['7.13e3'], {})
        7130.0
        >>> MathExpression.eval_number(['5', '%'], {'%': 0.01})
        0.05
        """
        result = float(parse_result[0])
        if len(parse_result) == 2:
            result = result * suffixes[parse_result[1]]
        return result

    @staticmethod
    def eval_variable(parse_result, variables):
        """
        Returns a copy of the variable in self.vars

        We return a copy so that nothing in self.vars is mutated.
        
        If the variable is a long integer, we convert it to a float so that numpy methods work on it.

        NOTE: The variable's value's class must implement a __copy__ method.
            (numpy ndarrays do implement this method)
        """
        value = variables[parse_result[0]]
        value = copy.copy(value)
        if isinstance(value, long):
            value = float(value)
        return value

    @staticmethod
    def eval_function(parse_result, functions):
        """
        Evaluates a function

        Arguments:
            parse_result: ['funcname', arglist]

        Usage
        =====
        Instantiate a parser and some functions:
        >>> import numpy as np
        >>> functions = {"sin": np.sin, "cos": np.cos}

        Single variable functions work:
        >>> MathExpression.eval_function(['sin', [0]], functions)
        0.0
        >>> MathExpression.eval_function(['cos', [0]], functions)
        1.0

        So do multivariable functions:
        >>> def h(x, y): return x + y
        >>> MathExpression.eval_function(['h', [1, 2]], {"h": h})
        3

        Validation:
        ==============================
        By default, eval_function inspects its function's arguments to first
        validate that the correct number of arguments are passed:

        >>> def h(x, y): return x + y
        >>> try:
        ...     MathExpression.eval_function(['h', [1, 2, 3]], {"h": h})
        ... except ArgumentError as error:
        ...     print(error)
        Wrong number of arguments passed to h(...): Expected 2 inputs, but received 3.

        However, if the function to be evaluated has a truthy 'validated'
        property, we assume it does its own validation and we do not check the
        number of arguments.

        >>> from mitxgraders.exceptions import StudentFacingError
        >>> def g(*args):
        ...     if len(args) != 2:
        ...         raise StudentFacingError('I need two inputs!')
        ...     return args[0]*args[1]
        >>> g.validated = True
        >>> try:
        ...     MathExpression.eval_function(['g', [1]], {"g": g})
        ... except StudentFacingError as error:
        ...     print(error)
        I need two inputs!
        """
        # Obtain the function and arguments
        name, args = parse_result
        func = functions[name]

        # If function does not do its own validation, try and validate here.
        if not getattr(func, 'validated', False):
            MathExpression.validate_function_call(func, name, args)

        # Try to call the function
        try:
            return func(*args)
        except StudentFacingError:
            raise
        except ZeroDivisionError:
            # It would be really nice to tell student the symbolic argument as part of this message,
            # but making symbolic argument available would require some nontrivial restructing
            msg = ("There was an error evaluating {name}(...). "
                   "Its input does not seem to be in its domain.").format(name=name)
            raise CalcZeroDivisionError(msg)
        except OverflowError:
            msg = ("There was an error evaluating {name}(...). "
                   "(Numerical overflow).").format(name=name)
            raise CalcOverflowError(msg)
        except Exception: # pylint: disable=W0703
            # Don't know what this is, or how you want to deal with it
            # Call it a domain issue.
            msg = ("There was an error evaluating {name}(...). "
                   "Its input does not seem to be in its domain.").format(name=name)
            raise FunctionEvalError(msg)

    @staticmethod
    def validate_function_call(func, name, args):
        """
        Checks that func has been called with the correct number of arguments.
        """
        num_args = len(args)
        expected = get_number_of_args(func)
        if expected != num_args:
            msg = ("Wrong number of arguments passed to {func}(...): "
                   "Expected {num} inputs, but received {num2}.")
            raise ArgumentError(msg.format(func=name, num=expected, num2=num_args))
        return True

    @staticmethod
    def eval_array(parse_result, metadata_dict):
        """
        Takes in a list of evaluated expressions and returns it as a MathArray.
        May mutate metadata_dict.

        If passed a list of numpy arrays, generates a matrix/tensor/etc.

        Arguments:
            parse_result: A list containing each element of the array
            metadata_dict: A dictionary with key 'max_array_dim_used', whose
                value should be an integer. If the result of eval_array has higher
                dimension than 'max_array_dim_used', this value will be updated.

        Usage
        =====
        Returns MathArray instances and updates metadata_dict['max_array_dim_used']
        if needed:
        >>> metadata_dict = { 'max_array_dim_used': 0 }
        >>> MathExpression.eval_array([1, 2, 3], metadata_dict)
        MathArray([1, 2, 3])
        >>> metadata_dict['max_array_dim_used']
        1

        If metadata_dict['max_array_dim_used'] is larger than returned array value,
        then metadata_dict is not updated:
        >>> metadata_dict = { 'max_array_dim_used': 2 }
        >>> MathExpression.eval_array([1, 2, 3], metadata_dict)
        MathArray([1, 2, 3])
        >>> metadata_dict['max_array_dim_used']
        2

        >>> metadata_dict = { 'max_array_dim_used': 0 }
        >>> MathExpression.eval_array([         # doctest: +NORMALIZE_WHITESPACE
        ...     [1 , 2],
        ...     [3, 4]
        ... ], metadata_dict)
        MathArray([[1,  2],
                [3,  4]])

        In practice, this is called recursively:
        >>> metadata_dict = { 'max_array_dim_used': 0 }
        >>> MathExpression.eval_array([         # doctest: +NORMALIZE_WHITESPACE
        ...     MathExpression.eval_array([1, 2, 3], metadata_dict),
        ...     MathExpression.eval_array([4, 5, 6], metadata_dict)
        ... ], metadata_dict)
        MathArray([[1, 2, 3],
               [4, 5, 6]])
        >>> metadata_dict['max_array_dim_used']
        2

        One complex entry will convert everything to complex:
        >>> metadata_dict = { 'max_array_dim_used': 0 }
        >>> MathExpression.eval_array([         # doctest: +NORMALIZE_WHITESPACE
        ...     MathExpression.eval_array([1, 2j, 3], metadata_dict),
        ...     MathExpression.eval_array([4, 5, 6], metadata_dict)
        ... ], metadata_dict)
        MathArray([[ 1.+0.j,  0.+2.j,  3.+0.j],
               [ 4.+0.j,  5.+0.j,  6.+0.j]])

        We try to detect shape errors:
        >>> metadata_dict = { 'max_array_dim_used': 0 }
        >>> try:                                            # doctest: +ELLIPSIS
        ...     MathExpression.eval_array([
        ...         MathExpression.eval_array([1, 2, 3], metadata_dict),
        ...         4
        ...     ], metadata_dict)
        ... except UnableToParse as error:
        ...     print(error)
        Unable to parse vector/matrix. If you're trying ...
        >>> metadata_dict = { 'max_array_dim_used': 0 }
        >>> try:                                            # doctest: +ELLIPSIS
        ...     MathExpression.eval_array([
        ...         2.0,
        ...         MathExpression.eval_array([1, 2, 3], metadata_dict),
        ...         4
        ...     ], metadata_dict)
        ... except UnableToParse as error:
        ...     print(error)
        Unable to parse vector/matrix. If you're trying ...
        """
        shape_message = ("Unable to parse vector/matrix. If you're trying to "
                         "enter a matrix, this is most likely caused by an "
                         "unequal number of elements in each row.")

        try:
            array = MathArray(parse_result)
        except ValueError:
            # This happens, for example, with np.array([1, 2, [3]])
            # when using numpy version 1.6
            raise UnableToParse(shape_message)

        if array.dtype == 'object':
            # This happens, for example, with np.array([[1], 2, 3]),
            # OR with with np.array([1, 2, [3]]) in recent versions of numpy
            raise UnableToParse(shape_message)

        if array.ndim > metadata_dict['max_array_dim_used']:
            metadata_dict['max_array_dim_used'] = array.ndim

        return array

    @staticmethod
    def eval_power(parse_result):
        """
        Exponentiate a list of numbers, right to left. Can also have minus signs
        interspersed, which means to flip the sign of the exponent.

        Arguments:
            parse_result: A list of numbers and "-" strings, to be read as exponentiated
            [a, b, c, d] = a^b^c^d
            [a, "-", c, d] = a^(-(c^d))

        Usage
        =====
        >>> MathExpression.eval_power([4,3,2])  # Evaluate 4^3^2
        262144
        >>> MathExpression.eval_power([2,"-",2,2])  # Evaluate 2^(-(2^2))
        0.0625
        """

        data = parse_result[:]
        result = data.pop()
        while data:
            # Result contains the current exponent
            working = data.pop()
            if isinstance(working, six.text_type) and working == "-":
                result = -result
            else:
                # working is base, result is exponent
                result = robust_pow(working, result)

        return result

    @staticmethod
    def eval_negation(parse_result):
        """
        Negate a number an appropriate number of times.

        Arguments:
            parse_result: A list containing zero or more "-" strings, followed by a number.
            ["-", "-", "-", a] = -a
            ["-", "-", a] = a

        Usage
        =====
        >>> MathExpression.eval_negation([2])
        2
        >>> MathExpression.eval_negation(["-",2])
        -2
        >>> MathExpression.eval_negation(["-","-",2])
        2
        >>> MathExpression.eval_negation(["-","-","-",2])
        -2
        >>> MathExpression.eval_negation(["-","-","-","-",2])
        2
        """
        num = parse_result[-1]
        return num * (-1)**(len(parse_result) - 1)

    @staticmethod
    def eval_parallel(parse_result):
        """
        Operator associated with parallel resistors (it's commutative).

        Return 0 if there is a zero among the inputs.

        Arguments:
            parse_result: A list of numbers to combine appropriately
            [a, b, c, d] = 1/(1/a + 1/b + 1/c + 1/d)

        Usage
        =====
        >>> MathExpression.eval_parallel([4,3,2])  # doctest: +ELLIPSIS
        0.9230769...
        >>> MathExpression.eval_parallel([1,2])  # doctest: +ELLIPSIS
        0.6666666...
        >>> MathExpression.eval_parallel([1,1])
        0.5
        >>> MathExpression.eval_parallel([1,0])
        0
        """
        if 0 in parse_result:
            return 0
        reciprocals = [1. / num for num in parse_result]
        return 1. / sum(reciprocals)

    @staticmethod
    def eval_product(parse_result):
        """
        Multiply/divide inputs appropriately

        Arguments:
            parse_result: A list of numbers to combine, separated by "*" and "/"
            [a, "*", b, "/", c] = a*b/c

        Has some extra logic to avoid ambiguous vector triple products.
        See https://github.com/mitodl/mitx-grading-library/issues/108

        Usage
        =====
        >>> MathExpression.eval_product([2,"*",3,"/",4])
        1.5
        >>> try:
        ...     MathExpression.eval_product([2,"*",3,"+",4])
        ... except CalcError as error:
        ...     print(error)
        Unexpected symbol + in eval_product
        """
        double_vector_mult_has_occured = False
        triple_vector_mult_error = CalcError(
            "Multiplying three or more vectors is ambiguous. "
            "Please place parentheses around vector multiplications."
            )

        result = parse_result[0]
        data = parse_result[1:]
        while data:
            op = data.pop(0)
            value = data.pop(0)
            if op == '/':
                # Don't use in-place ops, it conflicts with numpy version 1.16
                # 'same-type' casting
                result = result/value
            elif op == '*':
                if is_vector(value):
                    if double_vector_mult_has_occured:
                        raise triple_vector_mult_error
                    elif is_vector(result):
                        double_vector_mult_has_occured = True
                result = result*value
            else:
                raise CalcError("Unexpected symbol {} in eval_product".format(op))

            # Need to cast np numerics as builtins here (in addition to during
            # eval_node) because the result is changing shape
            result = cast_np_numeric_as_builtin(result)

        return result

    @staticmethod
    def eval_sum(parse_result):
        """
        Add/subtract inputs

        Arguments:
            parse_result: A list of numbers to combine, separated by "+" and "-",
            possibly with a leading "+" (a leading "-" will have been eaten by negation)

        Usage
        =====
        >>> MathExpression.eval_sum([2,"+",3,"-",4])
        1
        >>> MathExpression.eval_sum(["+",2,"+",3,"-",4])
        1
        >>> try:
        ...     MathExpression.eval_sum(["+",2,"*",3,"-",4])
        ... except CalcError as error:
        ...     print(error)
        Unexpected symbol * in eval_sum
        """
        data = parse_result[:]
        result = data.pop(0)
        if isinstance(result, six.text_type) and result == "+":
            result = data.pop(0)
        while data:
            op = data.pop(0)
            num = data.pop(0)
            if op == '+':
                result = result + num
            elif op == '-':
                result = result - num
            else:
                raise CalcError("Unexpected symbol {} in eval_sum".format(op))
        return result

PARSER = MathParser()

def parse(formula):
    """
    Parse a mathematical string into a MathExpression object. Useful for later
    evaluation or for accessing variables the variables/functions/suffixes used.
    """
    return PARSER.parse(formula)

def evaluator(formula,
              variables=DEFAULT_VARIABLES,
              functions=DEFAULT_FUNCTIONS,
              suffixes=DEFAULT_SUFFIXES,
              max_array_dim=None,
              allow_inf=False):
    """
    Evaluate an expression; that is, take a string of math and return a float.

    Arguments
    =========
    - formula (str): The formula to be evaluated
    Pass a scope consisting of variables, functions, and suffixes:
    - variables (dict): maps strings to variable values, defaults to DEFAULT_VARIABLES
    - functions (dict): maps strings to functions, defaults to DEFAULT_FUNCTIONS
    - suffixes (dict): maps strings to suffix values, defaults to DEFAULT_SUFFIXES
    Also:
    - max_array_dim: Maximum dimension of MathArrays
    - allow_inf: Whether to raise an error if the evaluator encounters an infinity

    NOTE: Everything is case sensitive (this is different to edX!)

    Usage
    =====
    Evaluates the formula and records usage of functions/variables/suffixes:
    >>> result = evaluator("1+1", {}, {}, {})
    >>> expected = ( 2.0 , EvalMetaData(
    ...     variables_used=set(),
    ...     functions_used=set(),
    ...     suffixes_used=set(),
    ...     max_array_dim_used=0
    ... ))
    >>> result == expected
    True
    >>> result = evaluator("square(x) + 5k",
    ...     variables={'x':5, 'y': 10},
    ...     functions={'square': lambda x: x**2, 'cube': lambda x: x**3},
    ...     suffixes={'%': 0.01, 'k': 1000  })
    >>> expected = ( 5025.0 , EvalMetaData(
    ...     variables_used=set(['x']),
    ...     functions_used=set(['square']),
    ...     suffixes_used=set(['k']),
    ...     max_array_dim_used=0
    ... ))
    >>> result == expected
    True

    Empty submissions evaluate to nan:
    >>> evaluator("")[0]
    nan

    Submissions that generate infinities will raise an error:
    >>> try:                                                # doctest: +ELLIPSIS
    ...     evaluator("inf", variables={'inf': float('inf')})[0]
    ... except CalcOverflowError as error:
    ...     print(error)
    Numerical overflow occurred. Does your expression generate ...

    Unless you specify that infinity is ok:
    >>> evaluator("inf", variables={'inf': float('inf')}, allow_inf=True)[0]
    inf
    """

    empty_usage = EvalMetaData(variables_used=set(),
                               functions_used=set(),
                               suffixes_used=set(),
                               max_array_dim_used=0)
    if formula is None:
        # No need to go further.
        return float('nan'), empty_usage
    formula = formula.strip()
    if formula == "":
        # No need to go further.
        return float('nan'), empty_usage

    parsed = parse(formula)
    result, eval_metadata = parsed.eval(variables, functions, suffixes, allow_inf=allow_inf)

    # Were vectors/matrices/tensors used when they shouldn't have been?
    if max_array_dim is not None and eval_metadata.max_array_dim_used > max_array_dim:
        if max_array_dim == 0:
            msg = "Vector and matrix expressions have been forbidden in this entry."
        elif max_array_dim == 1:
            msg = "Matrix expressions have been forbidden in this entry."
        else:
            msg = "Tensor expressions have been forbidden in this entry."
        raise UnableToParse(msg)

    # Return the result of the evaluation, as well as the set of functions used
    return result, eval_metadata
