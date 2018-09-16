from __future__ import division
from pytest import raises
import random
import numpy as np
from numbers import Number
from mitxgraders.helpers.calc.math_array import (
    MathArray,
    equal_as_arrays,
    approx_equal_as_arrays,
    random_math_array
)
from mitxgraders.helpers.calc.exceptions import (
    MathArrayError, MathArrayShapeError as ShapeError)

def test_random_math_array():
    matrix = random_math_array([3, 7])
    assert matrix.shape == (3, 7)
    assert isinstance(matrix, MathArray)

    tensor = random_math_array([3, 7, 5])
    assert tensor.shape == (3, 7, 5)
    assert isinstance(tensor, MathArray)

##########     Test Instantiation and Properties     ##########

def test_array_class_is_correct():
    """Tests two forms of MathArray creation actually create MathArray instances"""
    from_constructor = MathArray([[1, 2, 3], [4, 5, 6]])
    assert isinstance(from_constructor, MathArray)

    from_slice = MathArray([[1, 2, 3], [4, 5, 6]])[:, 2:3]
    assert isinstance(from_slice, MathArray)

def test_copying():
    A = MathArray([1, 2, 3])
    assert equal_as_arrays(A, A.copy())

def test_descriptions():
    scalar = MathArray(5)
    assert scalar.shape_name == 'scalar'
    assert scalar.description == 'scalar'
    assert scalar.shape == tuple()

    vector = MathArray([1, 2, 3, 4, 5])
    assert vector.shape_name == 'vector'
    assert vector.description == 'vector of length 5'
    assert vector.shape == (5,)

    matrix = MathArray([vector, vector, vector])
    assert matrix.shape_name == 'matrix'
    assert matrix.description == 'matrix of shape (rows: 3, cols: 5)'
    assert matrix.shape == (3, 5)


    tensor1 = MathArray([matrix, matrix, matrix, matrix])
    assert tensor1.shape_name == 'tensor'
    assert tensor1.description == 'tensor of shape (4, 3, 5)'
    assert tensor1.shape == (4, 3, 5)

    tensor2 = MathArray([tensor1, tensor1])
    assert tensor2.shape_name == 'tensor'
    assert tensor2.description == 'tensor of shape (2, 4, 3, 5)'
    assert tensor2.shape == (2, 4, 3, 5)


##########     Test Addition     ##########

def test_addition_with_correct_shapes():

    u = MathArray([1, 2, 3])
    v = MathArray([10, 20, 30])
    w = MathArray([11, 22, 33])
    assert equal_as_arrays(u + v, w)

    A = MathArray([[5,  2, 1], [-2, 4, -3]])
    B = MathArray([[2, -1, 4], [3,  0,  1]])
    C = MathArray([[7,  1, 5], [1,  4, -2]])
    assert equal_as_arrays(A + B, C)
    assert equal_as_arrays(A + B, B + A)

def test_addition_with_shape_mismath():
    # shape mismatch
    A = MathArray([[5, 2, 1], [-2, 4, -3]])
    B = MathArray([[2, -1], [3, 0]])
    match = ('Cannot add/subtract a matrix of shape \(rows: 2, cols: 3\) '
             'with a matrix of shape \(rows: 2, cols: 2\).')
    with raises(ShapeError, match=match):
        A + B

    # dimension mismatch
    u = MathArray([1, 2])
    v = MathArray([1, 2, 3])
    match = ('Cannot add/subtract a vector of length 2 with a matrix of '
             'shape \(rows: 2, cols: 2\).')
    with raises(ShapeError, match=match):
        u + B

    match = ('Cannot add/subtract a vector of length 2 with a vector of length 3.')
    with raises(ShapeError, match=match):
        u + v

