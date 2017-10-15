"""
Tests of base class functionality
"""
from graders import ListGrader, StringGrader

def test_debug():
    """Test that debug information is correctly added to the response"""
    grader = StringGrader(
        answers=('cat', 'dog'),
        wrong_msg='nope!',
        debug=True
    )
    expected_result = {'msg': 'nope!\n\nStudent Response:\nhorse', 'grade_decimal': 0, 'ok': False}
    assert grader(None, 'horse') == expected_result

    grader = StringGrader(
        answers=('cat', 'dog'),
        debug=True
    )
    expected_result = {'msg': 'Student Response:\ncat', 'grade_decimal': 1, 'ok': True}
    assert grader(None, 'cat') == expected_result

    grader = ListGrader(
        answers=['cat', 'dog', 'unicorn'],
        subgrader=StringGrader(),
        debug=True
    )
    expected_result = {
        'overall_message': 'Student Responses:\ncat\nfish\ndog',
        'input_list': [
            {'ok': True, 'grade_decimal': 1, 'msg': ''},
            {'ok': False, 'grade_decimal': 0, 'msg': ''},
            {'ok': True, 'grade_decimal': 1, 'msg': ''}
        ]
    }
    assert grader(None, ['cat', 'fish', 'dog']) == expected_result
