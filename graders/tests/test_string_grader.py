from __future__ import division
from .. import *

def test_single_expect_value_in_config():
    grader = StringGrader({
        'answers':['cat']
    })
    submission = 'dog'
    expected_result = {'msg': '', 'grade_decimal': 0, 'ok': False}
    assert grader(None, submission) == expected_result

def test_single_expect_value_in_config_and_passed_explicitly():
    grader = StringGrader({
        'answers':['cat']
    })
    submission = 'dog'
    expected_result = {'msg': '', 'grade_decimal': 0, 'ok': False}
    assert grader('cat', submission) == expected_result

def test_list_of_expect_values():
    grader = StringGrader({
        'answers':[
            {'expect':'zebra', 'grade_decimal':1},
            {'expect':'horse', 'grade_decimal':0.45},
            {'expect':'unicorn', 'grade_decimal':0, 'msg': "unicorn_msg"}
        ]
    })
    submission = 'horse'
    expected_result = {'msg': '', 'grade_decimal': 0.45, 'ok': 'partial'}
    assert grader(None, submission) == expected_result

def test_longer_message_wins_grade_ties():
    grader1 = StringGrader({
        'answers':[
            {'expect':'zebra', 'grade_decimal':1},
            {'expect':'horse', 'grade_decimal':0, 'msg':'short'},
            {'expect':'unicorn', 'grade_decimal':0, 'msg': "longer_msg"}
        ]
    })
    grader2 = StringGrader({
        'answers':[
            {'expect':'zebra', 'grade_decimal':1},
            {'expect':'unicorn', 'grade_decimal':0, 'msg': "longer_msg"},
            {'expect':'horse', 'grade_decimal':0, 'msg':'short'}
        ]
    })
    submission = 'unicorn'
    expected_result = {'msg': 'longer_msg', 'grade_decimal': 0, 'ok': False}
    result1 = grader1(None, submission)
    result2 = grader2(None, submission)
    assert result1 == result2 == expected_result