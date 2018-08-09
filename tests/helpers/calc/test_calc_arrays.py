from __future__ import division
from pytest import raises
import numpy as np
from mitxgraders import evaluator, MathArray
from mitxgraders.helpers.calc.math_array import equal_as_arrays
from mitxgraders.helpers.calc.exceptions import UnableToParse, CalcError

def test_array_input():
    """Test that vectors/matrices can be inputted into calc.py"""
    result = evaluator("[1, 2, 3]", {}, {}, {}, max_array_dim=1)[0]
    assert equal_as_arrays(result, MathArray([1, 2, 3]))

    result = evaluator("[[1, 2], [3, 4]]", {}, {}, {}, max_array_dim=2)[0]
    assert equal_as_arrays(result, MathArray([[1, 2], [3, 4]]))

    expr = '[v, [4, 5, 6]]'
    result = evaluator(expr, {'v': MathArray([1, 2, 3])}, max_array_dim=2)[0]
    assert equal_as_arrays(result, MathArray([[1, 2, 3], [4, 5, 6]]))

    msg = "Vector and matrix expressions have been forbidden in this entry."
    with raises(UnableToParse, match=msg):
        evaluator("[[1, 2], [3, 4]]", {}, {}, {}, max_array_dim=0)
    msg = "Matrix expressions have been forbidden in this entry."
    with raises(UnableToParse, match=msg):
        evaluator("[[1, 2], [3, 4]]", {}, {}, {}, max_array_dim=1)
    msg = "Tensor expressions have been forbidden in this entry."
    with raises(UnableToParse, match=msg):
        evaluator("[[[1, 2], [3, 4]]]", {}, {}, {}, max_array_dim=2)

    # By default, this is fine
    evaluator("[[[1, 2], [3, 4]]]")

# NOTE: These two examples are very brief. The vast majority of MathArray testing
# is done in its own file. Essentially, all I want to do here is verify that
# FormulaParser.evaluate (through evaluator) is calling the correct methods

def test_math_arrays():
    A = MathArray([
        [1, 5],
        [4, -2]
    ])
    v = MathArray([3, -2])
    n = 3
    x = 4.2
    z = 2 + 3j
    variables = {
        'A': A,
        'v': v,
        'n': n,
        'x': x,
        'z': z
    }

    expr = '(z*[[1, 5], [4, -2]]^n + 10*A/x)*v'
    result = evaluator(expr, variables, max_array_dim=2)[0]
    assert equal_as_arrays(result, (z*A**n + 10*A/x)*v)

def test_triple_vector_product_raises_error():
    # Since vector products are interpretted as dot products, they are
    # ambiguous, and we disallow them.

    variables = {
    'i': MathArray([1, 0]),
    'j': MathArray([0, 1]),
    }

    assert equal_as_arrays(
        evaluator("(i*i)*j", variables)[0],
        variables['j']
    )

    match = ("Multiplying three or more vectors is ambiguous. "
             "Please place parentheses around vector multiplications.")
    with raises(CalcError, match=match):
        evaluator("i*i*j", variables)[0]

    with raises(CalcError, match=match):
        evaluator("i*2*i*3*j", variables)[0]

    match = 'cat'
    with raises(CalcError, match=match):
        evaluator("i*j/i*i*j", variables)[0]
