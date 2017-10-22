"""
calc.py

Parser and evaluator for mathematical expressions.

Uses pyparsing to parse. Main function is evaluator().

Based on the edX calc.py, but heavily modified.
"""
from __future__ import division
import numbers
import operator
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
    ZeroOrMore,
    alphanums,
    alphas,
    nums,
    stringEnd
)

class UndefinedVariable(Exception):
    """
    Indicate when a student inputs a variable which was not expected.
    """
    pass


class UndefinedFunction(Exception):
    """
    Indicate when a student inputs a function which was not expected.
    """
    pass


class UnmatchedParentheses(Exception):
    """
    Indicate when a student's input has unmatched parentheses.
    """
    pass


# The following few functions define evaluation actions, which are run on lists
# of results from each parse component. They convert the strings and (previously
# calculated) numbers into the number that component represents.

algebraic = (numbers.Number, np.matrix)


def eval_atom(parse_result):
    """
    Return the value wrapped by the atom.

    In the case of parenthesis, ignore them.
    """
    # Find first number in the list
    result = next(k for k in parse_result if isinstance(k, algebraic))
    return result


def eval_power(parse_result):
    """
    Take a list of numbers and exponentiate them, right to left.

    e.g. [ 2, 3, 2 ] -> 2^3^2 = 2^(3^2) -> 512
    (not to be interpreted (2^3)^2 = 64)
    """
    # `reduce` will go from left to right; reverse the list.
    parse_result = reversed(
        [k for k in parse_result
         if isinstance(k, algebraic)]  # Ignore the '^' marks.
    )

    # Having reversed it, raise `b` to the power of `a`.
    def robust_pow(b, a):
        try:
            # builtin fails for (-4)**0.5, but works better for matrices
            return b**a
        except ValueError:
            # scimath.power is componentwise power on matrices, hence above try
            return np.lib.scimath.power(b, a)

    power = reduce(lambda a, b: robust_pow(b, a), parse_result)

    return power


def eval_parallel(parse_result):
    """
    Compute numbers according to the parallel resistors operator.

    BTW it is commutative. Its formula is given by
      out = 1 / (1/in1 + 1/in2 + ...)
    e.g. [ 1, 2 ] -> 2/3

    Return NaN if there is a zero among the inputs.
    """
    if len(parse_result) == 1:
        return parse_result[0]
    if 0 in parse_result:
        return float('nan')
    reciprocals = [1. / e for e in parse_result
                   if isinstance(e, algebraic)]
    return 1. / sum(reciprocals)


def eval_sum(parse_result):
    """
    Add the inputs, keeping in mind their sign.

    [ 1, '+', 2, '-', 3 ] -> 0

    Allow a leading + or -.
    """
    total = 0.0
    current_op = operator.add
    for token in parse_result:
        if token == '+':
            current_op = operator.add
        elif token == '-':
            current_op = operator.sub
        else:
            total = current_op(total, token)
    return total


def eval_product(parse_result):
    """
    Multiply the inputs.

    [ 1, '*', 2, '/', 3 ] -> 0.66
    """
    prod = 1.0
    current_op = operator.mul
    for token in parse_result:
        if token == '*':
            current_op = operator.mul
        elif token == '/':
            current_op = operator.truediv
        else:
            prod = current_op(prod, token)
    return prod


class ParserCache(object):
    """Stores the parser trees for formula strings for reuse"""

    def __init__(self):
        """Initializes the cache"""
        self.cache = {}

    def get_parser(self, formula, case_sensitive, suffixes):
        """Get a ParseAugmenter object for a given formula"""
        # Check the formula for matching parentheses
        if formula.count("(") != formula.count(")"):
            raise UnmatchedParentheses()

        # Construct the key
        suffixstr = ""
        for key in suffixes:
            suffixstr += key
        key = (formula, case_sensitive, ''.join(sorted(suffixstr)))

        # Check if it's in the cache
        parser = self.cache.get(key, None)
        if parser is not None:
            return parser

        # It's not, so construct it
        parser = ParseAugmenter(formula, case_sensitive, suffixes)
        parser.parse_algebra()

        # Save it for later use before returning it
        self.cache[key] = parser
        return parser

# The global parser cache
parsercache = ParserCache()


def evaluator(formula, variables, functions, suffixes, case_sensitive=True):
    """
    Evaluate an expression; that is, take a string of math and return a float.

    -Variables are passed as a dictionary from string to value. They must be
     python numbers.
    -Unary functions are passed as a dictionary from string to function.
    """
    formula = formula.strip()
    if formula == "":
        # No need to go further.
        return float('nan')

    # Parse the tree
    math_interpreter = parsercache.get_parser(formula, case_sensitive, suffixes)

    # If we're not case sensitive, then lower all variables and functions
    if not case_sensitive:
        # Also make the variables and functions lower case
        variables = {key.lower(): value for key, value in variables.iteritems()}
        functions = {key.lower(): value for key, value in functions.iteritems()}

    # Check the variables and functions
    math_interpreter.check_variables(variables, functions)

    # Some helper functions...
    if case_sensitive:
        casify = lambda x: x
    else:
        casify = lambda x: x.lower()  # Lowercase for case insensitive

    def eval_number(parse_result):
        """
        Create a float out of string parts
        Applies suffixes appropriately
        e.g. [ '7.13', 'e', '3' ] ->  7130
        ['5', '%'] -> 0.05
        """
        text = "".join(parse_result)
        if text[-1] in suffixes:
            return float(text[:-1]) * suffixes[text[-1]]
        else:
            return float(text)

    # Create a recursion to evaluate the tree
    evaluate_actions = {
        'number': eval_number,
        'variable': lambda x: variables[casify(x[0])],
        'function': lambda x: functions[casify(x[0])](x[1]),
        'atom': eval_atom,
        'power': eval_power,
        'parallel': eval_parallel,
        'product': eval_product,
        'sum': eval_sum
    }

    # Return the result of the evaluation, as well as the set of functions used
    return math_interpreter.reduce_tree(evaluate_actions), math_interpreter.functions_used


