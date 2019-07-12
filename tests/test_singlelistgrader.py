"""
Tests for SingleListGrader
"""
from __future__ import print_function, division, absolute_import

import pprint
from pytest import approx, raises
from mitxgraders import ConfigError, StringGrader, SingleListGrader, FormulaGrader, congruence_comparer
from mitxgraders.exceptions import MissingInput

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
        'msg': ("lion_msg<br/>\n"
                "unicorn_msg"),
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
        'msg': ("lion_msg<br/>\n"
                "unicorn_msg"),
        'grade_decimal': approx((1+0.5+0.75)/3 - 2*1/3)
    }
    assert grader(None, submission) == expected_result

def test_ordered_wrong_number():
    grader = SingleListGrader(
        answers=["tiger", "skunk"],
        subgrader=StringGrader(),
        length_error=False
    )
    assert grader(None, "tiger, skunk, horse")["grade_decimal"] == 0.5
    assert grader(None, "tiger")["grade_decimal"] == 0.5

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
        'msg': ("lion_msg<br/>\n"
                "unicorn_msg"),
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
    expect = 'List length error: Expected 2 terms in the list, but received 3. ' + \
             'Separate items with character ","'
    with raises(MissingInput, match=expect):
        grader(None, 'cat,dog,dragon')

    expect = 'List length error: Expected 2 terms in the list, but received 1. ' + \
             'Separate items with character ","'
    with raises(MissingInput, match=expect):
        grader(None, 'cat')

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
        answers=[['a', 'b'], ['c', 'd']],
        subgrader=SingleListGrader(
            subgrader=StringGrader()
        ),
        delimiter=';'
    )
    student_input = 'a, b; c, d'
    expected_result = {
        'ok': True,
        'msg': '',
        'grade_decimal': 1
    }
    assert grader(None, student_input) == expected_result

def test_nesting_with_same_delimiter_raises_config_error():
    with raises(ConfigError, match="Nested SingleListGraders must use different delimiters."):
        # Both delimiters have same default value
        SingleListGrader(
            subgrader=SingleListGrader(
                subgrader=StringGrader()
            )
        )

    # Why you would do this is beyond me, but hey, we can test it!
    with raises(ConfigError, match="Nested SingleListGraders must use different delimiters."):
        SingleListGrader(
            subgrader=SingleListGrader(
                subgrader=SingleListGrader(
                    subgrader=SingleListGrader(
                        subgrader=StringGrader(),
                        delimiter=','
                    ),
                    delimiter='-'
                ),
                delimiter=';'
            ),
            delimiter=','
        )

def test_order_matters():
    grader = SingleListGrader(
        answers=['cat', 'dog', 'fish'],
        subgrader=StringGrader(),
        ordered=True
    )
    submission = "cat, fish, moose"
    expected_result = {
        'ok': 'partial',
        'msg': '',
        'grade_decimal': 1/3
    }
    assert grader(None, submission) == expected_result

def test_docs():
    """Make sure that the documentation examples work as expected"""
    grader = SingleListGrader(
        answers=['cat', 'dog'],
        subgrader=StringGrader()
    )
    assert grader(None, "cat, dog")["grade_decimal"] == 1
    assert grader(None, "dog, cat")["grade_decimal"] == 1
    assert grader(None, "cat, octopus")["grade_decimal"] == 0.5
    assert grader(None, "cat")["grade_decimal"] == 0.5

    grader = SingleListGrader(
        answers=(
            [('cat', 'feline'), 'dog'],
            ['goat', 'vole'],
        ),
        subgrader=StringGrader()
    )
    assert grader(None, "cat, dog")["grade_decimal"] == 1
    assert grader(None, "feline, dog")["grade_decimal"] == 1
    assert grader(None, "goat, vole")["grade_decimal"] == 1
    assert grader(None, "cat, vole")["grade_decimal"] == 0.5
    assert grader(None, "dog, goat")["grade_decimal"] == 0.5

    grader = SingleListGrader(
        answers=['cat', 'dog'],
        subgrader=StringGrader(),
        ordered=True
    )
    assert grader(None, "cat, dog")["grade_decimal"] == 1
    assert grader(None, "cat")["grade_decimal"] == 0.5
    assert grader(None, "dog")["grade_decimal"] == 0

    grader = SingleListGrader(
        answers=['cat', 'dog'],
        subgrader=StringGrader(),
        length_error=True
    )
    with raises(MissingInput):
        grader(None, "cat")
    with raises(MissingInput):
        grader(None, "cat, dog, moose")

    grader = SingleListGrader(
        answers=['cat', 'dog'],
        subgrader=StringGrader(),
        delimiter=';'
    )
    assert grader(None, "cat, dog")["grade_decimal"] == 0
    assert grader(None, "dog, cat")["grade_decimal"] == 0
    assert grader(None, "cat; dog")["grade_decimal"] == 1
    assert grader(None, "dog; cat")["grade_decimal"] == 1

    grader = SingleListGrader(
        answers=[['a', 'b'], ['c', 'd']],
        subgrader=SingleListGrader(
            subgrader=StringGrader()
        ),
        delimiter=';'
    )
    assert grader(None, "a,b;c,d")["grade_decimal"] == 1
    assert grader(None, "b,a;d,c")["grade_decimal"] == 1
    assert grader(None, "c,d;a,b")["grade_decimal"] == 1
    assert grader(None, "a,c;b,d")["grade_decimal"] == 0.5

    grader = SingleListGrader(
        answers=['cat', 'dog'],
        subgrader=StringGrader(),
        partial_credit=False
    )
    assert grader(None, "cat, octopus")["grade_decimal"] == 0

    grader = SingleListGrader(
        answers=['cat', 'dog'],
        subgrader=StringGrader(),
        wrong_msg='Try again!'
    )
    assert grader(None, "moose, octopus")["msg"] == "Try again!"

