"""
ListGrader tests
"""
from __future__ import division
import pprint
from pytest import approx, raises
from graders import *

pp = pprint.PrettyPrinter(indent=4)
printit = pp.pprint


def test_order_not_matter():
    grader = ListGrader(
        answers=['cat', 'dog', 'unicorn'],
        subgrader=StringGrader()
    )
    submission = ['cat', 'fish', 'dog']
    expected_result = {
        'overall_message': '',
        'input_list': [
            {'ok': True, 'grade_decimal': 1, 'msg': ''},
            {'ok': False, 'grade_decimal': 0, 'msg': ''},
            {'ok': True, 'grade_decimal': 1, 'msg': ''}
        ]
    }
    assert grader(None, submission) == expected_result

def test_shorthand_answers_specification():
    grader = ListGrader(
        answers=['cat', 'dog', 'unicorn'],
        subgrader=StringGrader()
    )
    submission = ['cat', 'fish', 'dog']
    expected_result = {
        'overall_message': '',
        'input_list': [
            {'ok': True, 'grade_decimal': 1, 'msg': ''},
            {'ok': False, 'grade_decimal': 0, 'msg': ''},
            {'ok': True, 'grade_decimal': 1, 'msg': ''}
        ]
    }
    assert grader(None, submission) == expected_result

def test_duplicate_items():
    grader = ListGrader(
        answers=['cat', 'dog', 'unicorn', 'cat', 'cat'],
        subgrader=StringGrader()
    )
    submission = ['cat', 'dog', 'dragon', 'dog', 'cat']
    expected_result = {
        'overall_message': '',
        'input_list': [
            {'ok': True, 'grade_decimal': 1, 'msg': ''},
            {'ok': True, 'grade_decimal': 1, 'msg': ''},
            {'ok': False, 'grade_decimal': 0, 'msg': ''},
            {'ok': False, 'grade_decimal': 0, 'msg': ''},
            {'ok': True, 'grade_decimal': 1, 'msg': ''}
        ]
    }
    assert grader(None, submission) == expected_result

def test_partial_credit_assigment():
    grader = ListGrader(
        answers=[
            (
                {'expect': 'tiger', 'grade_decimal': 1},
                {'expect': 'lion', 'grade_decimal': 0.5, 'msg': "lion_msg"}
            ),
            'skunk',
            (
                {'expect': 'zebra', 'grade_decimal': 1},
                {'expect': 'horse', 'grade_decimal': 0},
                {'expect': 'unicorn', 'grade_decimal': 0.75, 'msg': "unicorn_msg"}
            )
        ],
        subgrader=StringGrader()
    )
    submission = ["skunk", "lion", "unicorn"]
    expected_result = {
        'overall_message': '',
        'input_list': [
            {'ok': True, 'grade_decimal': 1, 'msg': ''},
            {'ok': 'partial', 'grade_decimal': 0.5, 'msg': 'lion_msg'},
            {'ok': 'partial', 'grade_decimal': 0.75, 'msg': 'unicorn_msg'}
        ]
    }
    assert grader(None, submission) == expected_result

def test_multiple_graders():
    """Test multiple graders"""
    grader = ListGrader(
        answers=['cat', '1'],
        subgrader=[StringGrader(), FormulaGrader()],
        ordered=True
    )

    # Test success
    submission = ['cat', '1']
    expected_result = {
        'overall_message': '',
        'input_list': [
            {'ok': True, 'grade_decimal': 1, 'msg': ''},
            {'ok': True, 'grade_decimal': 1, 'msg': ''}
        ]
    }
    result = grader(None, submission)
    assert result == expected_result

    # Test incorrect ordering
    submission = ['1', 'cat']
    with raises(UndefinedVariable) as err:
        result = grader(None, submission)
    assert err.value.args[0] == 'Invalid Input: cat not permitted in answer'

    # Test failure
    submission = ['dog', '2']
    expected_result = {
        'overall_message': '',
        'input_list': [
            {'ok': False, 'grade_decimal': 0, 'msg': ''},
            {'ok': False, 'grade_decimal': 0, 'msg': ''}
        ]
    }
    result = grader(None, submission)
    assert result == expected_result