class ParseAugmenter(object):
    """
    Holds the data for a particular parse.

    Retains the `math_expr` and `case_sensitive` so they needn't be passed
    around method to method.
    Eventually holds the parse tree and sets of variables as well.
    """
    def __init__(self, math_expr, case_sensitive, suffixes):
        """
        Create the ParseAugmenter for a given math expression string.

        Do the parsing later, when called like `OBJ.parse_algebra()`.
        """
        self.case_sensitive = case_sensitive
        self.math_expr = math_expr
        self.tree = None
        self.variables_used = set()
        self.functions_used = set()
        self.suffixes = suffixes

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

    def parse_algebra(self):
        """
        Parse an algebraic expression into a tree.

        Store a `pyparsing.ParseResult` in `self.tree` with proper groupings to
        reflect parenthesis and order of operations. Leave all operators in the
        tree and do not parse any strings of numbers into their float versions.

        Adding the groups and result names makes the `repr()` of the result
        really gross. For debugging, use something like
          print OBJ.tree.asXML()
        """
        # 0.33 or 7 or .34 or 16.
        number_part = Word(nums)
        inner_number = (number_part + Optional("." + Optional(number_part))) | ("." + number_part)
        # pyparsing allows spaces between tokens--`Combine` prevents that.
        inner_number = Combine(inner_number)

        # Apply suffixes
        number_suffix = MatchFirst(Literal(k) for k in self.suffixes.keys())

        # 0.33k or 17
        plus_minus = Literal('+') | Literal('-')
        number = Group(
            Optional(plus_minus) +
            inner_number +
            Optional(CaselessLiteral("E") + Optional(plus_minus) + number_part) +
            Optional(number_suffix)
        )
        number = number("number")

        # Predefine recursive variables.
        expr = Forward()

        # Handle variables passed in. They must start with letters/underscores
        # and may contain numbers afterward.
        inner_varname = Word(alphas + "_", alphanums + "_")
        varname = Group(inner_varname)("variable")
        varname.setParseAction(self.variable_parse_action)

        # Same thing for functions
        # Allow primes (apostrophes) at the end of function names, useful for
        # indicating derivatives. Eg, f'(x), g''(x)
        funcname = Combine(inner_varname + Optional(Word("'")))
        function = Group(funcname + Suppress("(") + expr + Suppress(")"))("function")
        function.setParseAction(self.function_parse_action)

        atom = number | function | varname | "(" + expr + ")"
        atom = Group(atom)("atom")

        # Do the following in the correct order to preserve order of operation.
        pow_term = atom + ZeroOrMore("^" + atom)
        pow_term = Group(pow_term)("power")

        par_term = pow_term + ZeroOrMore('||' + pow_term)  # 5k || 4k
        par_term = Group(par_term)("parallel")

        prod_term = par_term + ZeroOrMore((Literal('*') | Literal('/')) + par_term)  # 7 * 5 / 4
        prod_term = Group(prod_term)("product")

        sum_term = Optional(plus_minus) + prod_term + ZeroOrMore(plus_minus + prod_term)  # -5 + 4 - 3
        sum_term = Group(sum_term)("sum")

        # Finish the recursion.
        expr << sum_term  # pylint: disable=pointless-statement
        self.tree = (expr + stringEnd).parseString(self.math_expr)[0]

    def reduce_tree(self, handle_actions, terminal_converter=None):
        """
        Call `handle_actions` recursively on `self.tree` and return result.

        `handle_actions` is a dictionary of node names (e.g. 'product', 'sum',
        etc&) to functions. These functions are of the following form:
         -input: a list of processed child nodes. If it includes any terminal
          nodes in the list, they will be given as their processed forms also.
         -output: whatever to be passed to the level higher, and what to
          return for the final node.
        `terminal_converter` is a function that takes in a token and returns a
        processed form. The default of `None` just leaves them as strings.
        """
        def handle_node(node):
            """
            Return the result representing the node, using recursion.

            Call the appropriate `handle_action` for this node. As its inputs,
            feed it the output of `handle_node` for each child node.
            """
            if not isinstance(node, ParseResults):
                # Then treat it as a terminal node.
                if terminal_converter is None:
                    return node
                else:
                    return terminal_converter(node)

            node_name = node.getName()
            if node_name not in handle_actions:  # pragma: no cover
                raise Exception(u"Unknown branch name '{}'".format(node_name))

            action = handle_actions[node_name]
            handled_kids = [handle_node(k) for k in node]
            return action(handled_kids)

        # Find the value of the entire tree.
        return handle_node(self.tree)

    def check_variables(self, valid_variables, valid_functions):
        """
        Confirm that all the variables and functions used in the tree are defined.
        Otherwise, raise an UndefinedVariable or UndefinedFunction
        """
        if self.case_sensitive:
            casify = lambda x: x
        else:
            casify = lambda x: x.lower()  # Lowercase for case insens.

        # Test if casify(X) is valid, but return the actual bad input (i.e. X)
        bad_vars = set(var for var in self.variables_used
                       if casify(var) not in valid_variables)
        if bad_vars:
            raise UndefinedVariable(' '.join(sorted(bad_vars)))

        bad_funcs = set(func for func in self.functions_used
                        if casify(func) not in valid_functions)
        func_is_var = any(casify(func) in valid_variables for func in bad_funcs)
        if bad_funcs:
            raise UndefinedFunction(' '.join(sorted(bad_funcs)), func_is_var)