def test_errors():
    """Tests to ensure that errors are raised appropriately"""
    # All answers have same length in tuple
    with raises(ConfigError, match="All possible list answers must have the same length"):
        SingleListGrader(
            answers=(["1", "2", "3"], ["1", "2"]),
            subgrader=StringGrader()
        )

    # Answers must not be empty
    with raises(ConfigError, match="Cannot have an empty list of answers"):
        SingleListGrader(
            answers=([], []),
            subgrader=StringGrader()
        )

    # Empty entries raises an error
    grader = SingleListGrader(
        answers=['1', '2', '3'],
        subgrader=StringGrader()
    )
    with raises(MissingInput, match="List error: Empty entry detected in position 1"):
        grader(None, ',1,2,3')
    with raises(MissingInput, match="List error: Empty entry detected in position 4"):
        grader(None, '1,2,3,')
    with raises(MissingInput, match="List error: Empty entry detected in position 2"):
        grader(None, '1,,2,3')
    with raises(MissingInput, match="List error: Empty entries detected in positions 1, 3"):
        grader(None, ',1,,2,3')

    grader = SingleListGrader(
        answers=['1', '2', '3'],
        subgrader=StringGrader(),
        missing_error=False
    )
    grader(None, ',1,2,3')['grade_decimal'] = 0.75
    grader(None, '1,2,3,')['grade_decimal'] = 0.75
    grader(None, '1,,2,3')['grade_decimal'] = 0.75
    grader(None, ',1,2,3,')['grade_decimal'] = 0.6

def test_infer_expect():
    grader = SingleListGrader(
        subgrader=SingleListGrader(
            subgrader=StringGrader(),
            delimiter=','
        ),
        delimiter=';',
        debug=True
    )
    assert grader.infer_from_expect('a,b;c,d') == [['a', 'b'], ['c', 'd']]
    assert grader.infer_from_expect('a,b,c;d,e,f;g,h,i') == [['a', 'b', 'c'],
                                                             ['d', 'e', 'f'],
                                                             ['g', 'h', 'i']]
    # Test that the grading process works
    assert grader('a,b;c,d', 'd,c;b,a')['ok']
    # Test that inferred answers show up in the debug log as expected
    msg = grader('a,b;c,d', 'a')['msg']
    assert 'Expect value inferred to be [["a", "b"], ["c", "d"]]' in msg
    msg = grader('a,b', 'a')['msg']
    assert 'Expect value inferred to be [["a", "b"]]' in msg
    msg = grader('a;b', 'a')['msg']
    assert 'Expect value inferred to be [["a"], ["b"]]' in msg

    # Test heavy nesting
    grader = SingleListGrader(
        subgrader=SingleListGrader(
            subgrader=SingleListGrader(
                subgrader=StringGrader(),
                delimiter='-'
            ),
            delimiter=','
        ),
        delimiter=';'
    )
    assert grader.infer_from_expect('a-1-@,b-2;c-3,d-4') == [[['a', '1', '@'], ['b', '2']],
                                                             [['c', '3'], ['d', '4']]]