def test_addition_with_zero():
    A = MathArray([[5,  2, 1], [-2, 4, -3]])
    assert equal_as_arrays(A + 0, A)
    assert equal_as_arrays(0 + A, A)
    z0 = MathArray(0)
    assert equal_as_arrays(A + z0, A)
    assert equal_as_arrays(z0 + A, A)

    # This is ugly, but convenient for logic and implementation
    z3 = MathArray([[[0]]])
    assert equal_as_arrays(A + z3, A)
    assert equal_as_arrays(z3 + A, A)

    u = MathArray([1, 2])
    assert equal_as_arrays(u + 0, u)
    assert equal_as_arrays(0 + u, u)

def test_addition_with_other_types():
    A = MathArray([[5, 2], [-2, 4]])
    match = "Cannot add/subtract scalars to a matrix."
    with raises(ShapeError, match=match):
        A + 1
    with raises(ShapeError, match=match):
        A + 1.0
    with raises(ShapeError, match=match):
        A + (1 + 2j)
    with raises(TypeError, match="Cannot add/subtract a matrix with object of "
                "<type 'list'>"):
        A + [[1, 2], [4, 5]]

##########     Test Subtraction     ##########
def test_subtraction_with_correct_shapes():

    u = MathArray([1, 2, 3])
    v = MathArray([10, 20, 30])
    w = MathArray([9, 18, 27])
    assert equal_as_arrays(v - u, w)

    A = MathArray([[5,  2, 1], [-2, 4, -3]])
    B = MathArray([[2, -1, 4], [3,  0,  1]])
    C = MathArray([[3,  3, -3], [-5,  4, -4]])
    assert equal_as_arrays(A - B, C)

def test_subtraction_with_shape_mismath():
    # shape mismatch
    A = MathArray([[5,  2, 1], [-2, 4, -3]])
    B = MathArray([[2, -1], [3,  0]])
    match = ('Cannot add/subtract a matrix of shape \(rows: 2, cols: 3\) '
             'with a matrix of shape \(rows: 2, cols: 2\).')
    with raises(ShapeError, match=match):
        A - B

    # dimension mismatch
    u = MathArray([1, 2])
    match = ('Cannot add/subtract a vector of length 2 with a matrix of '
             'shape \(rows: 2, cols: 2\).')
    with raises(ShapeError, match=match):
        u - B

def test_subtraction_with_zero():
    A = MathArray([[5,  2, 1], [-2, 4, -3]])
    assert equal_as_arrays(A - 0, A)
    assert equal_as_arrays(0 - A, -A) # pylint: disable=invalid-unary-operand-type

    u = MathArray([1, 2])
    assert equal_as_arrays(u - 0, u)
    assert equal_as_arrays(0 - u, -u) # pylint: disable=invalid-unary-operand-type

def test_subtraction_with_other_types():
    A = MathArray([[5,  2], [-2, 4]])

    match = "Cannot add/subtract scalars to a matrix."
    with raises(ShapeError, match=match):
        A - 1
    with raises(ShapeError, match=match):
        A - 1.0
    with raises(ShapeError, match=match):
        A - (1 + 2j)
    with raises(TypeError, match="Cannot add/subtract a matrix with object of "
                "<type 'list'>"):
        A - [[1, 2], [4, 5]]

##########     Test Multiplication     ##########
def test_matrix_times_matrix_multiplication():
    A = MathArray([
        [5, 2, 3],
        [-4, 3, -1]
    ])
    B = MathArray([
        [0, 4, 5, 2],
        [5, -2, 6, -3],
        [-7, 5, 8, 4]
    ])
    C = MathArray([
        [-11, 31, 61, 16],
        [22, -27, -10, -21]
    ])
    assert equal_as_arrays(A*B, C)

    X = random_math_array([3, 5])
    Y = random_math_array([4, 2])

    match = ("Cannot multiply a matrix of shape \(rows: 3, cols: 5\) with a matrix "
             "of shape \(rows: 4, cols: 2\)")
    with raises(ShapeError, match=match):
        X*Y

    row = MathArray([[1, 2, 3]])
    col = MathArray([[1], [2], [3]])
    assert row*col == 14 and isinstance(row*col, Number)

