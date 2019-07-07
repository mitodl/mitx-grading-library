"""
Tests of base class functionality
"""
from __future__ import print_function, division, absolute_import

import sys
import six
from imp import reload
from pytest import raises, approx
from voluptuous import Error
import mitxgraders
from mitxgraders import ListGrader, StringGrader, ConfigError, FormulaGrader, __version__
from mitxgraders.baseclasses import AbstractGrader
from mitxgraders.exceptions import MITxError, StudentFacingError
from tests.helpers import mock

def test_debug_with_author_message():
    grader = StringGrader(
        answers=('cat', 'dog'),
        wrong_msg='nope!',
        debug=True
    )
    student_response = "horse"
    template = ("{author_message}\n\n"
                "<pre>"
                "MITx Grading Library Version {version}\n"
                "{debug_content}"
                "</pre>")
    author_message = "nope!"
    debug_content = "Student Response:\nhorse"
    msg = template.format(author_message=author_message,
                          version=__version__,
                          debug_content=debug_content
                          ).replace("\n", "<br/>\n")
    expected_result = {'msg': msg, 'grade_decimal': 0, 'ok': False}
    assert grader(None, student_response) == expected_result

def test_debug_without_author_message():
    grader = StringGrader(
        answers=('cat', 'dog'),
        debug=True
    )
    student_response = "horse"
    template = ("<pre>"
                "MITx Grading Library Version {version}\n"
                "{debug_content}"
                "</pre>")
    debug_content = "Student Response:\nhorse"
    msg = template.format(version=__version__,
                          debug_content=debug_content
                         ).replace("\n", "<br/>\n")
    expected_result = {'msg': msg, 'grade_decimal': 0, 'ok': False}
    assert grader(None, student_response) == expected_result

def test_debug_with_input_list():
    grader = ListGrader(
        answers=['cat', 'dog', 'unicorn'],
        subgraders=StringGrader(),
        debug=True
    )
    student_response = ["cat", "fish", "dog"]
    template = ("<pre>"
                "MITx Grading Library Version {version}\n"
                "{debug_content}"
                "</pre>")
    debug_content = "Student Responses:\ncat\nfish\ndog"
    msg = template.format(version=__version__,
                          debug_content=debug_content
                         ).replace("\n", "<br/>\n")
    expected_result = {
        'overall_message': msg,
        'input_list': [
            {'ok': True, 'grade_decimal': 1, 'msg': ''},
            {'ok': False, 'grade_decimal': 0, 'msg': ''},
            {'ok': True, 'grade_decimal': 1, 'msg': ''}
        ]
    }
    assert grader(None, student_response) == expected_result

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
    with raises(ConfigError, match="Expected string for student_input, received {int}".format(int=int)):
        grader = StringGrader(answers="hello")
        grader(None, 5)

    grader = StringGrader(answers=("1", "2"))
    assert grader(None, "1")['ok']
    assert grader(None, "2")['ok']
    assert not grader(None, "3")['ok']

def test_itemgrader_infers_answers_from_expect():
    grader = StringGrader()
    expect = 'cat'
    student_input_1 = 'cat'
    student_input_2 = 'dog'
    assert grader(expect, student_input_1)['ok']
    assert not grader(expect, student_input_2)['ok']

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

def test_docs():
    """Test the documentation examples"""
    grader = StringGrader(
        answers='cat',
        wrong_msg='Try again!'
    )
    assert grader(None, 'cat')['ok']

    grader = StringGrader(
        answers={'expect': 'zebra', 'ok': True, 'grade_decimal': 1, 'msg': 'Yay!'},
        wrong_msg='Try again!'
    )
    expected_result = {'msg': 'Yay!', 'grade_decimal': 1, 'ok': True}
    assert grader(None, 'zebra') == expected_result
    expected_result = {'msg': 'Try again!', 'grade_decimal': 0, 'ok': False}
    assert grader(None, 'horse') == expected_result

    grader = StringGrader(
        answers='cat',
        # Equivalent to:
        # answers={'expect': 'cat', 'msg': '', 'grade_decimal': 1, 'ok': True}
        wrong_msg='Try again!'
    )
    expected_result = {'msg': '', 'grade_decimal': 1, 'ok': True}
    assert grader(None, 'cat') == expected_result

    grader = StringGrader(
        answers=(
            # the correct answer
            'wolf',
            # an alternative correct answer
            'canis lupus',
            # a partially correct answer
            {'expect': 'dog', 'grade_decimal': 0.5, 'msg': 'No, not dog!'},
            # a wrong answer with specific feedback
            {'expect': 'unicorn', 'grade_decimal': 0, 'msg': 'No, not unicorn!'}
        ),
        wrong_msg='Try again!'
    )
    expected_result = {'msg': '', 'grade_decimal': 1, 'ok': True}
    assert grader(None, 'wolf') == expected_result
    assert grader(None, 'canis lupus') == expected_result
    expected_result = {'msg': 'No, not dog!', 'grade_decimal': 0.5, 'ok': 'partial'}
    assert grader(None, 'dog') == expected_result
    expected_result = {'msg': 'No, not unicorn!', 'grade_decimal': 0, 'ok': False}
    assert grader(None, 'unicorn') == expected_result

