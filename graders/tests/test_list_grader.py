from __future__ import division
from .. import *

from pytest import approx, raises
import pprint

pp = pprint.PrettyPrinter(indent=4)
printit = pp.pprint

def test_order_not_matter_with_list_submission():
    grader = ListGrader({
        'answers': ['cat', 'dog', 'unicorn'],
        'subgrader': StringGrader()
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
        'answers': ['cat', 'dog', 'unicorn'],
        'subgrader': StringGrader()
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
        'answers': ['cat', 'dog', 'unicorn'],
        'subgrader': StringGrader()
    })
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

def test_duplicate_items_with_list_submission():
    grader = ListGrader({
        'answers': ['cat', 'dog', 'unicorn', 'cat', 'cat'],
        'subgrader': StringGrader()
    })
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

def test_partial_credit_assigment_with_list_submission():
    grader = ListGrader({
        'answers': [
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
        'subgrader': StringGrader()
    })
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

def test_partial_credit_assigment_with_string_submission():
    grader = ListGrader({
        'answers': [
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
        'subgrader': StringGrader()
    })
    submission = "skunk, lion, unicorn"
    expected_result = {
        'ok': 'partial',
        'msg': "lion_msg\nunicorn_msg",
        'grade_decimal': approx( (1+0.5+0.75)/3 )
    }
    assert grader(None, submission) == expected_result

def test_too_many_items_with_string_submission():
    grader = ListGrader({
        'answers': [
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
        'subgrader': StringGrader(),
        'length_error': False
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
        'answers': [
            (
                {'expect':'tiger', 'grade_decimal':1},
                {'expect':'lion', 'grade_decimal':0.5, 'msg': "lion_msg"}
            ),
            'skunk',
            (
                {'expect':'zebra', 'grade_decimal':1},
                {'expect':'horse', 'grade_decimal':0},
                {'expect':'unicorn', 'grade_decimal':0.75, 'msg': "unicorn_msg"}
            ),
        ],
        'subgrader': StringGrader(),
        'length_error': False
    })
    submission = "skunk, fish, dragon, dog, lion, unicorn, bear"
    expected_result = {
        'ok': False,
        'msg': "lion_msg\nunicorn_msg",
        'grade_decimal': 0
    }
    assert grader(None, submission) == expected_result

def test_too_few_items_with_string_submission():
    grader = ListGrader({
        'answers': [
            (
                {'expect':'tiger', 'grade_decimal':1},
                {'expect':'lion', 'grade_decimal':0.5, 'msg': "lion_msg"}
            ),
            ('skunk'),
            (
                {'expect':'zebra', 'grade_decimal':1},
                {'expect':'horse', 'grade_decimal':0},
                {'expect':'unicorn', 'grade_decimal':0.75, 'msg': "unicorn_msg"}
            )
        ],
        'subgrader': StringGrader(),
        'length_error': False
    })
    submission = "skunk, unicorn"
    expected_result = {
        'ok':'partial',
        'msg': "unicorn_msg",
        'grade_decimal':approx( (1+0.75)/3 )
    }
    assert grader(None, submission) == expected_result

def test_wrong_length_string_submission():
    grader = ListGrader({
        'answers': ["cat", "dog"],
        'subgrader': StringGrader(),
        'length_error': True
    })
    with raises(ValueError) as excinfo:
        result = grader(None, 'cat,dog,dragon')
    assert excinfo.value.args[0] == 'List length error: Expected 2 terms in the list, but received 3'

    with raises(ValueError) as excinfo:
        result = grader(None, 'cat')
    assert excinfo.value.args[0] == 'List length error: Expected 2 terms in the list, but received 1'

def test_multiple_graders():
    """Test multiple graders"""
    grader = ListGrader({
        'answers': ['cat', '1'],
        'subgrader': [StringGrader(), FormulaGrader()],
        'ordered': True
    })

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
    with raises(UndefinedVariable) as excinfo:
        result = grader(None, submission)
    assert excinfo.value.args[0] == 'Invalid Input: cat not permitted in answer'

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
    with raises(ConfigError) as excinfo:
        grader = ListGrader({
            'answers': ['cat', '1'],
            'subgrader': [StringGrader()],
            'ordered': True
        })
    assert excinfo.value.args[0] == 'The number of subgraders and answers are different'

    # Unordered entry
    with raises(ConfigError) as excinfo:
        grader = ListGrader({
            'answers': ['cat', '1'],
            'subgrader': [StringGrader(), StringGrader()],
            'ordered': False
        })
    assert excinfo.value.args[0] == 'Cannot use unordered lists with multiple graders'

    # Multiple graders on single input
    with raises(ConfigError) as excinfo:
        grader = ListGrader({
            'answers': ['cat', '1'],
            'subgrader': [StringGrader(), StringGrader()],
            'ordered': True
        })
        result = grader(None, 'cat,1')
    assert excinfo.value.args[0] == 'Multiple subgraders cannot be used for single input lists'

def test_wrong_number_of_answers():
    """Check that an error is raised if number of answers != number of inputs"""
    with raises(ConfigError) as excinfo:
        grader = ListGrader({
            'answers': ['cat', 'dog'],
            'subgrader': StringGrader()
        })
        result = grader(None, ['cat'])
    assert excinfo.value.args[0] == 'The number of answers (2) and the number of inputs (1) are different'

def test_insufficient_answers():
    """Check that an error is raised if ListGrader is fed only one answer"""
    with raises(ConfigError) as excinfo:
        grader = ListGrader({
            'answers': ['cat'],
            'subgrader': StringGrader()
        })
    assert excinfo.value.args[0] == 'ListGrader does not work with a single answer'

def test_zero_answers():
    """Check that ListGrader instantiates without any answers supplied (used in nesting)"""
    grader = ListGrader({
        'answers': [],
        'subgrader': StringGrader()
    })
