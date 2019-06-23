from mitxgraders import FormulaGrader
from mitxgraders.comparers import LinearComparer

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
