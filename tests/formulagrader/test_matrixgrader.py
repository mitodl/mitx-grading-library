from __future__ import print_function, division, absolute_import

import re
from pytest import raises
from mitxgraders import (MatrixGrader, RealMatrices, RealVectors, ComplexRectangle)
from mitxgraders.formulagrader.matrixgrader import InputTypeError
from mitxgraders.helpers.calc.exceptions import (
    DomainError, MathArrayError, ArgumentError,
    MathArrayShapeError as ShapeError, UnableToParse
)
from mitxgraders.helpers.calc.math_array import identity, equal_as_arrays

def test_identity_dim_provides_identity():
    no_identity = MatrixGrader()
    assert no_identity.constants.get('I', None) is None

    grader = MatrixGrader(
        identity_dim=4
    )
    assert equal_as_arrays(grader.constants['I'], identity(4))

def test_max_array_dim():
    grader = MatrixGrader(
        answers="[1, 2, 3]"
    )
    # by default, student cannot enter matrices entry-by-entry
    match = "Matrix expressions have been forbidden in this entry."
    with raises(UnableToParse, match=match):
        grader(None, "[[1, 2, 3]]")

    # But authors can. This allows authors to specify a matrix in comparer_params
    # when students are required to input an eigenvector
    grader = MatrixGrader(
        answers="[[1, 2, 3]]"
    )
    match = "Expected answer to be a matrix, but input is a scalar"
    with raises(InputTypeError, match=match):
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
        },
        identity_dim=2
    )

    correct_0 = 'x*A*B*u + z*C^3*v/(u*C*v)'
    correct_1 = 'z*C^3*v/(u*C*v) + x*A*B*u'
    correct_2 = '(1/16)* z*(2*I)*(2*C)^3*v/(u*C*v) + x*A*B*u'
    correct_3 = '(1/16)* z*(2*I)*(2*C)^3*v/(v*trans(C)*u) + x*A*B*u/2 + 0.5*x*A*B*u'

    assert grader(None, correct_0)['ok']
    assert grader(None, correct_1)['ok']
    assert grader(None, correct_2)['ok']
    assert grader(None, correct_3)['ok']

    match = r"Cannot multiply a matrix of shape \(rows: 3, cols: 2\) with a matrix of shape \(rows: 3, cols: 2\)"
    with raises(ShapeError, match=match):
        grader(None, 'B*B')

    match = "Cannot raise a non-square matrix to powers."
    with raises(ShapeError, match=match):
        grader(None, 'B^2')

    match = "Cannot add/subtract scalars to a matrix."
    with raises(ShapeError, match=match):
        grader(None, 'B + 5')

    match = (r"There was an error evaluating function sin\(...\)<br/>"
             r"1st input has an error: received a matrix of shape "
             r"\(rows: 3, cols: 2\), expected a scalar")
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
    match = (r'Expected answer to be a matrix of shape \(rows: 1, cols: 3\), '
             r'but input is a vector of length 3')
    with raises(InputTypeError, match=match):
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
    with raises(InputTypeError, match=match):
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

def test_wrong_answer_type_error_messages_with_scalars():
    """
    Check that answer shape errors are raised correctly when answer or student_input
    is a scalar.

    These are worth checking separately because the numbers do not have 'shape'
    attributes.
    """

    grader = MatrixGrader(
        answers='[1, 2, 3]',
        max_array_dim=2,
        answer_shape_mismatch=dict(
            is_raised=True,
            msg_detail='type'
        )
    )
    match = 'Expected answer to be a vector, but input is a scalar'
    with raises(InputTypeError, match=match):
        grader(None, '10')

    grader = MatrixGrader(
        answers='10',
        max_array_dim=2,
        answer_shape_mismatch=dict(
            is_raised=True,
            msg_detail='type'
        )
    )
    match = 'Expected answer to be a scalar, but input is a vector'
    with raises(InputTypeError, match=match):
        grader(None, '[1, 2, 3]')

def test_validate_student_input_shape_edge_case():
    with raises(AttributeError):
        MatrixGrader.validate_student_input_shape([1, 2], (2,), 'type')

def test_suppress_matrix_messages():
    grader = MatrixGrader(
        answers='[1, 2, 3]',
        answer_shape_mismatch=dict(
            is_raised=True,  # Overridden by suppress_matrix_messages
        ),
        shape_errors=True,  # Overridden by suppress_matrix_messages
        suppress_matrix_messages=True
    )
    assert grader(None, '10')['ok'] is False
    assert grader(None, '10')['msg'] == ''
    assert grader(None, '[1, 2, 3] + 1')['ok'] is False
    assert grader(None, '[1, 2, 3] + 1')['msg'] == ''
    assert grader(None, '[1, 2, 3, 4]')['ok'] is False
    assert grader(None, '[1, 2, 3, 4]')['msg'] == ''
    assert grader(None, 'sin([1, 2, 3])')['ok'] is False
    assert grader(None, '[1, 2, 3]^1.3')['ok'] is False

    # Note that we haven't suppressed all errors:
    with raises(ArgumentError):
        grader(None, 'sin(1, 2)')

def test_default_grader_instance_override():
    grader_0 = MatrixGrader()
    grader_1 = MatrixGrader(entry_partial_credit='proportional')
    grader_2 = MatrixGrader()

    # not the same grader...
    assert grader_0 is not grader_2
    # but should use the exact same comparer function, class default
    assert grader_0.default_comparer is grader_2.default_comparer
    # but grader_1 should use an instance-specific default_comparer
    assert grader_0.default_comparer is not grader_1.default_comparer

def test_entry_partial_proportional_credit_grading():
    grader = MatrixGrader(
        max_array_dim=2,
        answers='[[0, 1, 2], [x, y, z]]',
        variables=['x', 'y', 'z'],
        entry_partial_credit='proportional'
    )
    expected = {
        'ok': 'partial',
        'msg': 'Matrix entries at [row column] locations [1 2], [1 3], [2 1], [2 2] are incorrect.',
        'grade_decimal': 2/6
    }
    assert grader(None, '[[0, 10, 20*z], [x/2, y^2, z]]') == expected
    assert grader(None, '[[0, 1, 2], [x, y, z]]') == {
        'ok': True,
        'msg': '',
        'grade_decimal': 1
    }
    assert grader(None, '[[10, 20, 30], [40, 50, 60]]') == {
        'ok': False,
        'msg': '',
        'grade_decimal': 0
    }

def test_entry_partial_flat_rate_credit_grading():
    grader = MatrixGrader(
        max_array_dim=2,
        answers='[[0, 1, 2], [x, y, z]]',
        variables=['x', 'y', 'z'],
        entry_partial_credit=0.123
    )
    expected = {
        'ok': 'partial',
        'msg': 'Matrix entries at [row column] locations [1 2], [1 3], [2 1], [2 2] are incorrect.',
        'grade_decimal': 0.123
    }
    assert grader(None, '[[0, 10, 20*z], [x/2, y^2, z]]') == expected
    assert grader(None, '[[0, 1, 2], [x, y, z]]') == {
        'ok': True,
        'msg': '',
        'grade_decimal': 1
    }
    assert grader(None, '[[10, 20, 30], [40, 50, 60]]') == {
        'ok': False,
        'msg': '',
        'grade_decimal': 0
    }
