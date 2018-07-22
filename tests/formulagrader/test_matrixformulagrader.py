from pytest import raises
import re
from mitxgraders import (MatrixGrader, RealMatrices, RealVectors, ComplexRectangle)
from mitxgraders.helpers.calc.exceptions import (
    DomainError, MathArrayError,
    MathArrayShapeError as ShapeError, UnableToParse
)

def test_max_array_dim():
    grader = MatrixGrader(
        answers="[1, 2, 3]"
    )
    # by default, student cannot enter matrices entry-by-entry
    match = "Matrix expressions have been forbidden in this entry."
    with raises(UnableToParse, match=match):
        grader(None, "[[1, 2, 3]]")

    # by default, author cannot enter matrices entry-by-entry
    # But it's not caught till grading occurs
    grader = MatrixGrader(
        answers="[[1, 2, 3]]"
    )
    with raises(UnableToParse, match=match):
        grader(None, "0")

    grader = MatrixGrader(
        answers="[[1, 2, 3]]",
        max_array_dim=2
    )
    assert grader(None, "[[1, 2, 3]]")['ok']

def test_fg_with_arrays():
    grader = MatrixGrader(
        answers='x*A*B*u + z*C^3*v/(u*C*v)',
        variables=['A', 'B', 'C', 'u', 'v', 'z', 'x'],
        sample_from={
            'A': RealMatrices(shape=[2, 3]),
            'B': RealMatrices(shape=[3, 2]),
            'C': RealMatrices(shape=[2, 2]),
            'u': RealVectors(shape=[2]),
            'v': RealVectors(shape=[2]),
            'z': ComplexRectangle()
        }
    )

    correct_0 = 'x*A*B*u + z*C^3*v/(u*C*v)'
    correct_1 = 'z*C^3*v/(u*C*v) + x*A*B*u'
    correct_2 = '(1/16)* z*(2*I)*(2*C)^3*v/(u*C*v) + x*A*B*u'
    correct_3 = '(1/16)* z*(2*I)*(2*C)^3*v/(v*trans(C)*u) + x*A*B*u/2 + 0.5*x*A*B*u'

    assert grader(None, correct_0)['ok']
    assert grader(None, correct_1)['ok']
    assert grader(None, correct_2)['ok']
    assert grader(None, correct_3)['ok']

    match = "Cannot multiply a matrix of shape \(rows: 3, cols: 2\) with a matrix of shape \(rows: 3, cols: 2\)"
    with raises(ShapeError, match=match):
        grader(None, 'B*B')

    match = "Cannot raise a non-square matrix to powers."
    with raises(ShapeError, match=match):
        grader(None, 'B^2')

    match = "Cannot add/subtract scalars to a matrix."
    with raises(ShapeError, match=match):
        grader(None, 'B + 5')

    match = "Cannot add/subtract multiples of the identity to a non-square matrix."
    with raises(ShapeError, match=match):
        grader(None, 'B + 5*I')

    match = ("There was an error evaluating function sin\(...\)<br/>"
             "1st input has an error: received a matrix of shape "
             "\(rows: 3, cols: 2\), expected a scalar")
    with raises(DomainError, match=match):
        grader(None, 'sin(B)')

def test_shape_errors_false_grades_incorrect():
    grader0 = MatrixGrader(
        answers='A*B',
        variables=['A', 'B'],
        sample_from={
            'A': RealMatrices(shape=[2, 3]),
            'B': RealMatrices(shape=[3, 2])
        }
    )
    grader1 = MatrixGrader(
        answers='A*B',
        variables=['A', 'B'],
        sample_from={
            'A': RealMatrices(shape=[2, 3]),
            'B': RealMatrices(shape=[3, 2])
        },
        shape_errors=False
    )

    msg = ("Cannot add/subtract a matrix of shape (rows: 2, cols: 3) with "
             "a matrix of shape (rows: 3, cols: 2).")
    with raises(ShapeError, match=re.escape(msg)):
        grader0(None, 'A + B')

    assert grader1(None, 'A + B') == {
        'ok': False,
        'msg': msg,
        'grade_decimal': 0
    }

def test_matrix_inverses_work_if_not_disabled():
    grader = MatrixGrader(
        answers='A^2',
        variables=['A'],
        sample_from={
            'A': RealMatrices()
        }
    )
    assert grader(None, 'A^3*A^-1')['ok']

def test_matrix_inverses_raise_error_if_disabled():
    grader = MatrixGrader(
        answers='A^2',
        variables=['A'],
        sample_from={
            'A': RealMatrices()
        },
        negative_powers=False
    )

    match='Negative matrix powers have been disabled.'
    with raises(MathArrayError, match=match):
        grader(None, 'A^3*A^-1')['ok']

def test_wrong_answer_type_error_messages():
    # Note: our convention is that single-row matrix and vectors cannot
    # be compared, [[1, 2, 3]] are graded as different [1, 2, 3]
    # (and, in particular, incomparable)

    grader = MatrixGrader(
        answers='[[1, 2, 3]]',
        max_array_dim=2,
        answer_shape_mismatch=dict(
            is_raised=True,
            msg_detail='shape'
        )
    )
    match = ('Expected answer to be a matrix of shape \(rows: 1, cols: 3\), '
             'but input is a vector of length 3')
    with raises(ShapeError, match=match):
        grader(None, '[1, 2, 3]')

    grader = MatrixGrader(
        answers='[[1, 2, 3]]',
        max_array_dim=2,
        answer_shape_mismatch=dict(
            is_raised=True,
            msg_detail='type'
        )
    )
    match = 'Expected answer to be a matrix, but input is a vector'
    with raises(ShapeError, match=match):
        grader(None, '[1, 2, 3]')

    grader = MatrixGrader(
        answers='[[1, 2, 3]]',
        max_array_dim=2,
        answer_shape_mismatch=dict(
            is_raised=False,
            msg_detail='shape'
        )
    )
    msg = ('Expected answer to be a matrix of shape (rows: 1, cols: 3), '
           'but input is a vector of length 3')
    assert grader(None, '[1, 2, 3]') == { 'ok': False, 'grade_decimal': 0, 'msg': msg }

    grader = MatrixGrader(
        answers='[[1, 2, 3]]',
        max_array_dim=2,
        answer_shape_mismatch=dict(
            is_raised=False,
            msg_detail='type'
        )
    )
    msg = 'Expected answer to be a matrix, but input is a vector'
    assert grader(None, '[1, 2, 3]') == { 'ok': False, 'grade_decimal': 0, 'msg': msg }

    msg = 'Expected answer to be a matrix, but input is a matrix of incorrect shape'
    assert grader(None, '[[1, 2, 3, 4]]') == { 'ok': False, 'grade_decimal': 0, 'msg': msg }

    grader = MatrixGrader(
        answers='[[1, 2, 3]]',
        max_array_dim=2,
        answer_shape_mismatch=dict(
            is_raised=False,
            msg_detail=None
        )
    )
    assert grader(None, '[1, 2, 3]') == { 'ok': False, 'grade_decimal': 0, 'msg': '' }
