"""
calc.py

Parser and evaluator for mathematical expressions.

Uses pyparsing to parse. Main function is evaluator().

Heavily modified from the edX calc.py
"""
from __future__ import division
import copy
from collections import namedtuple
import numpy as np
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
    >>> expr = '1 + ( ( x + 1 )^2 + ( + [2'
    >>> BV.validate(expr)                           # doctest: +NORMALIZE_WHITESPACE
    Traceback (most recent call last):
    UnbalancedBrackets: Invalid Input: 2 parentheses and 1 square brackets were
    opened without being closed, highlighted below.
    <code>1 + <mark>(</mark> ( x + 1 )^2 + <mark>(</mark> + <mark>[</mark>2</code>

    NOTE: This class only contains class variables and static methods.
    It could just as well be a separate file/module.
    """

    # Stores bracket metadata
    Bracket = namedtuple('Bracket', ['char', 'partner', 'is_closer', 'name'])

    # The brackets that we care about
    bracket_registry = {
        '(': Bracket(char='(', partner=')', is_closer=False, name='parenthesis'),
        ')': Bracket(char=')', partner='(', is_closer=True, name='parenthesis'),
        '[': Bracket(char='[', partner=']', is_closer=False, name='square bracket'),
        ']': Bracket(char=']', partner='[', is_closer=True, name='square bracket')
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
        p_count = sum([entry.bracket.char == '(' for entry in stack])
        b_count = sum([entry.bracket.char == '[' for entry in stack])

        if p_count and b_count:
            msg = ("Invalid Input: {p_count} parentheses and {b_count} "
                   "square brackets were opened without being closed, "
                   "highlighted below.\n{highlight}")
        elif p_count:
            msg = ("Invalid Input: {p_count} parentheses were opened without "
                   "being closed, highlighted below.\n{highlight}")
        else:
            msg = ("Invalid Input: {b_count} square brackets were opened "
                   "without being closed, highlighted below.\n{highlight}")

        indices = [entry.index for entry in stack]
        highlight = BracketValidator.highlight_formula(formula, indices)
        formatted = msg.format(p_count=p_count, b_count=b_count, highlight=highlight)
        raise UnbalancedBrackets(formatted)

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

class ParserCache(object):
    """Stores the parser trees for formula strings for reuse"""

    def __init__(self):
        """Initializes the cache"""
        self.cache = {}

    def get_parser(self, formula, suffixes):
        """Get a FormulaParser object for a given formula"""
        # Check the formula for matching parentheses
        BracketValidator.validate(formula)

        # Strip out any whitespace, so that two otherwise-equivalent formulas are treated
        # the same
        stripformula = formula.replace(" ", "")

        # Construct the key
        suffixstr = ""
        for key in suffixes:
            suffixstr += key
        key = (stripformula, ''.join(sorted(suffixstr)))

        # Check if it's in the cache
        parser = self.cache.get(key, None)
        if parser is not None:
            return parser

        # It's not, so construct it
        parser = FormulaParser(stripformula, suffixes)
        try:
            parser.parse_algebra()
        except ParseException:
            msg = "Invalid Input: Could not parse '{}' as a formula"
            raise UnableToParse(msg.format(formula))

        # Save it for later use before returning it
        self.cache[key] = parser
        return parser

# The global parser cache
parsercache = ParserCache()

ScopeUsage = namedtuple('ScopeUSage', ['variables', 'functions', 'suffixes'])

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
    >>> expected = ( 2.0 , ScopeUsage(
    ...     variables=set(),
    ...     functions=set(),
    ...     suffixes=set()
    ... ))
    >>> result == expected
    True
    >>> result = evaluator("square(x) + 5k",
    ...     variables={'x':5, 'y': 10},
    ...     functions={'square': lambda x: x**2, 'cube': lambda x: x**3},
    ...     suffixes={'%': 0.01, 'k': 1000  })
    >>> expected = ( 5025.0 , ScopeUsage(
    ...     variables=set(['x']),
    ...     functions=set(['square']),
    ...     suffixes=set(['k'])
    ... ))
    >>> result == expected
    True

    Empty submissions evaluate to nan:
    >>> evaluator("")[0]
    nan

    Submissions that generate infinities will raise an error:
    >>> evaluator("inf", variables={'inf': float('inf')})[0]  # doctest: +ELLIPSIS
    Traceback (most recent call last):
    CalcOverflowError: Numerical overflow occurred. Does your expression generate ...

    Unless you specify that infinity is ok:
    >>> evaluator("inf", variables={'inf': float('inf')}, allow_inf=True)[0]
    inf
    """

    empty_usage = ScopeUsage(set(), set(), set())
    if formula is None:
        # No need to go further.
        return float('nan'), empty_usage
    formula = formula.strip()
    if formula == "":
        # No need to go further.
        return float('nan'), empty_usage

    # Parse the tree
    math_interpreter = parsercache.get_parser(formula, suffixes)

    # Set the variables and functions
    math_interpreter.set_vars_funcs(variables, functions)

    # Check the variables and functions
    math_interpreter.check_variables()

    # Perform the evaluation
    result = math_interpreter.evaluate(allow_inf)

    # Were vectors/matrices/tensors used when they shouldn't have been?
    if max_array_dim is not None and math_interpreter.max_array_dim_used > max_array_dim:
        if max_array_dim == 0:
            msg = "Vector and matrix expressions have been forbidden in this entry."
        elif max_array_dim == 1:
            msg = "Matrix expressions have been forbidden in this entry."
        else:
            msg = "Tensor expressions have been forbidden in this entry."
        raise UnableToParse(msg)

    # Return the result of the evaluation, as well as the set of functions used
    usage = ScopeUsage(variables=math_interpreter.variables_used,
                       functions=math_interpreter.functions_used,
                       suffixes=math_interpreter.suffixes_used)
    return result, usage

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
    >>> [type(cast_np_numeric_as_builtin(example)) for example in examples]
    [<type 'float'>, <type 'float'>, <type 'int'>, <type 'int'>, <type 'complex'>, <type 'complex'>]

    Leaves MathArrays alone:
    >>> from mitxgraders.helpers.calc.math_array import MathArray
    >>> A = MathArray([1, 2, 3])
    >>> cast_np_numeric_as_builtin(A)
    MathArray([1, 2, 3])

    Optionally, map across a list:
    >>> target = [np.float64(1.0), np.float64(2.0)]
    >>> result = cast_np_numeric_as_builtin(target, map_across_lists=True)
    >>> [type(item) for item in result]
    [<type 'float'>, <type 'float'>]

    """
    if isinstance(obj, np.number):
        return np.asscalar(obj)
    if map_across_lists and isinstance(obj, list):
        return [np.asscalar(item) if isinstance(item, np.number) else item
                for item in obj]
    return obj

class FormulaParser(object):
    """
    Parses a mathematical expression into a tree that can subsequently be evaluated
    against given dictionaries of variables and functions.
    """
    def __init__(self, math_expr, suffixes):
        """
        Create the ParseAugmenter for a given math expression string.

        Do the parsing later, when called like `OBJ.parse_algebra()`.
        """
        self.math_expr = math_expr
        self.tree = None
        self.variables_used = set()
        self.functions_used = set()
        self.suffixes_used = set()
        self.max_array_dim_used = 0
        self.suffixes = suffixes
        self.actions = {
            'number': self.eval_number,
            'variable': self.eval_variable,
            'arguments': lambda tokens: tokens,
            'function': self.eval_function,
            'array': self.eval_array,
            'power': self.eval_power,
            'negation': self.eval_negation,
            'parallel': self.eval_parallel,
            'product': self.eval_product,
            'sum': self.eval_sum,
            'parentheses': lambda tokens: tokens[0]  # just get the unique child
        }
        self.vars = {}
        self.functions = {}

    def variable_parse_action(self, tokens):
        """
        When a variable is recognized, store it in `variables_used`.
        """
        self.variables_used.add(tokens[0][0])

    def function_parse_action(self, tokens):
        """
        When a function is recognized, store it in `functions_used`.
        """
        self.functions_used.add(tokens[0][0])

    def suffix_parse_action(self, tokens):
        """
        When a suffix is recognized, store it in `suffixes_used`.
        """
        self.suffixes_used.add(tokens[0][0])

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

    def parse_algebra(self):
        """
        Parse an algebraic expression into a tree.

        Store a `pyparsing.ParseResult` in `self.tree` with proper groupings to
        reflect parenthesis and order of operations. Leave all operators in the
        tree and do not parse any strings of numbers into their float versions.

        To visualize the tree for debugging purposes, use
            FormulaParser.dump_parse_result(parse_result)
        """
        # Define + and -
        plus = Literal("+")
        minus = Literal("-")
        plus_minus = plus | minus

        # 1 or 1.0 or .1
        number_part = Word(nums)
        inner_number = Combine((number_part + Optional("." + Optional(number_part)))
                               |
                               ("." + number_part))
        # Combine() joints the matching parts together in a single token,
        # and requires that the matching parts be contiguous

        # Define our suffixes
        suffix = MatchFirst(Literal(k) for k in self.suffixes.keys())
        suffix.setParseAction(self.suffix_parse_action)

        # Construct a number as a group consisting of a text string (num) and an optional
        # suffix num can include a decimal number and numerical exponent, and can be
        # converted to a number using float()
        # suffix is the suffix string that matches one of our suffixes
        # Spaces are ignored inside numbers
        # Group wraps everything up into its own ParseResults object when parsing
        number = Group(
            Combine(
                inner_number +
                Optional(CaselessLiteral("E") + Optional(plus_minus) + number_part),
                adjacent=False
            )("num")
            + Optional(suffix)("suffix")
        )("number")
        # Note that calling ("name") on the end of a parser is equivalent to calling
        # parser.setResultsName, which is used to pulling that result out of a parsed
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
        #       Of form "_{(-)<alaphnumeric>}"
        #   upper_indices (optional):
        #       Of form "^{(-)<alaphnumeric>}"
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

        # Predefine recursive variable expr
        expr = Forward()

        # Construct functions as consisting of funcname and arguments as
        # funcname(arguments)
        # where arguments is a comma-separated list of arguments, returned as a list
        # Must have at least 1 argument
        function = Group(name("funcname") +
                         Suppress("(") +
                         Group(delimitedList(expr))("arguments") +
                         Suppress(")")
                         )("function")
        function.setParseAction(self.function_parse_action)

        # Define parentheses
        parentheses = Group(Suppress("(") +
                            expr +
                            Suppress(")"))('parentheses')

        # Define arrays
        array = Group(Suppress("[") +
                      delimitedList(expr) +
                      Suppress("]"))("array")

        # Define an atomic unit as an expression that evaluates directly to a number
        # without the use of binary operations (assuming all children have been evaluated).
        atom = number | function | variable | parentheses | array

        # The following are in order of operational precedence
        # Define exponentiation, possibly including negative powers
        power = atom + ZeroOrMore(Suppress("^") + Optional(minus)("op") + atom)
        power.addParseAction(self.group_if_multiple('power'))

        # Define negation (eg, in 5*-3 --> we need to evaluate the -3 first)
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
        expr << sumdiff

        # Save the resulting tree
        self.tree = (expr + stringEnd).parseString(self.math_expr)[0]

    def dump_parse_result(self):  # pragma: no cover
        """Pretty-print an XML version of the parse_result for debug purposes"""
        print(self.tree.asXML())

    def set_vars_funcs(self, variables=None, functions=None):
        """Stores the given dictionaries of variables and functions for future use"""
        self.vars = variables if variables else {}
        self.functions = functions if functions else {}

    def evaluate(self, allow_inf):
        """
        Recursively evaluate `self.tree` and return the result.
        """
        def handle_node(node):
            """
            Return the result representing the node, using recursion.

            Call the appropriate action from self.actions for this node. As its inputs,
            feed it the output of `handle_node` for each child node.
            """
            if not isinstance(node, ParseResults):
                # Entry is either a (python) number or a string.
                # Return it directly to the next level up.
                return cast_np_numeric_as_builtin(node)

            node_name = node.getName()
            if node_name not in self.actions:  # pragma: no cover
                raise Exception(u"Unknown branch name '{}'".format(node_name))

            action = self.actions[node_name]
            handled_kids = [handle_node(k) for k in node]

            # Check for nan
            if any(np.isnan(item) for item in handled_kids if isinstance(item, float)):
                return float('nan')

            # Compute the result of this node
            result = action(handled_kids)

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

        # Find the value of the entire tree
        # Catch math errors that may arise
        try:
            result = handle_node(self.tree)
        except OverflowError:
            raise CalcOverflowError("Numerical overflow occurred. "
                                    "Does your input generate very large numbers?")
        except ZeroDivisionError:
            raise CalcZeroDivisionError("Division by zero occurred. "
                                        "Check your input's denominators.")

        return result

    def check_variables(self):
        """
        Confirm that all the variables and functions used in the tree are defined.
        """
        bad_vars = set(var for var in self.variables_used
                       if var not in self.vars)
        if bad_vars:
            message = "Invalid Input: {} not permitted in answer as a variable"
            varnames = ", ".join(sorted(bad_vars))

            # Check to see if there is a different case version of the variable
            caselist = set()
            for var2 in bad_vars:
                for var1 in self.vars:
                    if var1.lower() == var2.lower():
                        caselist.add(var1)
            if len(caselist) > 0:
                betternames = ', '.join(sorted(caselist))
                message += " (did you mean " + betternames + "?)"

            raise UndefinedVariable(message.format(varnames))

        bad_funcs = set(func for func in self.functions_used
                        if func not in self.functions)
        if bad_funcs:
            funcnames = ', '.join(sorted(bad_funcs))
            message = "Invalid Input: {} not permitted in answer as a function"

            # Check to see if there is a corresponding variable name
            if any(func in self.vars for func in bad_funcs):
                message += " (did you forget to use * for multiplication?)"

            # Check to see if there is a different case version of the function
            caselist = set()
            for func2 in bad_funcs:
                for func1 in self.functions:
                    if func2.lower() == func1.lower():
                        caselist.add(func1)
            if len(caselist) > 0:
                betternames = ', '.join(sorted(caselist))
                message += " (did you mean " + betternames + "?)"

            raise UndefinedFunction(message.format(funcnames))

    # The following functions define evaluation actions, which are run on lists
    # of results from each parse component. They convert the strings and (previously
    # calculated) numbers into the number that component represents.

    def eval_number(self, parse_result):
        """
        Create a float out of the input, applying a suffix if there is one

        Arguments:
            parse_result: A list, [string_number, suffix(optional)]

        Usage
        =====
        >>> parser = FormulaParser("1", {"%": 0.01})
        >>> parser.eval_number(['7.13e3'])
        7130.0
        >>> parser.eval_number(['5', '%'])
        0.05
        """
        result = float(parse_result[0])
        if len(parse_result) == 2:
            result *= self.suffixes[parse_result[1]]
        return result

    def eval_variable(self, parse_result):
        """
        Returns a copy of the variable in self.vars

        We return a copy so that nothing in self.vars is mutated.

        NOTE: The variable's class must implement a __copy__ method.
            (numpy ndarrays do implement this method)
        """
        variable = self.vars[parse_result[0]]
        return copy.copy(variable)

    def eval_function(self, parse_result):
        """
        Evaluates a function

        Arguments:
            parse_result: ['funcname', arglist]

        Usage
        =====
        Instantiate a parser and some functions:
        >>> import math
        >>> parser = FormulaParser("1", {})
        >>> parser.set_vars_funcs(functions={"sin": math.sin, "cos": math.cos})

        Single variable functions work:
        >>> parser.eval_function(['sin', [0]])
        0.0
        >>> parser.eval_function(['cos', [0]])
        1.0

        So do multivariable functions:
        >>> def h(x, y): return x + y
        >>> parser.set_vars_funcs(functions={"h": h})
        >>> parser.eval_function(['h', [1, 2]])
        3

        Validation:
        ==============================
        By default, eval_function inspects its function's arguments to first
        validate that the correct number of arguments are passed:

        >>> def h(x, y): return x + y
        >>> parser.set_vars_funcs(functions={"h": h})
        >>> parser.eval_function(['h', [1, 2, 3]])
        Traceback (most recent call last):
        ArgumentError: Wrong number of arguments passed to h. Expected 2, received 3.

        However, if the function to be evaluated has a truthy 'validated'
        property, we assume it does its own validation and we do not check the
        number of arguments.

        >>> from mitxgraders.exceptions import StudentFacingError
        >>> def g(*args):
        ...     if len(args) != 2:
        ...         raise StudentFacingError('I need two inputs!')
        ...     return args[0]*args[1]
        >>> g.validated = True
        >>> parser.set_vars_funcs(functions={"g": g})
        >>> parser.eval_function(['g', [1]])
        Traceback (most recent call last):
        StudentFacingError: I need two inputs!
        """
        # Obtain the function and arguments
        name, args = parse_result
        func = self.functions[name]

        # If function does not do its own validation, try and validate here.
        if not getattr(func, 'validated', False):
            FormulaParser.validate_function_call(func, name, args)

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
        except Exception as err:  # pylint: disable=W0703
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
            msg = ("Wrong number of arguments passed to {func}. "
                   "Expected {num}, received {num2}.")
            raise ArgumentError(msg.format(func=name, num=expected, num2=num_args))
        return True

    def eval_array(self, parse_result):
        """
        Takes in a list of evaluated expressions and returns it as a MathArray.

        If passed a list of numpy arrays, generates a matrix/tensor/etc.

        Arguments:
            parse_result: A list containing each element of the array

        Usage
        =====
        Returns MathArray instances:
        >>> parser = FormulaParser("1", {}) # fake parser instance
        >>> parser.eval_array([1, 2, 3])
        MathArray([1, 2, 3])
        >>> parser.eval_array([
        ...     [1, 2],
        ...     [3, 4]
        ... ])
        MathArray([[1, 2],
               [3, 4]])

        In practice, this is called recursively:
        >>> parser.eval_array([
        ...     parser.eval_array([1, 2, 3]),
        ...     parser.eval_array([4, 5, 6])
        ... ])
        MathArray([[1, 2, 3],
               [4, 5, 6]])

        One complex entry will convert everything to complex:
        >>> parser.eval_array([
        ...     parser.eval_array([1, 2j, 3]),
        ...     parser.eval_array([4, 5, 6])
        ... ])
        MathArray([[ 1.+0.j,  0.+2.j,  3.+0.j],
               [ 4.+0.j,  5.+0.j,  6.+0.j]])

        We try to detect shape errors:
        >>> parser.eval_array([                      # doctest: +ELLIPSIS
        ...     parser.eval_array([1, 2, 3]),
        ...     4
        ... ])
        Traceback (most recent call last):
        UnableToParse: Unable to parse vector/matrix. If you're trying ...
        >>> parser.eval_array([                      # doctest: +ELLIPSIS
        ...     2.0,
        ...     parser.eval_array([1, 2, 3]),
        ...     4
        ... ])
        Traceback (most recent call last):
        UnableToParse: Unable to parse vector/matrix. If you're trying ...
        """

        shape_message = ("Unable to parse vector/matrix. If you're trying to "
                         "enter a matrix, this is most likely caused by an "
                         "unequal number of elements in each row.")

        try:
            array = MathArray(parse_result)
        except ValueError:
            # This happens, for example, with np.array([1, 2, [3]])
            raise UnableToParse(shape_message)

        if array.dtype == 'object':
            # This happens, for example, with np.array([[1], 2, 3])
            raise UnableToParse(shape_message)

        if array.ndim > self.max_array_dim_used:
            self.max_array_dim_used = array.ndim

        return array

    def eval_power(self, parse_result):
        """
        Take a list of numbers and exponentiate them, right to left.

        Can also have minus signs interspersed, which means to flip the sign of the
        exponent.

        Arguments:
            parse_result: A list of numbers and "-" strings, to be read as exponentiated
            [a, b, c, d] = a^b^c^d
            [a, "-", c, d] = a^(-(c^d))

        Usage
        =====
        >>> parser = FormulaParser("1", {"%": 0.01})
        >>> parser.eval_power([4,3,2])  # Evaluate 4^3^2
        262144
        >>> parser.eval_power([2,"-",2,2])  # Evaluate 2^(-(2^2))
        0.0625
        """

        data = parse_result[:]
        result = data.pop()
        while data:
            # Result contains the current exponent
            working = data.pop()
            if working == "-":
                result = -result
            else:
                # working is base, result is exponent
                result = robust_pow(working, result)

        return result

    def eval_negation(self, parse_result):
        """
        Negate a number an appropriate number of times.

        Arguments:
            parse_result: A list containing zero or more "-" strings, followed by a number.
            ["-", "-", "-", a] = -a
            ["-", "-", a] = a

        Usage
        =====
        >>> parser = FormulaParser("1", {"%": 0.01})
        >>> parser.eval_negation([2])
        2
        >>> parser.eval_negation(["-",2])
        -2
        >>> parser.eval_negation(["-","-",2])
        2
        >>> parser.eval_negation(["-","-","-",2])
        -2
        >>> parser.eval_negation(["-","-","-","-",2])
        2
        """
        num = parse_result[-1]
        return num * (-1)**(len(parse_result) - 1)

    def eval_parallel(self, parse_result):
        """
        Compute numbers according to the parallel resistors operator (note commutative).

        Return NaN if there is a zero among the inputs.

        Arguments:
            parse_result: A list of numbers to combine appropriately
            [a, b, c, d] = 1/(1/a + 1/b + 1/c + 1/d)

        Usage
        =====
        >>> parser = FormulaParser("1", {"%": 0.01})
        >>> parser.eval_parallel([4,3,2])  # doctest: +ELLIPSIS
        0.9230769...
        >>> parser.eval_parallel([1,2])  # doctest: +ELLIPSIS
        0.6666666...
        >>> parser.eval_parallel([1,1])
        0.5
        >>> parser.eval_parallel([1,0])
        nan
        """
        if 0 in parse_result:
            return float('nan')
        reciprocals = [1. / num for num in parse_result]
        return 1. / sum(reciprocals)

    def eval_product(self, parse_result):
        """
        Multiply/divide inputs appropriately

        Arguments:
            parse_result: A list of numbers to combine, separated by "*" and "/"
            [a, "*", b, "/", c] = a*b/c

        Has some extra logic to avoid ambiguous vector tirple products.
        See https://github.com/mitodl/mitx-grading-library/issues/108

        Usage
        =====
        >>> parser = FormulaParser("1", {"%": 0.01})
        >>> parser.eval_product([2,"*",3,"/",4])
        1.5
        >>> parser.eval_product([2,"*",3,"+",4])
        Traceback (most recent call last):
        CalcError: Unexpected symbol + in eval_product
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
                result /= value
            elif op == '*':
                if is_vector(value):
                    if double_vector_mult_has_occured:
                        raise triple_vector_mult_error
                    elif is_vector(result):
                        double_vector_mult_has_occured = True
                result *= value
            else:
                raise CalcError("Unexpected symbol {} in eval_product".format(op))

            # Need to cast np numerics as builtins here (in addition to during
            # handle_node) because the result is changing shape
            result = cast_np_numeric_as_builtin(result)

        return result

    def eval_sum(self, parse_result):
        """
        Add/subtract inputs

        Arguments:
            parse_result: A list of numbers to combine, separated by "+" and "-",
            possibly with a leading "+" (a leading "-" will have been eaten by negation)

        Usage
        =====
        >>> parser = FormulaParser("1", {"%": 0.01})
        >>> parser.eval_sum([2,"+",3,"-",4])
        1
        >>> parser.eval_sum(["+",2,"+",3,"-",4])
        1
        >>> parser.eval_sum(["+",2,"*",3,"-",4])
        Traceback (most recent call last):
        CalcError: Unexpected symbol * in eval_sum
        """
        data = parse_result[:]
        result = data.pop(0)
        if result == "+":
            result = data.pop(0)
        while data:
            op = data.pop(0)
            num = data.pop(0)
            if op == '+':
                result += num
            elif op == '-':
                result -= num
            else:
                raise CalcError("Unexpected symbol {} in eval_sum".format(op))
        return result
