"""
Tests of calc.py
"""
from __future__ import division
import re
import numpy as np
from pytest import raises, approx
from mitxgraders.exceptions import StudentFacingError
from mitxgraders import evaluator
from mitxgraders.helpers.calc.exceptions import (
    CalcError, UnableToParse,
    UnbalancedBrackets, UndefinedVariable,
    ArgumentError, CalcOverflowError, CalcZeroDivisionError
)
from mitxgraders.helpers.calc.math_array import equal_as_arrays, MathArray

def test_calcpy():
    """Tests of calc.py that aren't covered elsewhere"""

    # Test unhandled exception
    def badfunc(a):
        raise ValueError("Badness!")
    msg = (r"There was an error evaluating f\(...\). "
           "Its input does not seem to be in its domain.")
    with raises(CalcError, match=msg):
        evaluator("1+f(2)", {}, {"f": badfunc}, {})

    # Test formula with None
    value, used = evaluator(None, {}, {}, {})
    assert value == approx(float('nan'), nan_ok=True)
    assert (used.functions, used.variables, used.suffixes) == (set(), set(), set())

    # Test formulae with parallel operator
    value, used = evaluator("1 || 1 || 1", {}, {}, {})
    assert value == 1/3
    assert (used.functions, used.variables, used.suffixes) == (set(), set(), set())

    value, used = evaluator("1 || 1 || 0", {}, {}, {})
    assert value == approx(float('nan'), nan_ok=True)
    assert (used.functions, used.variables, used.suffixes) == (set(), set(), set())

    # Test incorrect case variables
    msg = r"Invalid Input: X not permitted in answer as a variable \(did you mean x\?\)"
    with raises(UndefinedVariable, match=msg):
        evaluator("X", {"x": 1}, {}, {})

def test_varnames():
    """Test variable names in calc.py"""
    # Tensor variable names
    assert evaluator("U^{ijk}", {"U^{ijk}": 2}, {}, {})[0] == 2
    assert evaluator("U_{ijk}/2", {"U_{ijk}": 2}, {}, {})[0] == 1
    assert evaluator("U_{ijk}^{123}", {"U_{ijk}^{123}": 2}, {}, {})[0] == 2
    assert evaluator("U_{ijk}^{123}'''''", {"U_{ijk}^{123}'''''": 2}, {}, {})[0] == 2
    assert evaluator("U_{ijk}^2", {"U_{ijk}": 2}, {}, {})[0] == 4
    assert evaluator("U^{ijk}^2", {"U^{ijk}": 2}, {}, {})[0] == 4
    assert evaluator("U_{ijk}^{123}^2", {"U_{ijk}^{123}": 2}, {}, {})[0] == 4
    # Regular variable names
    assert evaluator("U_cat/2 + Th3_dog__7a_", {"U_cat": 2, "Th3_dog__7a_": 4}, {}, {})[0] == 5
    # tensor subscripts need braces
    with raises(UnableToParse):
        assert evaluator("U_123^{ijk}", {}, {}, {})
    with raises(UnableToParse):
        assert evaluator("T_1_{123}^{ijk}", {}, {}, {})

def test_bracket_balancing_open_without_close_raises_error():
    assert issubclass(UnbalancedBrackets, StudentFacingError)

    # parens only
    match = ("Invalid Input: 2 parentheses were opened without being closed, "
             "highlighted below.\n"
             "<code>5 + <mark>(</mark>(1) + <mark>(</mark></code>")
    with raises(UnbalancedBrackets, match=re.escape(match)):
        evaluator("5 + ((1) + (")

    # brackets only
    match = ("Invalid Input: 1 square brackets were opened without being "
             "closed, highlighted below.\n"
             "<code>5 + <mark>[</mark>1, (1 + 2),</code>")
    with raises(UnbalancedBrackets, match=re.escape(match)):
        evaluator("5 + [1, (1 + 2), ")

    # parens and brackets
    match = ("Invalid Input: 1 parentheses and 1 square brackets were opened "
             "without being closed, highlighted below.\n"
             "<code>5 + <mark>(</mark>(1) + <mark>[</mark></code>")
    with raises(UnbalancedBrackets, match=re.escape(match)):
        evaluator("5 + ((1) + [")