def test_multiple_graders_errors():
    """Test that exceptions are raised on bad config"""
    # Wrong number of graders
    with raises(ConfigError) as err:
        grader = ListGrader(
            answers=['cat', '1'],
            subgrader=[StringGrader()],
            ordered=True
        )
    assert err.value.args[0] == 'The number of subgraders and answers are different'

    # Unordered entry
    with raises(ConfigError) as err:
        grader = ListGrader(
            answers=['cat', '1'],
            subgrader=[StringGrader(), StringGrader()],
            ordered=False
        )
    assert err.value.args[0] == 'Cannot use unordered lists with multiple graders'

def test_wrong_number_of_answers():
    """Check that an error is raised if number of answers != number of inputs"""
    with raises(ConfigError) as err:
        grader = ListGrader(
            answers=['cat', 'dog'],
            subgrader=StringGrader()
        )
        grader(None, ['cat'])
    expect = 'The number of answers (2) and the number of inputs (1) are different'
    assert err.value.args[0] == expect

def test_insufficient_answers():
    """Check that an error is raised if ListGrader is fed only one answer"""
    with raises(ConfigError) as err:
        ListGrader(
            answers=['cat'],
            subgrader=StringGrader()
        )
    assert err.value.args[0] == 'ListGrader does not work with a single answer'

def test_zero_answers():
    """Check that ListGrader instantiates without any answers supplied (used in nesting)"""
    ListGrader(
        answers=[],
        subgrader=StringGrader()
    )

def test_multiple_list_answers():
    """Check that a listgrader with multiple possible answers is graded correctly"""
    grader = ListGrader(
        answers=(['cat', 'meow'], ['dog', 'woof']),
        subgrader=StringGrader()
    )

    result = grader(None, ['cat', 'meow'])
    expected_result = {
        'overall_message': '',
        'input_list': [
            {'ok': True, 'grade_decimal': 1.0, 'msg': ''},
            {'ok': True, 'grade_decimal': 1.0, 'msg': ''}
        ]
    }
    assert result == expected_result

    result = grader(None, ['cat', 'woof'])
    expected_result = {
        'overall_message': '',
        'input_list': [
            {'ok': True, 'grade_decimal': 1.0, 'msg': ''},
            {'ok': False, 'grade_decimal': 0, 'msg': ''}
        ]
    }
    assert result == expected_result

    result = grader(None, ['dog', 'woof'])
    expected_result = {
        'overall_message': '',
        'input_list': [
            {'ok': True, 'grade_decimal': 1.0, 'msg': ''},
            {'ok': True, 'grade_decimal': 1.0, 'msg': ''}
        ]
    }
    assert result == expected_result

    result = grader(None, ['dog', 'meow'])
    expected_result = {
        'overall_message': '',
        'input_list': [
            {'ok': True, 'grade_decimal': 1.0, 'msg': ''},
            {'ok': False, 'grade_decimal': 0, 'msg': ''}
        ]
    }
    assert result == expected_result

    result = grader(None, ['badger', 'grumble'])
    expected_result = {
        'overall_message': '',
        'input_list': [
            {'ok': False, 'grade_decimal': 0, 'msg': ''},
            {'ok': False, 'grade_decimal': 0, 'msg': ''}
        ]
    }
    assert result == expected_result

def test_multiple_list_answers_same_grade():
    grader = ListGrader(
        answers=(
            [{'expect': 'dog', 'msg': 'dog1'}, 'woof'],
            ['cat', 'woof'],
            [{'expect': 'dog', 'msg': 'dog2'}, 'woof'],
            ['dolphin', 'squeak'],
        ),
        subgrader=StringGrader()
    )

    result = grader(None, ['dog', 'woof'])
    expected_result = {
        'overall_message': '',
        'input_list': [
            {'ok': True, 'grade_decimal': 1.0, 'msg': 'dog1'},
            {'ok': True, 'grade_decimal': 1.0, 'msg': ''}
        ]
    }
    printit(result)

    assert result == expected_result

def test_nested_listgrader():
    """Check that we can use nested listgraders on multiple single-input lists"""
    grader = ListGrader(
        answers=[
            ['1', '2'],
            ['3', '4']
        ],
        subgrader=SingleListGrader(
            subgrader=StringGrader()
        )
    )
    result = grader(None, ['1,2', '4,3'])
    expected_result = {
        'overall_message': '',
        'input_list': [
            {'ok': True, 'grade_decimal': 1, 'msg': ''},
            {'ok': True, 'grade_decimal': 1, 'msg': ''}
        ]
    }
    assert result == expected_result
