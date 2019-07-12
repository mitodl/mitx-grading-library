from pytest import raises
from mitxgraders import FormulaGrader, MatrixGrader, RealMatrices, NumericalGrader
from mitxgraders.comparers import LinearComparer
from mitxgraders.exceptions import ConfigError

def test_linear_comparer_default_modes():
    grader = FormulaGrader(
        answers={
            'comparer_params': ['m*c^2'],
            'comparer': LinearComparer()
        },
        variables=['m', 'c']
    )

    equals_result = {'msg': '', 'grade_decimal': 1.0, 'ok': True}
    proportional_result = {
        'msg': 'The submitted answer differs from an expected answer by a constant factor.',
        'grade_decimal': 0.5,
        'ok': 'partial'
    }
    wrong_result = {'msg': '', 'grade_decimal': 0, 'ok': False}

    assert grader(None, 'm*c^2') == equals_result
    assert grader(None, '3*m*c^2') == proportional_result
    assert grader(None, 'm*c^2 + 10') == wrong_result
    assert grader(None, '-3*m*c^2 + 10') == wrong_result
    assert grader(None, 'm*c^3') == wrong_result
    assert grader(None, '0') == wrong_result

def test_linear_comparer_with_zero_as_correct_answer():
    grader = FormulaGrader(
        answers={
            'comparer_params': ['0'],
            'comparer': LinearComparer(proportional=0.5, offset=0.4, linear=0.3)
        },
        variables=['m', 'c']
    )
    assert grader(None, '0')['grade_decimal'] == 1
    assert grader(None, 'm')['grade_decimal'] == 0 # proportional & linear test fails
    assert grader(None, '1')['grade_decimal'] == 0.4 # not 0.5, proportional disabled

def test_linear_comparer_custom_credit_modes():
    grader = FormulaGrader(
        answers={
            'comparer_params': ['m*c^2'],
            'comparer': LinearComparer(equals=0.8, proportional=0.6, offset=0.4, linear=0.2)
        },
        variables=['m', 'c']
    )

    equals_result = {'msg': '', 'grade_decimal': 0.8, 'ok': 'partial'}
    proportional_result = {
        'msg': 'The submitted answer differs from an expected answer by a constant factor.',
        'grade_decimal': 0.6,
        'ok': 'partial'
    }
    offset_result = {'msg': '', 'grade_decimal': 0.4, 'ok': 'partial'}
    linear_result = {'msg': '', 'grade_decimal': 0.2, 'ok': 'partial'}
    wrong_result = {'msg': '', 'grade_decimal': 0, 'ok': False}

    assert grader(None, 'm*c^2') == equals_result
    assert grader(None, '3*m*c^2') == proportional_result
    assert grader(None, 'm*c^2 + 10') == offset_result
    assert grader(None, '-3*m*c^2 + 10') == linear_result
    assert grader(None, 'm*c^3') == wrong_result
    assert grader(None, '0') == wrong_result

def test_scaling_partial_credit():
    FormulaGrader.set_default_comparer(LinearComparer())
    grader = FormulaGrader(
        answers=(
            'm*c^2',
            { 'expect': 'm*c^3', 'grade_decimal': 0.1 }
        ),
        variables=['m', 'c']
    )
    FormulaGrader.reset_default_comparer()

    expected = {
        'ok': 'partial',
        'grade_decimal': 0.1 * 0.5,
        # This message is a bit awkward ... in this situation, probably better to set up
        # a different LinearComparer for the common wrong answers, if you want to do that.
        # Or only use an linear comparer for the correct answer, and use equality_compaer
        # for the common wrong answers.
        # Anyway, I'm just testing the partial credit scaling
        'msg': 'The submitted answer differs from an expected answer by a constant factor.',
    }

    assert grader(None, '4*m*c^3') == expected

def test_works_with_matrixgrader():
    grader = MatrixGrader(
        answers={
            'comparer_params': ['x*A*B^2'],
            'comparer': LinearComparer(proportional=0.6, offset=0.4, linear=0.2)
        },
        variables=['x', 'A', 'B'],
        sample_from={
            'A': RealMatrices(),
            'B': RealMatrices()
        },
        max_array_dim=2
    )

    assert grader(None, 'x*A*B^2')['grade_decimal'] == 1.0
    assert grader(None, '2*x*A*B^2')['grade_decimal'] == 0.6
    assert grader(None, 'x*A*B^2 + 5*[[1, 1], [1, 1]]')['grade_decimal'] == 0.4
    assert grader(None, '3*x*A*B^2 + 5*[[1, 1], [1, 1]]')['grade_decimal'] == 0.2
    assert grader(None, 'x*A*B^2 + x*[[1, 1], [1, 1]]')['grade_decimal'] == 0
    assert grader(None, '0*A')['grade_decimal'] == 0

def test_linear_too_few_comparisons():
    FormulaGrader.set_default_comparer(LinearComparer())
    grader = FormulaGrader(samples=2)
    with raises(ConfigError, match='Cannot perform linear comparison with less than 3 samples'):
        grader('1.5', '1.5')

    # Ensure that NumericalGrader does not use the same default comparer as FormulaGrader
    grader = NumericalGrader()
    assert grader('1.5', '1.5')['ok']

    FormulaGrader.reset_default_comparer()
