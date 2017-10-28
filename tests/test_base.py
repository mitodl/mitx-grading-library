"""
Tests of base class functionality
"""
from __future__ import division
from mitxgraders import ListGrader, StringGrader, ConfigError, __version__
from mitxgraders.voluptuous import Error
from pytest import raises

def test_debug():
    """Test that debug information is correctly added to the response"""
    header = 'MITx Grading Library Version ' + __version__ + '\n'
    grader = StringGrader(
        answers=('cat', 'dog'),
        wrong_msg='nope!',
        debug=True
    )
    msg = 'nope!\n\n' + header + 'Student Response:\nhorse'
    expected_result = {'msg': msg, 'grade_decimal': 0, 'ok': False}
    assert grader(None, 'horse') == expected_result

    grader = StringGrader(
        answers=('cat', 'dog'),
        debug=True
    )
    expected_result = {'msg': header + 'Student Response:\ncat', 'grade_decimal': 1, 'ok': True}
    assert grader(None, 'cat') == expected_result

    grader = ListGrader(
        answers=['cat', 'dog', 'unicorn'],
        subgraders=StringGrader(),
        debug=True
    )
    expected_result = {
        'overall_message': header + 'Student Responses:\ncat\nfish\ndog',
        'input_list': [
            {'ok': True, 'grade_decimal': 1, 'msg': ''},
            {'ok': False, 'grade_decimal': 0, 'msg': ''},
            {'ok': True, 'grade_decimal': 1, 'msg': ''}
        ]
    }
    assert grader(None, ['cat', 'fish', 'dog']) == expected_result

def test_config():
    """Test giving a class a config dict or arguments"""
    assert StringGrader(answers="cat").config["answers"][0]['expect'] == "cat"
    assert StringGrader({'answers': 'cat'}).config["answers"][0]['expect'] == "cat"

def test_itemgrader():
    """Various tests of ItemGrader. We use StringGrader as a standin for ItemGrader"""
    # wrong_msg
    with raises(Error):
        StringGrader(wrong_msg=1)
    StringGrader(wrong_msg="message")

    # answers
    StringGrader(answers="cat")
    StringGrader(answers=("cat", "dog"))
    with raises(Error):
        StringGrader(answers=["cat", "dog"])
    StringGrader(answers={'expect': 'cat', 'grade_decimal': 0.2, 'ok': 'computed', 'msg': 'hi!'})
    StringGrader(answers=(
                 {'expect': 'cat', 'grade_decimal': 0.2, 'ok': 'computed', 'msg': 'hi!'},
                 {'expect': 'dog', 'grade_decimal': 1, 'ok': 'computed', 'msg': 'hi!'}
                 ))
    with raises(Error):
        StringGrader(answers={'grade_decimal': 0.2, 'ok': 'partial', 'msg': 'hi!'})
    with raises(Error):
        StringGrader(answers={'expect': 'cat', 'grade_decimal': -1, 'msg': 'hi!'})
    with raises(Error):
        StringGrader(answers={'expect': 'cat', 'ok': 'wrong', 'msg': 'hi!'})
    with raises(Error):
        StringGrader(answers={'expect': 'cat', 'msg': 5.5})
    with raises(Error):
        StringGrader(answers={'expect': 5.5})

    # Grading
    with raises(ConfigError, match="Expected at least one answer in answers"):
        grader = StringGrader(answers=())
        grader(None, "hello")
    with raises(ConfigError, match="Expected string for student_input, received <type 'int'>"):
        grader = StringGrader(answers="hello")
        grader(None, 5)

    grader = StringGrader(answers=("1", "2"))
    assert grader(None, "1")['ok']
    assert grader(None, "2")['ok']
    assert not grader(None, "3")['ok']

def test_single_expect_value_in_config():
    grader = StringGrader(
        answers='cat'
    )
    submission = 'dog'
    expected_result = {'msg': '', 'grade_decimal': 0, 'ok': False}
    assert grader(None, submission) == expected_result

def test_single_expect_value_in_config_and_passed_explicitly():
    grader = StringGrader(
        answers='cat'
    )
    submission = 'dog'
    expected_result = {'msg': '', 'grade_decimal': 0, 'ok': False}
    assert grader('cat', submission) == expected_result

def test_two_expect_values_in_config():
    grader = StringGrader(
        answers=('cat', 'horse')
    )
    submission = 'horse'
    expected_result = {'msg': '', 'grade_decimal': 1, 'ok': True}
    assert grader(None, submission) == expected_result

def test_list_of_expect_values():
    grader = StringGrader(
        answers=(
            {'expect': 'zebra', 'grade_decimal': 1},
            {'expect': 'horse', 'grade_decimal': 0.45},
            {'expect': 'unicorn', 'grade_decimal': 0, 'msg': "unicorn_msg"}
        )
    )
    submission = 'horse'
    expected_result = {'msg': '', 'grade_decimal': 0.45, 'ok': 'partial'}
    assert grader(None, submission) == expected_result

def test_longer_message_wins_grade_ties():
    grader1 = StringGrader(
        answers=(
            {'expect': 'zebra', 'grade_decimal': 1},
            {'expect': 'horse', 'grade_decimal': 0, 'msg': 'short'},
            {'expect': 'unicorn', 'grade_decimal': 0, 'msg': "longer_msg"}
        )
    )
    grader2 = StringGrader(
        answers=(
            {'expect': 'zebra', 'grade_decimal': 1},
            {'expect': 'unicorn', 'grade_decimal': 0, 'msg': "longer_msg"},
            {'expect': 'horse', 'grade_decimal': 0, 'msg': 'short'}
        )
    )
    submission = 'unicorn'
    expected_result = {'msg': 'longer_msg', 'grade_decimal': 0, 'ok': False}
    result1 = grader1(None, submission)
    result2 = grader2(None, submission)
    assert result1 == result2 == expected_result