def test_readme():
    """Tests that the README.md file examples work"""
    grader = StringGrader(
        answers='cat'
    )

    grader = ListGrader(
        answers=['1', '2'],
        subgraders=FormulaGrader()
    )

    del grader

def test_voluptuous_import_error_message():
    with mock.patch.dict(sys.modules, {'voluptuous': None}):
        msg = ("External dependency 'voluptuous' not found;"
               " see https://github.com/mitodl/mitx-grading-library#faq")
        with raises(ImportError, match=msg):
            # importing is not good enough to raise the error; need to reload
            # because conftest.py already imported voluptuous
            reload(mitxgraders)

def test_error_handing():
    class MockGrader(AbstractGrader):

        @property
        def schema_config(self):
            return super(MockGrader, self).schema_config.extend({
                'error': Exception
            })

        def check(self, answers, student_input):
            """student_input should be an exception"""
            raise self.config['error']

    # MITxErrors are caught, with some simple format replacements
    with raises(MITxError, match='Rats!<br/>Bats!'):
        grader = MockGrader(error=MITxError('Rats!\nBats!'))
        grader(None, 'Cats!')

    # other errors produce a generic output...
    with raises(StudentFacingError, match="Invalid Input: Could not check input 'Cats!'"):
        grader = MockGrader(error=ValueError('Rats!\nBats!'))
        grader(None, 'Cats!')

    # ...except in debug mode
    with raises(ValueError, match="Rats!\nBats!"):
        grader = MockGrader(debug=True, error=ValueError('Rats!\nBats!'))
        grader(None, 'Cats!')

    # Check generic multiput error.
    match = "Invalid Input: Could not check inputs 'Cats!', 'Gnats!'"
    with raises(StudentFacingError, match=match):
        grader = MockGrader(error=ValueError('Rats!\nBats!'))
        grader(None, ['Cats!', 'Gnats!'])

def test_ensure_text_inputs():
    ensure_text_inputs = AbstractGrader.ensure_text_inputs

    # Lists are ok
    valid_inputs = ['cat', six.u('dog')]
    if six.PY2:
        assert not isinstance(valid_inputs[0], six.text_type)
        assert isinstance(valid_inputs[1], six.text_type)
    result = ensure_text_inputs(valid_inputs)
    assert all(map(six.text_type, result))

    # single text is ok
    assert isinstance(ensure_text_inputs('cat'), six.text_type)
    assert isinstance(ensure_text_inputs(six.u('cat')), six.text_type)

    # empty lists are ok:
    assert ensure_text_inputs([]) == []

def test_ensure_text_inputs_errors():
    ensure_text_inputs = AbstractGrader.ensure_text_inputs

    msg = ("The student_input passed to a grader should be:\n"
           " - a text string for problems with a single input box\n"
           " - a list of text strings for problems with multiple input boxes\n"
           "Received student_input of {}").format(int)
    with raises(ConfigError, match=msg):
        ensure_text_inputs(5)

    msg = ("Expected student_input to be a list of text strings, but "
           "received {}").format(int)
    with raises(ConfigError, match=msg):
        ensure_text_inputs(5, allow_single=False)

    msg = ("Expected a list of text strings for student_input, but "
           "item at position 1 has {}").format(int)
    with raises(ConfigError, match=msg):
        ensure_text_inputs(['cat', 5], allow_single=False)

    msg = "Expected string for student_input, received {}".format(int)
    with raises(ConfigError,  match=msg):
        ensure_text_inputs(5, allow_lists=False)

    msg = r"At least one of \(allow\_lists, allow\_single\) must be True."
    with raises(ValueError,  match=msg):
        ensure_text_inputs('cat', allow_lists=False, allow_single=False)

