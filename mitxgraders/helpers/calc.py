"""
calc.py

Parser and evaluator for mathematical expressions.

Uses pyparsing to parse. Main function is evaluator().

Heavily modified from the edX calc.py
"""
from __future__ import division
from numbers import Number
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
from mitxgraders.baseclasses import StudentFacingError
from mitxgraders.helpers.validatorfuncs import get_number_of_args
from mitxgraders.helpers.mathfunc import (DEFAULT_FUNCTIONS,
                                          DEFAULT_SUFFIXES,
                                          DEFAULT_VARIABLES,
                                          robust_pow)
from mitxgraders.helpers.math_array import MathArray

class CalcError(StudentFacingError):
    """Base class for errors originating in calc.py"""
    pass

class UndefinedVariable(CalcError):
    """
    Indicate when a student inputs a variable which was not expected.
    """
    pass

class UndefinedFunction(CalcError):
    """
    Indicate when a student inputs a function which was not expected.
    """
    pass

class UnmatchedParentheses(CalcError):
    """
    Indicate when a student's input has unmatched parentheses.
    """
    pass

class FactorialError(CalcError):
    """
    Indicate when factorial is called on a bad input
    """
    pass

class CalcZeroDivisionError(CalcError):
    """
    Indicates division by zero
    """

class CalcOverflowError(CalcError):
    """
    Indicates numerical overflow
    """

class FunctionEvalError(CalcError):
    """
    Indicates that something has gone wrong during function evaluation.
    """

class UnableToParse(CalcError):
    """
    Indicate when an expression cannot be parsed
    """
    pass

class ArgumentError(CalcError):
    """
    Raised when the wrong number of arguments is passed to a function
    """
    pass


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

class ParserCache(object):
    """Stores the parser trees for formula strings for reuse"""

    def __init__(self):
        """Initializes the cache"""
        self.cache = {}

    def get_parser(self, formula, suffixes):
        """Get a FormulaParser object for a given formula"""
        # Check the formula for matching parentheses
        count = 0
        delta = {
            '(': +1,
            ')': -1
        }
        for index, char in enumerate(formula):
            if char in delta:
                count += delta[char]
                if count < 0:
                    msg = "Invalid Input: A closing parenthesis was found after segment " + \
                          "{}, but there is no matching opening parenthesis before it."
                    raise UnmatchedParentheses(msg.format(formula[0:index]))
        if count > 0:
            msg = "Invalid Input: Parentheses are unmatched. " + \
                  "{} parentheses were opened but never closed."
            raise UnmatchedParentheses(msg.format(count))

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

