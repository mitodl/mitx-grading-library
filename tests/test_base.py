"""
Tests of base class functionality
"""
from graders import ListGrader, StringGrader, __version__

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
