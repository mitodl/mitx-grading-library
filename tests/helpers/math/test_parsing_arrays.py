from __future__ import division
from pytest import raises
from mitxgraders.helpers.mitmath import evaluator, MathArray, IdentityMultiple
from mitxgraders.helpers.mitmath.math_array import equal_as_arrays
from mitxgraders.helpers.mitmath.exceptions import UnableToParse

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
        evaluator("[[1, 2], [3, 4]]", {}, {}, {})
    msg = "Matrix expressions have been forbidden in this entry."
    with raises(UnableToParse, match=msg):
        evaluator("[[1, 2], [3, 4]]", {}, {}, {}, max_array_dim=1)
    msg = "Tensor expressions have been forbidden in this entry."
    with raises(UnableToParse, match=msg):
        evaluator("[[[1, 2], [3, 4]]]", {}, {}, {}, max_array_dim=2)

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

def test_identity_multiple():
    I5 = IdentityMultiple(5)
    n = 3
    x = 4.2
    z = 2 + 3j
    variables = {
        'I5': I5,
        'n': n,
        'x': x,
        'z': z
    }

    expr = 'z*I5^n + 10*I5/x'
    result = evaluator(expr, variables, max_array_dim=2)[0]
    assert result == z*I5**n + 10*I5/x