def evaluator(formula,
              variables=DEFAULT_VARIABLES,
              functions=DEFAULT_FUNCTIONS,
              suffixes=DEFAULT_SUFFIXES,
              max_array_dim=0):
    """
    Evaluate an expression; that is, take a string of math and return a float.

    -Variables are passed as a dictionary from string to value. They must be
     python numbers.
    -Unary functions are passed as a dictionary from string to function.
    -Everything is case sensitive (note, this is different to edX!)

    Usage
    =====
    >>> evaluator("1+1", {}, {}, {})
    (2.0, set([]))
    >>> evaluator("1+x", {"x": 5}, {}, {})
    (6.0, set([]))
    >>> evaluator("square(2)", {}, {"square": lambda x: x*x}, {})
    (4.0, set(['square']))
    >>> evaluator("", {}, {}, {})
    (nan, set([]))
    """
    if formula is None:
        # No need to go further.
        return float('nan'), set()
    formula = formula.strip()
    if formula == "":
        # No need to go further.
        return float('nan'), set()

    # Parse the tree
    math_interpreter = parsercache.get_parser(formula, suffixes)

    # Set the variables and functions
    math_interpreter.set_vars_funcs(variables, functions)

    # Check the variables and functions
    math_interpreter.check_variables()

    # Attempt to perform the evaluation
    try:
        result = math_interpreter.evaluate()
    except ZeroDivisionError:
        raise CalcZeroDivisionError("Division by zero occurred. "
                                    "Check your input's denominators.")
    except OverflowError:
        raise CalcOverflowError("Numerical overflow occurred. "
                                "Does your input contain very large numbers?")
    except Exception:
        # Don't know what this is, or how you want to deal with it
        raise

    # Were vectors/matrices/tensors used when they shouldn't have been?
    if math_interpreter.max_array_dim_used > max_array_dim:
        if max_array_dim == 0:
            msg = "Vector and matrix expressions have been forbidden in this entry."
        elif max_array_dim == 1:
            msg = "Matrix expressions have been forbidden in this entry."
        else:
            msg = "Tensor expressions have been forbidden in this entry."
        raise UnableToParse(msg)

    # Return the result of the evaluation, as well as the set of functions used
    return result, math_interpreter.functions_used

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
        self.max_array_dim_used = 0
        self.suffixes = suffixes
        self.actions = {
            'number': self.eval_number,
            'variable': lambda tokens: self.vars[tokens[0]],
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

    def evaluate(self):
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
                return node

            node_name = node.getName()
            if node_name not in self.actions:  # pragma: no cover
                raise Exception(u"Unknown branch name '{}'".format(node_name))

            action = self.actions[node_name]
            handled_kids = [handle_node(k) for k in node]
            return action(handled_kids)

        # Find the value of the entire tree.
        result = handle_node(self.tree)
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
            result = result * self.suffixes[parse_result[1]]
        return result

    def eval_function(self, parse_result):
        """
        Evaluates a function

        Arguments:
            parse_result: ['funcname', arglist]

        Usage
        =====
        >>> import math
        >>> parser = FormulaParser("1", {"%": 0.01})
        >>> parser.set_vars_funcs(functions={"sin": math.sin, "cos": math.cos})
        >>> parser.eval_function(['sin', [0]])
        0.0
        >>> parser.eval_function(['cos', [0]])
        1.0
        >>> def h(x, y): return x + y
        >>> parser.set_vars_funcs(functions={"h": h})
        >>> parser.eval_function(['h', [1, 2]])
        3
        >>> parser.eval_function(['h', [1, 2, 3]])
        Traceback (most recent call last):
        ArgumentError: Wrong number of arguments passed to h. Expected 2, received 3.
        >>> parser.eval_function(['h', [1]])
        Traceback (most recent call last):
        ArgumentError: Wrong number of arguments passed to h. Expected 2, received 1.
        """
        # Obtain the function and arguments
        name, args = parse_result
        func = self.functions[name]

        # Check to make sure we've been passed the correct number of arguments
        num_args = len(args)
        expected = get_number_of_args(func)
        if expected != num_args:
            msg = ("Wrong number of arguments passed to {func}. "
                   "Expected {num}, received {num2}.")
            raise ArgumentError(msg.format(func=name, num=expected, num2=num_args))

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
            if isinstance(err, ValueError) and 'factorial' in err.message:
                # This is thrown when fact() or factorial() is used
                # that tests on negative integer inputs
                # err.message will be: `factorial() only accepts integral values` or
                # `factorial() not defined for negative values`
                raise FactorialError("Error evaluating factorial() or fact() in input. " +
                                     "These functions cannot be used at negative integer values.")
            else:
                # Don't know what this is, or how you want to deal with it
                # Call it a domain issue.
                msg = ("There was an error evaluating {name}(...). "
                       "Its input does not seem to be in its domain.").format(name=name)
                raise FunctionEvalError(msg)

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

        All entries need to have the same shape:
        >>> parser.eval_array([                      # doctest: +ELLIPSIS
        ...     parser.eval_array([1, 2, 3]),
        ...     4
        ... ])
        Traceback (most recent call last):
        UnableToParse: Unable to parse vector/matrix. If you're trying ...
        """
        array = MathArray(parse_result)
        if array.dtype == 'object':
            # This happens, for example, with np.array([[1], 2, 3])
            msg = ("Unable to parse vector/matrix. If you're trying to enter a matrix, "
                   "make sure that each row has the same number of elements.For example, "
                   "[[1, 2, 3], [4, 5, 6]].")
            raise UnableToParse(msg)

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

        Usage
        =====
        >>> parser = FormulaParser("1", {"%": 0.01})
        >>> parser.eval_product([2,"*",3,"/",4])
        1.5
        >>> parser.eval_product([2,"*",3,"+",4])
        Traceback (most recent call last):
        CalcError: Undefined symbol + in eval_product
        """
        result = parse_result[0]
        data = parse_result[1:]
        while data:
            op = data.pop(0)
            num = data.pop(0)
            if op == '*':
                result = result * num
            elif op == '/':
                result = result / num
            else:
                raise CalcError("Undefined symbol {} in eval_product".format(op))
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
        CalcError: Undefined symbol * in eval_sum
        """
        data = parse_result[:]
        result = data.pop(0)
        if result == "+":
            result = data.pop(0)
        while data:
            op = data.pop(0)
            num = data.pop(0)
            if op == '+':
                result = result + num
            elif op == '-':
                result = result - num
            else:
                raise CalcError("Undefined symbol {} in eval_sum".format(op))
        return result
