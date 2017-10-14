"""
Tests for SingleListGrader
"""
from __future__ import division
import pprint
from pytest import approx, raises
from graders import *

pp = pprint.PrettyPrinter(indent=4)
printit = pp.pprint


def test_order_not_matter():
    grader = SingleListGrader(
        answers=['cat', 'dog', 'unicorn'],
        subgrader=StringGrader()
    )
    submission = "cat, fish, dog"
    expected_result = {
        'ok': 'partial',
        'msg': '',
        'grade_decimal': 2/3
    }
    assert grader(None, submission) == expected_result

def test_partial_credit_assigment():
    grader = SingleListGrader(
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
    submission = "skunk, lion, unicorn"
    expected_result = {
        'ok': 'partial',
        'msg': "lion_msg\nunicorn_msg",
        'grade_decimal': approx((1+0.5+0.75)/3)
    }
    assert grader(None, submission) == expected_result

def test_partial_credit_override():
    grader0 = SingleListGrader(
        answers=['moose', 'eagle'],
        partial_credit=False,
        subgrader=StringGrader()
    )
    grader1 = SingleListGrader(
        answers=['moose', 'eagle'],
        subgrader=StringGrader()
    )
    submission = "hawk, moose"
    expected_result0 = {
        'ok': False,
        'grade_decimal': 0,
        'msg': ''
    }
    expected_result1 = {
        'ok': 'partial',
        'grade_decimal': 0.5,
        'msg': ''
    }
    assert grader0(None, submission) == expected_result0
    assert grader1(None, submission) == expected_result1

def test_too_many_items():
    grader = SingleListGrader(
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
            ),
        ],
        subgrader=StringGrader(),
        length_error=False
    )
    submission = "skunk, fish, lion, unicorn, bear"
    expected_result = {
        'ok': 'partial',
        'msg': "lion_msg\nunicorn_msg",
        'grade_decimal': approx((1+0.5+0.75)/3 - 2*1/3)
    }
    assert grader(None, submission) == expected_result

def test_way_too_many_items_reduces_score_to_zero():
    grader = SingleListGrader(
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
            ),
        ],
        subgrader=StringGrader(),
        length_error=False
    )
    submission = "skunk, fish, dragon, dog, lion, unicorn, bear"
    expected_result = {
        'ok': False,
        'msg': "lion_msg\nunicorn_msg",
        'grade_decimal': 0
    }
    assert grader(None, submission) == expected_result

def test_too_few_items():
    grader = SingleListGrader(
        answers=[
            (
                {'expect': 'tiger', 'grade_decimal': 1},
                {'expect': 'lion', 'grade_decimal': 0.5, 'msg': "lion_msg"}
            ),
            ('skunk'),
            (
                {'expect': 'zebra', 'grade_decimal': 1},
                {'expect': 'horse', 'grade_decimal': 0},
                {'expect': 'unicorn', 'grade_decimal': 0.75, 'msg': "unicorn_msg"}
            )
        ],
        subgrader=StringGrader(),
        length_error=False
    )
    submission = "skunk, unicorn"
    expected_result = {
        'ok': 'partial',
        'msg': "unicorn_msg",
        'grade_decimal': approx((1+0.75)/3)
    }
    assert grader(None, submission) == expected_result

def test_wrong_length_string_submission():
    grader = SingleListGrader(
        answers=["cat", "dog"],
        subgrader=StringGrader(),
        length_error=True
    )
    with raises(ValueError) as err:
        grader(None, 'cat,dog,dragon')
    assert err.value.args[0] == 'List length error: Expected 2 terms in the list, but received 3. Separate items with character ","'

    with raises(ValueError) as err:
        grader(None, 'cat')
    assert err.value.args[0] == 'List length error: Expected 2 terms in the list, but received 1. Separate items with character ","'

def test_multiple_list_answers():
    """
    Check that a SingleListGrader with multiple possible answers is graded correctly
    """
    grader = SingleListGrader(
        answers=(['cat', 'meow'], ['dog', 'woof']),
        subgrader=StringGrader()
    )

    expected_result = {'ok': True, 'msg': '', 'grade_decimal': 1}
    result = grader(None, 'cat,meow')
    assert result == expected_result

    expected_result = {'ok': 'partial', 'msg': '', 'grade_decimal': 0.5}
    result = grader(None, 'cat,woof')
    assert result == expected_result

    expected_result = {'ok': True, 'msg': '', 'grade_decimal': 1}
    result = grader(None, 'dog,woof')
    assert result == expected_result

    expected_result = {'ok': 'partial', 'msg': '', 'grade_decimal': 0.5}
    result = grader(None, 'dog,meow')
    assert result == expected_result

    expected_result = {'ok': False, 'msg': '', 'grade_decimal': 0}
    result = grader(None, 'badger,grumble')
    assert result == expected_result

def test_nesting():
    grader = SingleListGrader(
        answers = [['a', 'b'], ['c', 'd']],
        subgrader = SingleListGrader(
            subgrader=StringGrader()
        ),
        delimiter=';'
    )
    student_input = 'a, b; c, d'
    expected_result = {
        'ok':True,
        'msg':'',
        'grade_decimal':1
    }
    assert grader(None, student_input) == expected_result

def test_nesting_with_same_delimiter_raises_config_error():
    with raises(ConfigError) as err:
        # Both delimiters have same default value
        grader = SingleListGrader(
            answers = [['a', 'b'], ['c', 'd']],
            subgrader = SingleListGrader(
                subgrader=StringGrader()
            )
        )
    assert err.value.args[0] == "Nested SingleListGraders must use different delimiters."
