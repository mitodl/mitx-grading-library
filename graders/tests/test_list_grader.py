from __future__ import division
from .. import *

from pytest import approx

def test_order_not_matter_with_list_submission():
    grader = ListGrader({
        'answers_list': [['cat'], ['dog'], ['unicorn']],
        'item_grader': StringGrader()
    })
    submission = ['cat','fish','dog']
    expected_result = {
        'overall_message':'',
        'input_list':[
            {'ok':True , 'grade_decimal':1, 'msg':''},
            {'ok':False, 'grade_decimal':0, 'msg':''},
            {'ok':True , 'grade_decimal':1, 'msg':''}
        ]
    }
    assert grader(None, submission) == expected_result

def test_order_not_matter_with_string_submission():
    grader = ListGrader({
        'answers_list': [['cat'], ['dog'], ['unicorn']],
        'item_grader': StringGrader()
    })
    submission = "cat, fish, dog"
    expected_result = {
        'ok':'partial',
        'msg':'',
        'grade_decimal':2/3
    }
    assert grader(None, submission) == expected_result

def test_shorthand_answers_specification():
    grader = ListGrader({
        'answers_list': ['cat', 'dog', 'unicorn'],
        'item_grader': StringGrader()
    })
    submission = ['cat','fish','dog']
    expected_result = {
        'overall_message':'',
        'input_list':[
            {'ok':True , 'grade_decimal':1, 'msg':''},
            {'ok':False, 'grade_decimal':0, 'msg':''},
            {'ok':True , 'grade_decimal':1, 'msg':''}
        ]
    }
    assert grader(None, submission) == expected_result

def test_duplicate_items_with_list_submission():
    grader = ListGrader({
        'answers_list': [['cat'], ['dog'], ['unicorn'], ['cat'],['cat']],
        'item_grader': StringGrader()
    })
    submission = ['cat','dog', 'dragon','dog','cat']
    expected_result = {
        'overall_message':'',
        'input_list':[
            {'ok':True , 'grade_decimal':1, 'msg':''},
            {'ok':True , 'grade_decimal':1, 'msg':''},
            {'ok':False, 'grade_decimal':0, 'msg':''},
            {'ok':False, 'grade_decimal':0, 'msg':''},
            {'ok':True , 'grade_decimal':1, 'msg':''}
        ]
    }
    assert grader(None, submission) == expected_result

def test_partial_credit_assigment_with_list_submission():
    grader = ListGrader({
        'answers_list': [
            [
                {'expect':'tiger', 'grade_decimal':1},
                {'expect':'lion', 'grade_decimal':0.5, 'msg': "lion_msg"}
            ],
            ['skunk'],
            [
                {'expect':'zebra', 'grade_decimal':1},
                {'expect':'horse', 'grade_decimal':0},
                {'expect':'unicorn', 'grade_decimal':0.75, 'msg': "unicorn_msg"}
            ]
        ],
        'item_grader': StringGrader()
    })
    submission = ["skunk", "lion", "unicorn"]
    expected_result = {
        'overall_message':'',
        'input_list': [
            {'ok':True, 'grade_decimal':1, 'msg':''},
            {'ok':'partial','grade_decimal':0.5, 'msg':'lion_msg'},
            {'ok':'partial','grade_decimal':0.75, 'msg':'unicorn_msg'}
        ]
    }
    assert grader(None, submission) == expected_result

def test_partial_credit_assigment_with_string_submission():
    grader = ListGrader({
        'answers_list': [
            [
                {'expect':'tiger', 'grade_decimal':1},
                {'expect':'lion', 'grade_decimal':0.5, 'msg': "lion_msg"}
            ],
            ['skunk'],
            [
                {'expect':'zebra', 'grade_decimal':1},
                {'expect':'horse', 'grade_decimal':0},
                {'expect':'unicorn', 'grade_decimal':0.75, 'msg': "unicorn_msg"}
            ]
        ],
        'item_grader': StringGrader()
    })
    submission = "skunk, lion, unicorn"
    expected_result = {
        'ok':'partial',
        'msg': "lion_msg\nunicorn_msg",
        'grade_decimal':approx( (1+0.5+0.75)/3 )
    }
    assert grader(None, submission) == expected_result

def test_too_many_items_with_string_submission():
    grader = ListGrader({
        'answers_list': [
            [
                {'expect':'tiger', 'grade_decimal':1},
                {'expect':'lion', 'grade_decimal':0.5, 'msg': "lion_msg"}
            ],
            ['skunk'],
            [
                {'expect':'zebra', 'grade_decimal':1},
                {'expect':'horse', 'grade_decimal':0},
                {'expect':'unicorn', 'grade_decimal':0.75, 'msg': "unicorn_msg"}
            ],
        ],
        'item_grader': StringGrader()
    })
    submission = "skunk, fish, lion, unicorn, bear"
    expected_result = {
        'ok':'partial',
        'msg': "lion_msg\nunicorn_msg",
        'grade_decimal': approx( (1+0.5+0.75)/3 - 2*1/3 )
    }
    assert grader(None, submission) == expected_result

def test_way_too_many_items_reduces_score_to_zero_with_string_submission():
    grader = ListGrader({
        'answers_list': [
            [
                {'expect':'tiger', 'grade_decimal':1},
                {'expect':'lion', 'grade_decimal':0.5, 'msg': "lion_msg"}
            ],
            ['skunk'],
            [
                {'expect':'zebra', 'grade_decimal':1},
                {'expect':'horse', 'grade_decimal':0},
                {'expect':'unicorn', 'grade_decimal':0.75, 'msg': "unicorn_msg"}
            ],
        ],
        'item_grader': StringGrader()
    })
    submission = "skunk, fish, dragon, dog, lion, unicorn, bear"
    expected_result = {
        'ok':False,
        'msg': "lion_msg\nunicorn_msg",
        'grade_decimal': 0
    }
    assert grader(None, submission) == expected_result

def test_too_few_items_with_string_submission():
    grader = ListGrader({
        'answers_list': [
            [
                {'expect':'tiger', 'grade_decimal':1},
                {'expect':'lion', 'grade_decimal':0.5, 'msg': "lion_msg"}
            ],
            ['skunk'],
            [
                {'expect':'zebra', 'grade_decimal':1},
                {'expect':'horse', 'grade_decimal':0},
                {'expect':'unicorn', 'grade_decimal':0.75, 'msg': "unicorn_msg"}
            ]
        ],
        'item_grader': StringGrader()
    })
    submission = "skunk, unicorn"
    expected_result = {
        'ok':'partial',
        'msg': "unicorn_msg",
        'grade_decimal':approx( (1+0.75)/3 )
    }
    assert grader(None, submission) == expected_result