def test_empty_entry_in_answers():
    msg = ("There is a problem with the author's problem configuration: "
           "Empty entry detected in answer list. Students receive an error "
           "when supplying an empty entry. Set 'missing_error' to False in "
           "order to allow such entries.")
    # Test base case
    with raises(ConfigError, match=msg):
        grader = SingleListGrader(
            answers=['a', 'b', ' ', 'c'],
            subgrader=StringGrader()
        )

    # Test case with dictionary
    with raises(ConfigError, match=msg):
        grader = SingleListGrader(
            answers=['a', 'b', {'expect': ' '}, 'c'],
            subgrader=StringGrader()
        )

    # Test case with unusual expect values
    with raises(ConfigError, match=msg):
        grader = SingleListGrader(
            answers=['a',
                     'b',
                     {'comparer': congruence_comparer, 'comparer_params': ['b^2/a', '2*pi']},
                     ''],
            subgrader=FormulaGrader()
        )

    # Test case with really unusual expect values
    with raises(ConfigError, match=msg):
        grader = SingleListGrader(
            answers=['a',
                     'b',
                     {
                         'expect': {
                             'comparer': congruence_comparer,
                             'comparer_params': ['b^2/a', '2*pi']
                         },
                         'msg': 'Well done!'
                     },
                     ''],
            subgrader=FormulaGrader()
        )

    # Test nested case
    with raises(ConfigError, match=msg):
        grader = SingleListGrader(
            answers=[['a', 'b'], ['c', '']],
            subgrader=SingleListGrader(
                subgrader=StringGrader(),
                delimiter=';'
            )
        )

    # Test case with no error
    grader = SingleListGrader(
        answers=['a', 'b', ' ', 'c'],
        subgrader=StringGrader(),
        missing_error=False
    )
    grader('a,,b', 'a, b, c')

def test_answer_validation():
    grader = SingleListGrader(
        subgrader=StringGrader(),
        answers=['a', 'b']
    )
    assert grader.config['answers'] == (
        {
            'expect': [
                ({'expect': 'a', 'msg': '', 'grade_decimal': 1, 'ok': True}, ),
                ({'expect': 'b', 'msg': '', 'grade_decimal': 1, 'ok': True}, )
            ],
            'grade_decimal': 1,
            'msg': '',
            'ok': True
        },
    )

def test_overall_grade_msg():
    grader = SingleListGrader(
        subgrader=StringGrader(),
        answers={'expect': ['a', 'b'], 'msg': 'Yay', 'grade_decimal': 0.5}
    )
    assert grader(None, 'a, b')['grade_decimal'] == 0.5
    assert grader(None, 'a, b')['msg'] == 'Yay'
    assert grader(None, 'a, c')['grade_decimal'] == 0.25
    assert grader(None, 'a, c')['msg'] == ''

    grader = SingleListGrader(
        subgrader=StringGrader(),
        answers={'expect': [{'expect': 'a', 'msg': 'a msg'},
                            {'expect': 'b', 'msg': 'b msg'}],
                 'msg': 'Yay', 'grade_decimal': 0.5}
    )
    assert grader(None, 'a, b')['grade_decimal'] == 0.5
    assert grader(None, 'a, b')['msg'] == 'a msg<br/>\nb msg<br/>\nYay'
    assert grader(None, 'a, c')['grade_decimal'] == 0.25
    assert grader(None, 'a, c')['msg'] == 'a msg'

    grader = SingleListGrader(
        answers=(
            {
                'expect': [('X', {'expect': 'x', 'grade_decimal': 0.5}),
                           ('Y', {'expect': 'y', 'grade_decimal': 0.5})],
                'msg': 'Good pairing!'
            },
            {
                'expect': [('W', {'expect': 'w', 'grade_decimal': 0.5}),
                           ('Z', {'expect': 'z', 'grade_decimal': 0.5})],
                'msg': 'Good pairing!'
            }
        ),
        subgrader=StringGrader()
    )
    result = grader(None, 'X, Y')
    assert result['grade_decimal'] == 1
    assert result['msg'] == 'Good pairing!'
    result = grader(None, 'X, y')
    assert result['grade_decimal'] == 0.75
    assert result['msg'] == 'Good pairing!'
    result = grader(None, 'w, z')
    assert result['grade_decimal'] == 0.5
    assert result['msg'] == 'Good pairing!'
    result = grader(None, 'X, z')
    assert result['grade_decimal'] == 0.5
    assert result['msg'] == ''
    result = grader(None, 'y, z')
    assert result['grade_decimal'] == 0.25
    assert result['msg'] == ''

def test_overall_msg_nested():
    grader = SingleListGrader(
        answers={
            'expect': [['a', 'b'], ['c', {'expect': 'd', 'grade_decimal': 0.5}]],
            'msg': 'Good job!'
        },
        subgrader=SingleListGrader(
            subgrader=StringGrader()
        ),
        delimiter=';'
    )
    result = grader(None, 'a,b;c,d')
    assert result['grade_decimal'] == 0.875
    assert result['msg'] == 'Good job!'
    result = grader(None, 'a,b;c,e')
    assert result['grade_decimal'] == 0.75
    assert result['msg'] == ''