def test_matrix_times_vector_multiplication():
    u = MathArray([1, -2, 3])
    A = MathArray([
        [2, 4, -1],
        [4, -3, 0]
    ])
    b = MathArray([-9, 10])
    assert equal_as_arrays(A*u, b)
    assert b.ndim == 1 # result is a vector

    X = random_math_array([4, 3])
    Y = random_math_array(5)

    match = ("Cannot multiply a matrix of shape \(rows: 4, cols: 3\) with a vector "
             "of length 5.")
    with raises(ShapeError, match=match):
        X*Y

def test_vector_times_matrix_multiplication():
    u = MathArray([1, -2, 3])
    A = MathArray([
        [2, 4],
        [4, -3],
        [-1, 0]
    ])
    b = MathArray([-9, 10])
    assert equal_as_arrays(u*A, b)
    assert b.ndim == 1 # result is a vector

    X = random_math_array(5)
    Y = random_math_array([4, 3])

    match = ("Cannot multiply a vector of length 5 with a matrix of shape "
             "\(rows: 4, cols: 3\)")
    with raises(ShapeError, match=match):
        X*Y

def test_vector_times_vector_is_dot_product():
    a = MathArray([1, 2, 3])
    b = MathArray([-2, 3, 4])
    c = MathArray([1, 2, 3, 4, 5])

    assert isinstance(a*b, Number)
    assert a*b == b*a == 16

    match = "Cannot calculate the dot product of a vector of length 3 with a vector of length 5"
    with raises(ShapeError, match=match):
        a*c

def test_vector_times_vector_does_not_conjugate():
    a = MathArray([1j, 4, 3])
    b = MathArray([1j, 2, -1])
    # -1 + 8 -3 = 3
    assert a*b == b*a == 4

def test_scalar_product():
    X = MathArray([
        [1, 2, 3],
        [10, 20, 30]
    ])
    two = MathArray(2)
    two3 = MathArray([[[2]]])
    Y = MathArray([
        [2, 4, 6],
        [20, 40, 60]
    ])
    assert equal_as_arrays(2*X, Y)
    assert equal_as_arrays(X*2, Y)
    assert equal_as_arrays(two*X, Y)
    assert equal_as_arrays(X*two, Y)
    # This is ugly, but convenient for logic and implementation
    assert equal_as_arrays(two3*X, Y)
    assert equal_as_arrays(X*two3, Y)

def test_tensor_multiplication_not_supported():
    A = random_math_array([2, 3, 4])
    B = random_math_array([4, 2])

    match = "Multiplication of tensor arrays is not currently supported."
    with raises(MathArrayError, match=match):
        A*B
    with raises(MathArrayError, match=match):
        B*A

def test_multiplication_with_unexpected_types_raises_TypeError():
    A = random_math_array([4, 2])
    B = [1, 2, 3]
    match = "Cannot multiply a matrix with object of <type 'list'>"
    with raises(TypeError, match=match):
        A*B

    match = "Cannot multiply object of type <type 'list'> with a matrix."
    with raises(TypeError, match=match):
        B*A

##########     Test Division     ##########
def test_division_by_scalar():
    A = MathArray([4, 8])
    assert equal_as_arrays(A/2, MathArray([2, 4]))
    assert equal_as_arrays(A/MathArray(2), MathArray([2, 4]))

    assert 4/MathArray(2) == MathArray(2)

def test_division_by_array_raises_error():
    A = MathArray([4, 8])

    match = "Cannot divide by a vector"
    with raises(ShapeError, match=match):
        2/A

    match = "Cannot divide a vector by a vector"
    with raises(ShapeError, match=match):
        A/A

    match = "Cannot divide vector by object of <type 'list'>"
    with raises(TypeError, match=match):
        A/[1, 2, 3]

##########     Test Powers     ##########
def test_matrix_power_works_with_floats_and_scalars_if_integral():
    A = random_math_array([3, 3])
    assert equal_as_arrays(A**2, A**2.0)
    assert equal_as_arrays(A**2, A**MathArray(2.0))

