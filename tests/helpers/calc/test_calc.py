"""
Tests of calc.py
"""
from __future__ import division
import re
import numpy as np
from pytest import raises, approx
from mitxgraders import CalcError
from mitxgraders.baseclasses import StudentFacingError
from mitxgraders.helpers.calc import (evaluator, UnableToParse, UndefinedVariable,
                                     ArgumentError, UnbalancedBrackets)

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

def test_bracket_balancing():
    assert issubclass(UnbalancedBrackets, StudentFacingError)

    expect = ("Invalid Input: parentheses are unmatched. 1 parentheses "
              "were opened but never closed.")
    with raises(UnbalancedBrackets, match=expect):
        evaluator("5*(3")

    expect = ("Invalid Input: A closing parenthesis was found after segment "
              "'5\*\(3\)', but there is no matching opening parenthesis before it.")
    with raises(UnbalancedBrackets, match=expect):
        evaluator("5*(3))")

    expect = ("Invalid Input: square brackets are unmatched. 1 square brackets "
              "were opened but never closed.")
    with raises(UnbalancedBrackets, match=expect):
        evaluator("[1,2,3")

    expect = ("Invalid Input: A closing square bracket was found after segment "
              "'1,2,3', but there is no matching opening square bracket before it.")
    with raises(UnbalancedBrackets, match=expect):
        evaluator("1,2,3]")

def test_calc_functions_multiple_arguments():
    """Tests calc.py handling functions with multiple arguments correctly"""
    def h1(x): return x

    def h2(x, y): return x + y

    def h3(x, y, z): return x + y + z

    assert evaluator("h(2)", {}, {"h": h1}, {})[0] == 2.0
    assert evaluator("h(1, 2)", {}, {"h": h2}, {})[0] == 3.0
    assert evaluator("h(1, 2, 3)", {}, {"h": h3}, {})[0] == 6.0
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