def test_attempt_based_grading_single():
    # Test basic usage
    grader = StringGrader(
        answers='cat',
        attempt_based_credit=True,
        decrease_credit_after=3,
        decrease_credit_steps=3,
        minimum_credit=0.1,
        attempt_based_credit_msg=False
    )

    expected_result = {'msg': '', 'grade_decimal': 1, 'ok': True}
    for i in range(0, 4):  # Includes edX error case: attempt = 0
        assert grader(None, 'cat', attempt=i) == expected_result

    grade = 1
    for i in range(4, 7):
        grade -= 0.3
        expected_result = {'msg': '', 'grade_decimal': None, 'ok': 'partial'}
        result = grader(None, 'cat', attempt=i)
        assert result['msg'] == expected_result['msg']
        assert result['ok'] == expected_result['ok']
        assert result['grade_decimal'] == approx(grade)

    for i in range(7, 10):
        expected_result = {'msg': '', 'grade_decimal': 0.1, 'ok': 'partial'}
        result = grader(None, 'cat', attempt=i)
        assert result['msg'] == expected_result['msg']
        assert result['ok'] == expected_result['ok']
        assert result['grade_decimal'] == approx(0.1)

    # Test individual flags
    # Ensure it turns off properly
    grader = StringGrader(
        answers='cat',
        attempt_based_credit=False
    )

    expected_result = {'msg': '', 'grade_decimal': 1, 'ok': True}
    for i in range(1, 10):
        assert grader(None, 'cat', attempt=i) == expected_result

    # Ensure that wrong answers are always zeros
    grader = StringGrader(
        answers='cat',
        attempt_based_credit=True
    )

    expected_result = {'msg': '', 'grade_decimal': 0, 'ok': False}
    for i in range(1, 10):
        assert grader(None, 'dog', attempt=i) == expected_result

    # Ensure that zero credit is graded as false appropriately
    grader = StringGrader(
        answers='cat',
        attempt_based_credit=True,
        minimum_credit=0,
        attempt_based_credit_msg=False
    )

    expected_result = {'msg': '', 'grade_decimal': 0, 'ok': False}
    for i in range(10, 20):
        assert grader(None, 'cat', attempt=i) == expected_result

    # Ensure that messages are included as appropriate
    grader = StringGrader(
        answers='cat',
        attempt_based_credit=True,
        minimum_credit=0,
        decrease_credit_after=1,
        decrease_credit_steps=2,
        attempt_based_credit_msg=True
    )

    expected_result = {'msg': '', 'grade_decimal': 1, 'ok': True}
    assert grader(None, 'cat', attempt=1) == expected_result
    expected_result = {'msg': '', 'grade_decimal': 0, 'ok': False}
    assert grader(None, 'dog', attempt=1) == expected_result

    expected_result = {'msg': 'Maximum credit for attempt #2 is 0.50.', 'grade_decimal': 0.5, 'ok': 'partial'}
    assert grader(None, 'cat', attempt=2) == expected_result
    expected_result = {'msg': '', 'grade_decimal': 0, 'ok': False}
    assert grader(None, 'dog', attempt=2) == expected_result

    expected_result = {'msg': 'Maximum credit for attempt #3 is 0.00.', 'grade_decimal': 0, 'ok': False}
    assert grader(None, 'cat', attempt=3) == expected_result
    expected_result = {'msg': '', 'grade_decimal': 0, 'ok': False}
    assert grader(None, 'dog', attempt=3) == expected_result

    # Ensure that messages are appended as appropriate
    grader = StringGrader(
        answers={'expect': 'cat', 'msg': 'Meow!'},
        attempt_based_credit=True,
        minimum_credit=0,
        decrease_credit_after=1,
        decrease_credit_steps=2,
        attempt_based_credit_msg=True,
        wrong_msg='too bad'
    )

    expected_result = {'msg': 'Meow!', 'grade_decimal': 1, 'ok': True}
    assert grader(None, 'cat', attempt=1) == expected_result
    expected_result = {'msg': 'too bad', 'grade_decimal': 0, 'ok': False}
    assert grader(None, 'dog', attempt=1) == expected_result

    expected_result = {'msg': 'Meow!<br/>\n<br/>\nMaximum credit for attempt #2 is 0.50.', 'grade_decimal': 0.5, 'ok': 'partial'}
    assert grader(None, 'cat', attempt=2) == expected_result
    expected_result = {'msg': 'too bad', 'grade_decimal': 0, 'ok': False}
    assert grader(None, 'dog', attempt=2) == expected_result

    expected_result = {'msg': 'Meow!<br/>\n<br/>\nMaximum credit for attempt #3 is 0.00.', 'grade_decimal': 0, 'ok': False}
    assert grader(None, 'cat', attempt=3) == expected_result
    expected_result = {'msg': 'too bad', 'grade_decimal': 0, 'ok': False}
    assert grader(None, 'dog', attempt=3) == expected_result

    # Ensure that things behave when an attempt number is not passed in
    grader = StringGrader(
        answers='cat',
        attempt_based_credit=True
    )

    expected_result = {'msg': '', 'grade_decimal': 1, 'ok': True}
    assert grader(None, 'cat') == expected_result

    grader = StringGrader(
        answers='cat',
        attempt_based_credit=True,
        debug=True
    )

    template = ("<pre>"
                "MITx Grading Library Version {version}\n"
                "{debug_content}\n"
                "Attempt-based credit requested, but attempt number not passed through to grader"
                "</pre>")
    debug_content = "Student Response:\ncat"
    msg = template.format(version=__version__,
                          debug_content=debug_content
                          ).replace("\n", "<br/>\n")
    expected_result = {'msg': msg, 'grade_decimal': 1, 'ok': True}
    assert grader(None, 'cat') == expected_result

    # Ensure that debug info is passed along
    grader = StringGrader(
        answers='cat',
        attempt_based_credit=True,
        debug=True
    )

    template = ("<pre>"
                "MITx Grading Library Version {version}\n"
                "{debug_content}\n"
                "{attempt_msg}"
                "</pre>")
    debug_content = "Student Response:\ncat"
    attempt_msg = 'Attempt number 1'
    msg = template.format(version=__version__,
                          debug_content=debug_content,
                          attempt_msg=attempt_msg).replace("\n", "<br/>\n")
    expected_result = {'msg': msg, 'grade_decimal': 1, 'ok': True}
    assert grader(None, 'cat', attempt=1) == expected_result

    template = ("Maximum credit for attempt #3 is 0.60.\n\n<pre>"
                "MITx Grading Library Version {version}\n"
                "{debug_content}\n"
                "{attempt_msg}"
                "</pre>")
    attempt_msg = 'Attempt number 3\nMaximum credit is 0.6'
    msg = template.format(version=__version__,
                          debug_content=debug_content,
                          attempt_msg=attempt_msg).replace("\n", "<br/>\n")
    expected_result = {'msg': msg, 'grade_decimal': 0.6, 'ok': 'partial'}
    assert grader(None, 'cat', attempt=3) == expected_result

def test_attempt_based_grading_list():
    grader = ListGrader(
        answers=['cat', 'dog'],
        subgraders=StringGrader(),
        attempt_based_credit=True,
    )

    expected_result = {
        'overall_message': '',
        'input_list': [
            {'ok': True, 'grade_decimal': 1, 'msg': ''},
            {'ok': True, 'grade_decimal': 1, 'msg': ''}
        ]
    }
    assert grader(None, ['cat', 'dog'], attempt=1) == expected_result

    expected_result = {
        'overall_message': 'Maximum credit for attempt #5 is 0.20.',
        'input_list': [
            {'ok': 'partial', 'grade_decimal': 0.2, 'msg': ''},
            {'ok': 'partial', 'grade_decimal': 0.2, 'msg': ''}
        ]
    }
    assert grader(None, ['cat', 'dog'], attempt=5) == expected_result

    expected_result = {
        'overall_message': 'Maximum credit for attempt #5 is 0.20.',
        'input_list': [
            {'ok': 'partial', 'grade_decimal': 0.2, 'msg': ''},
            {'ok': False, 'grade_decimal': 0, 'msg': ''}
        ]
    }
    assert grader(None, ['cat', 'unicorn'], attempt=5) == expected_result