def test_nonpositive_matrix_powers():
    A = MathArray([
        [1, 5],
        [-4, 3]
    ])
    I2 = MathArray([
        [1, 0],
        [0, 1]
    ])

    # B is not invertible
    B = MathArray([
        [2, 1],
        [6, 3]
    ])

    assert equal_as_arrays(A**0, I2)
    # Slight numerical errors in the inversion
    assert approx_equal_as_arrays(A**-2 * A**3, A, tol=1e-15)

    match = 'Cannot raise singular matrix to negative powers.'
    with raises(MathArrayError, match=match):
        B**-1

def test_power_error_messages():
    A = random_math_array([3, 3])
    B = random_math_array([3, 4])
    u = random_math_array([5])

    # Plausible case with MathArray on the right.
    match = 'Cannot raise a scalar to power of a matrix.'
    with raises(ShapeError, match=match):
        2**A

    # Weird case with MathArray on the right.
    match = "Cannot raise <type 'list'> to power of matrix."
    with raises(TypeError, match=match):
        [1, 2, 3]**A

    # with MathArrays on the left:

    match = 'Cannot raise a vector to powers.'
    with raises(ShapeError, match=match):
        u**2
    with raises(ShapeError, match=match):
        u**A

    match = "Cannot raise a matrix to non-integer powers"
    with raises(MathArrayError, match=match):
        A**2.4

    match = "Cannot raise a non-square matrix to powers."
    with raises(ShapeError, match=match):
        B**2

    match = "Cannot raise a matrix to matrix powers."
    with raises(ShapeError, match=match):
        A**B

    match = "Cannot raise matrix to power of type <type 'list'>."
    with raises(TypeError, match=match):
        A**[1, 2, 3]

def test_scalar_special_cases():
    five = MathArray(5)
    three = MathArray(3)
    # Addition
    assert five + three == 8
    assert five + 3 == 8
    assert 5 + three == 8
    # Subtraction
    assert five - three == 2
    assert five - 3 == 2
    assert 5 - three == 2
    # Powers
    assert five**3 == 125
    assert 5**three == 125
    assert five**three == 125

    # With MathArrays on the right:
    match = "Cannot raise a scalar to a <type 'list'> power"
    with raises(TypeError, match=match):
        MathArray(2)**[1, 2, 3]

    match = 'Cannot raise a scalar to power of a vector.'
    with raises(ShapeError, match=match):
        MathArray(2)**MathArray([1, 2, 3])

##########     Test in-place operations     ##########
def test_in_place_addition():

    amounts = [0, random_math_array([2, 2])]
    for amount in amounts:
        A = random_math_array([2, 2])
        A_copy = A.copy()
        A += amount
        assert equal_as_arrays(A, A_copy + amount)

def test_in_place_subtraction():

    amounts = [0, random_math_array([2, 2])]
    for amount in amounts:
        A = random_math_array([2, 2])
        A_copy = A.copy()
        A -= amount
        assert equal_as_arrays(A, A_copy - amount)

def test_in_place_multiplication():

    amounts = [5, random_math_array(tuple()), random_math_array([2, 2])]
    for amount in amounts:
        A = random_math_array([2, 2])
        A_copy = A.copy()
        A *= amount
        assert equal_as_arrays(A, A_copy * amount)

def test_in_place_division():

    amounts = [5, MathArray(5)]
    for amount in amounts:
        A = random_math_array([2, 2])
        A_copy = A.copy()
        A /= amount
        assert equal_as_arrays(A, A_copy / amount)

def test_in_place_powers():
    amounts = [2, -3.0, MathArray(5)]
    for amount in amounts:
        A = random_math_array([2, 2])
        A_copy = A.copy()
        A **= amount
        assert equal_as_arrays(A, A_copy ** amount)

##########     Miscellaneous     ##########

def test_numpy_functions_preserve_class():
    A = MathArray([
        [1, 2, 3],
        [4, 5, 6]
    ])
    A_trans = MathArray([
        [1, 4],
        [2, 5],
        [3, 6]
    ])
    assert equal_as_arrays(np.transpose(A), A_trans)
    assert equal_as_arrays(A.T, A_trans)