def test_brackets_close_without_open_raises_error():
    match = ("Invalid Input: a parenthesis was closed without ever being "
             "opened, highlighted below.\n"
             "<code>5 + <mark>)</mark>1) + 1</code>")
    with raises(UnbalancedBrackets, match=re.escape(match)):
        evaluator("5 + )1) + 1")

def test_brackets_closed_by_wrong_type_raise_error():
    match = ("Invalid Input: a parenthesis was opened and then closed by a "
             "square bracket, highlighted below.\n"
             "<code>5 + <mark>(</mark>1+2<mark>]</mark> + 3</code>")
    with raises(UnbalancedBrackets, match=re.escape(match)):
        evaluator("5 + (1+2] + 3")

def test_calc_functions_multiple_arguments():
    """Tests calc.py handling functions with multiple arguments correctly"""
    def h1(x): return x

    def h2(x, y): return x * y

    def h3(x, y, z): return x * y * z

    assert evaluator("h(2)", {}, {"h": h1}, {})[0] == 2.0
    assert evaluator("h(2, 3)", {}, {"h": h2}, {})[0] == 6.0
    assert evaluator("h(2, 3, 4)", {}, {"h": h3}, {})[0] == 24.0
    assert equal_as_arrays(evaluator("h(2, [1, 2, 3])", {}, {"h": h2})[0],
                           MathArray([2, 4, 6]))
    with raises(ArgumentError):
        evaluator("h(2, 1)", {}, {"h": h1}, {})
    with raises(UnableToParse):
        evaluator("h()", {}, {"h": h1}, {})
    with raises(ArgumentError):
        evaluator("h(1)", {}, {"h": h2}, {})
    with raises(ArgumentError):
        evaluator("h(1,2,3)", {}, {"h": h2}, {})
    with raises(UnableToParse):
        evaluator("h()", {}, {"h": h3}, {})
    with raises(ArgumentError):
        evaluator("h(1)", {}, {"h": h3}, {})
    with raises(ArgumentError):
        evaluator("h(1,2)", {}, {"h": h3}, {})


def test_negation():
    """Test that appropriate numbers of +/- signs are accepted"""
    assert evaluator("1+-1")[0] == 0
    assert evaluator("1--1")[0] == 2
    assert evaluator("2*-1")[0] == -2
    assert evaluator("2/-4")[0] == -0.5
    assert evaluator("-1+-1")[0] == -2
    assert evaluator("+1+-1")[0] == 0
    assert evaluator("2^-2")[0] == 0.25
    assert evaluator("+-1")[0] == -1

    msg = "Invalid Input: Could not parse '{}' as a formula"
    badformulas = ["1---1", "2^--2", "1-+2", "1++2", "1+++2", "--2", "---2", "-+2", "--+2"]
    for formula in badformulas:
        with raises(UnableToParse, match=re.escape(msg.format(formula))):
            evaluator(formula)

def test_evaluation_does_not_mutate_variables():
    """
    This test should not be considered as related to vector/matrix/tensor algebra.

    We're just trying to verify that variables aren't accidentally mutated
    during evaluation.

    Numpy arrays just happen to be a convenient mutatable object that implements
    all the necessary operations.
    """

    A = np.array([
        [
            [1, 2, 3],
            [4, 5, 6]
        ],
        [
            [7, 8, 9],
            [10, 11, 12]
        ]
    ])
    A_copy = A.copy()
    variables = {'A': A}
    evaluator('A/2', variables)
    assert np.all(A == A_copy)

def test_inf_overflow():
    """Test that infinity is treated as an overflow when requested"""
    functions = {'f': lambda _ : float('inf')}
    # This is ok
    evaluator("f(1)", functions=functions, allow_inf=True)
    # This gives an error
    msg = "Numerical overflow occurred. Does your expression generate very large numbers\?"
    with raises(CalcOverflowError, match=msg):
        evaluator("f(1)", functions=functions,)

def test_div_by_zero():
    """Test that division by zero is caught"""
    msg = "Division by zero occurred. Check your input's denominators."
    with raises(CalcZeroDivisionError, match=msg):
        evaluator("1/0")
    with raises(CalcZeroDivisionError, match=msg):
        evaluator("0^-1")
