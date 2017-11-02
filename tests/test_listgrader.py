"""
Tests for ListGrader
"""
from __future__ import division
import pprint
from pytest import raises
from mitxgraders import (ListGrader, ConfigError, StringGrader, FormulaGrader, NumericalGrader,
                         CalcError, SingleListGrader)

pp = pprint.PrettyPrinter(indent=4)
printit = pp.pprint


def test_order_not_matter():
    grader = ListGrader(
        answers=['cat', 'dog', 'unicorn'],
        subgraders=StringGrader()
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

def test_shorthandAnswers_specification():
    grader = ListGrader(
        answers=['cat', 'dog', 'unicorn'],
        subgraders=StringGrader()
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
        subgraders=StringGrader()
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

def test_partial_creditAssigment():
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
        subgraders=StringGrader()
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
        subgraders=[StringGrader(), FormulaGrader()],
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
    with raises(CalcError, match='Invalid Input: cat not permitted in answer'):
        result = grader(None, submission)

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
    with raises(ConfigError, match='The number of subgraders and answers are different'):
        ListGrader(
            answers=['cat', '1'],
            subgraders=[StringGrader()],
            ordered=True
        )

    # Unordered entry
    with raises(ConfigError, match='Cannot use unordered lists with multiple graders'):
        ListGrader(
            answers=['cat', '1'],
            subgraders=[StringGrader(), StringGrader()],
            ordered=False
        )

def test_wrong_number_of_inputs():
    """Check that an error is raised if number of answers != number of inputs"""
    expect = r'The number of answers \(2\) and the number of inputs \(1\) are different'
    with raises(ConfigError, match=expect):
        grader = ListGrader(
            answers=['cat', 'dog'],
            subgraders=StringGrader()
        )
        grader(None, ['cat'])

def test_insufficientAnswers():
    """Check that an error is raised if ListGrader is fed only one answer"""
    with raises(ConfigError, match='ListGrader does not work with a single answer'):
        ListGrader(
            answers=['cat'],
            subgraders=StringGrader()
        )

def test_zeroAnswers():
    """Check that ListGrader instantiates without any answers supplied (used in nesting)"""
    ListGrader(
        answers=[],
        subgraders=StringGrader()
    )

def test_multiple_listAnswers():
    """Check that a listgrader with multiple possible answers is graded correctly"""
    grader = ListGrader(
        answers=(['cat', 'meow'], ['dog', 'woof']),
        subgraders=StringGrader()
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

def test_multiple_listAnswers_same_grade():
    grader = ListGrader(
        answers=(
            [{'expect': 'dog', 'msg': 'dog1'}, 'woof'],
            ['cat', 'woof'],
            [{'expect': 'dog', 'msg': 'dog2'}, 'woof'],
            ['dolphin', 'squeak'],
        ),
        subgraders=StringGrader()
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
    """Check that we can use have a SingleListGrader as a subgrader"""
    grader = ListGrader(
        answers=[
            ['1', '2'],
            ['3', '4']
        ],
        subgraders=SingleListGrader(
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

def test_grouping_errors_subgraderAnd_groups_mismatched_in_size():
    """Test that errors are raised when nested ListGraders have size mismatches"""
    # Too many graders
    with raises(ConfigError, match="Number of subgraders and number of groups are not equal"):
        ListGrader(
            answers=[
                ['bat', 'ghost', 'pumpkin'],
                'Halloween'
            ],
            subgraders=[
                ListGrader(
                    subgraders=StringGrader()
                ),
                StringGrader()
            ],
            ordered=True,
            grouping=[1, 1, 1, 1]
        )
    # Too few graders
    with raises(ConfigError, match="Number of subgraders and number of groups are not equal"):
        ListGrader(
            answers=[
                ['bat', 'ghost', 'pumpkin'],
                'Halloween',
            ],
            subgraders=[
                ListGrader(
                    subgraders=StringGrader()
                ),
                StringGrader()
            ],
            ordered=True,
            grouping=[1, 1, 1, 2, 3]
        )

def test_grouping_not_contiguous_integers():
    """Test that the group numbers are contiguous integers"""
    msg = "Grouping should be a list of contiguous positive integers starting at 1."
    with raises(ConfigError, match=msg):
        ListGrader(
            answers=[
                ['bat', 'ghost', 'pumpkin'],
                'Halloween',
            ],
            subgraders=[
                ListGrader(
                    subgraders=StringGrader()
                ),
                StringGrader()
            ],
            ordered=True,
            grouping=[1, 1, 1, 3]
        )

def test_grouping_errors_group_needs_list_grader():
    """Test that anything with grouping needs a ListGrader"""
    msg = "Grouping index 2 has 3 items, but has a StringGrader subgrader instead of ListGrader"
    with raises(ConfigError, match=msg):
        ListGrader(
            answers=[
                ['bat', 'ghost', 'pumpkin'],
                'Halloween'
            ],
            subgraders=[
                ListGrader(
                    subgraders=StringGrader()
                ),
                StringGrader()
            ],
            ordered=True,
            grouping=[1, 2, 2, 2]
        )

def test_wrong_number_of_inputs_with_grouping():
    """Test that the right number of inputs is required"""
    msg = "Grouping indicates 4 inputs are expected, but only 3 inputs exist."
    with raises(ConfigError, match=msg):
        grader = ListGrader(
            answers=[
                ['bat', 'ghost', 'pumpkin'],
                'Halloween'
            ],
            subgraders=[
                ListGrader(
                    subgraders=StringGrader()
                ),
                StringGrader()
            ],
            ordered=True,
            grouping=[2, 1, 1, 1]
        )
        grader(None, ['Halloween', 'cat', 'rat'])

def test_grouping_unordered_inputs():
    """
    Test nested ListGraders using grouping.
    Intended to mimick a two-column layout, list mammals in one column birds in another.
    """
    grader = ListGrader(
        answers=[
            ['cat', 'otter', 'bear'],
            ['eagle', 'sparrow', 'hawk']
        ],
        grouping=[1, 2, 1, 2, 1, 2],
        subgraders=ListGrader(
            subgraders=StringGrader()
        )
    )
    student_input = [
        'hawk', 'otter',
        'falcon', 'bear',
        'eagle', 'dog'
    ]
    expected_result = {
        'overall_message': '',
        'input_list': [
            # hawk good, otter good
            {'ok': True, 'msg': '', 'grade_decimal': 1},
            {'ok': True, 'msg': '', 'grade_decimal': 1},
            # falcon bad, bear good
            {'ok': False, 'msg': '', 'grade_decimal': 0},
            {'ok': True, 'msg': '', 'grade_decimal': 1},
            # eagle good, dog bad
            {'ok': True, 'msg': '', 'grade_decimal': 1},
            {'ok': False, 'msg': '', 'grade_decimal': 0},
        ]
    }
    assert grader(None, student_input) == expected_result

def test_grouping_with_subgraders_list():
    """Another test of a nested ListGrader with grouping"""
    grader = ListGrader(
        answers=[
            [
                'bat',
                ('ghost', {'expect': 'spectre', 'grade_decimal': 0.5}),
                'pumpkin'
            ],
            'Halloween'
        ],
        subgraders=[
            ListGrader(
                subgraders=StringGrader()
            ),
            StringGrader()
        ],
        ordered=True,
        grouping=[1, 2, 1, 1]
    )
    student_input = ['pumpkin', 'Halloween', 'bird', 'spectre']
    expected_result = {
        'overall_message': '',
        'input_list': [
            {'ok': True, 'grade_decimal': 1, 'msg': ''},
            {'ok': True, 'grade_decimal': 1, 'msg': ''},
            {'ok': False, 'grade_decimal': 0, 'msg': ''},
            {'ok': 'partial', 'grade_decimal': 0.5, 'msg': ''}
        ]
    }
    assert grader(None, student_input) == expected_result

def test_multiple_nestingAnd_groups():
    """
    Test of a grouping inside a grouping.
    Enter the normalized, eigenvalues & eigenvectors of [[1,0],[0,-1]]
    Of course, in a real problem we wouldn't use StringGrader to grade the numbers

    TODO Expand this test once the required infrastructure is in place
    """
    grader = ListGrader(
        answers=[
            [
                {'expect': '1', 'msg': 'first eigenvalue'},
                (
                    {'expect': '+1, 0', 'msg': 'positive first eigenvector'},
                    {'expect': '-1, 0', 'msg': 'negative first eigenvector', 'grade_decimal': 0.8}
                )
            ],
            [
                {'expect': '-1', 'msg': 'second eigenvalue'},
                (
                    {'expect': '0, +1', 'msg': 'positive second eigenvector'},
                    {'expect': '0, -1', 'msg': 'negative second eigenvector', 'grade_decimal': 0.8}
                )
            ],
        ],
        subgraders=ListGrader(
            subgraders=[
                FormulaGrader(),
                StringGrader()
            ],
            ordered=True,
            grouping=[1, 2]
        ),
        grouping=[1, 1, 2, 2]
    )

    submission = [
        '-1', '0, -1',
        '1', '+1, 0',
    ]
    expected = {
        'overall_message': '',
        'input_list': [
            {'ok': True, 'msg': 'second eigenvalue', 'grade_decimal': 1},
            {'ok': 'partial', 'msg': 'negative second eigenvector', 'grade_decimal': 0.8},
            {'ok': True, 'msg': 'first eigenvalue', 'grade_decimal': 1},
            {'ok': True, 'msg': 'positive first eigenvector', 'grade_decimal': 1}
        ]
    }
    assert grader(None, submission) == expected

def test_nested_grouping_ordered():
    """Test that ordered nested groupings work appropriately"""
    grader = ListGrader(
        answers=[
            ['0', '1'],
            ['2', '3'],
        ],
        subgraders=ListGrader(
            subgraders=FormulaGrader(),
            ordered=True
        ),
        grouping=[1, 1, 2, 2]
    )

    def expect(a, b, c, d):
        return {
            'input_list': [
                {'grade_decimal': a, 'msg': '', 'ok': a == 1},
                {'grade_decimal': b, 'msg': '', 'ok': b == 1},
                {'grade_decimal': c, 'msg': '', 'ok': c == 1},
                {'grade_decimal': d, 'msg': '', 'ok': d == 1}
            ],
            'overall_message': ''
        }
    assert grader(None, ['0', '1', '2', '3']) == expect(1, 1, 1, 1)
    assert grader(None, ['1', '0', '3', '2']) == expect(0, 0, 0, 0)
    assert grader(None, ['2', '3', '0', '1']) == expect(1, 1, 1, 1)
    assert grader(None, ['3', '2', '1', '0']) == expect(0, 0, 0, 0)
    assert grader(None, ['1', '3', '2', '0']) == expect(0, 1, 0, 0)
    assert grader(None, ['0', '2', '3', '1']) == expect(1, 0, 0, 0)


def test_grouping_unordered_different_lengths():
    """Test that an error is raised if unordered groupings use different numbers of inputs"""
    msg = "Groups must all be the same length when unordered"
    with raises(ConfigError, match=msg):
        ListGrader(
            answers=[
                ['bat', 'ghost', 'pumpkin'],
                ['Halloween', 'Easter'],
            ],
            subgraders=ListGrader(
                subgraders=StringGrader()
            ),
            ordered=False,
            grouping=[1, 1, 1, 2]
        )


def test_docs():
    """Tests that the examples in the documentation behave as expected"""
    grader = ListGrader(
        answers=['cat', 'dog'],
        subgraders=StringGrader()
    )
    expected_result = {
        'overall_message': '',
        'input_list': [
            {'ok': True, 'grade_decimal': 1, 'msg': ''},
            {'ok': True, 'grade_decimal': 1, 'msg': ''},
        ]
    }
    submissions = ['cat', 'dog']
    assert grader(None, submissions) == expected_result
    submissions = ['dog', 'cat']
    assert grader(None, submissions) == expected_result

    answer1 = (
        {'expect': 'zebra', 'grade_decimal': 1},
        {'expect': 'horse', 'grade_decimal': 0.45},
        {'expect': 'unicorn', 'grade_decimal': 0, 'msg': 'Unicorn? Really?'}
    )
    answer2 = (
        {'expect': 'cat', 'grade_decimal': 1},
        {'expect': 'feline', 'grade_decimal': 0.5}
    )
    grader = ListGrader(
        answers=[answer1, answer2],
        subgraders=StringGrader()
    )
    expected_result = {
        'overall_message': '',
        'input_list': [
            {'ok': True, 'grade_decimal': 1, 'msg': ''},
            {'ok': True, 'grade_decimal': 1, 'msg': ''},
        ]
    }
    submissions = ['cat', 'zebra']
    assert grader(None, submissions) == expected_result
    expected_result = {
        'overall_message': '',
        'input_list': [
            {'ok': 'partial', 'grade_decimal': 0.5, 'msg': ''},
            {'ok': False, 'grade_decimal': 0, 'msg': 'Unicorn? Really?'},
        ]
    }
    submissions = ['feline', 'unicorn']
    assert grader(None, submissions) == expected_result

    grader = ListGrader(
        answers=['cat', 'dog'],
        subgraders=StringGrader(),
        ordered=True
    )
    expected_result = {
        'overall_message': '',
        'input_list': [
            {'ok': True, 'grade_decimal': 1, 'msg': ''},
            {'ok': True, 'grade_decimal': 1, 'msg': ''},
        ]
    }
    submissions = ['cat', 'dog']
    assert grader(None, submissions) == expected_result
    expected_result = {
        'overall_message': '',
        'input_list': [
            {'ok': False, 'grade_decimal': 0, 'msg': ''},
            {'ok': False, 'grade_decimal': 0, 'msg': ''},
        ]
    }
    submissions = ['dog', 'cat']
    assert grader(None, submissions) == expected_result

    grader = ListGrader(
        answers=['cat', 'x^2+1'],
        subgraders=[StringGrader(), FormulaGrader(variables=["x"])],
        ordered=True
    )
    expected_result = {
        'overall_message': '',
        'input_list': [
            {'ok': True, 'grade_decimal': 1, 'msg': ''},
            {'ok': True, 'grade_decimal': 1, 'msg': ''},
        ]
    }
    submissions = ['cat', '(x-i)*(x+i)']
    assert grader(None, submissions) == expected_result

    grader = ListGrader(
        answers=[
            ['2', '4'],
            ['1', '3']
        ],
        subgraders=SingleListGrader(
            subgrader=NumericalGrader()
        ),
        ordered=True
    )
    expected_result = {
        'overall_message': '',
        'input_list': [
            {'ok': True, 'grade_decimal': 1, 'msg': ''},
            {'ok': True, 'grade_decimal': 1, 'msg': ''},
        ]
    }
    submissions = ['2, 4', '3,1']
    assert grader(None, submissions) == expected_result

    grader = ListGrader(
        answers=[
            ['cat', '1'],
            ['dog', '2'],
            ['tiger', '3']
        ],
        subgraders=ListGrader(
            subgraders=[StringGrader(), NumericalGrader()],
            ordered=True
        ),
        grouping=[1, 1, 2, 2, 3, 3]
    )
    expected_result = {
        'overall_message': '',
        'input_list': [
            {'ok': True, 'grade_decimal': 1, 'msg': ''},
            {'ok': True, 'grade_decimal': 1, 'msg': ''},
            {'ok': True, 'grade_decimal': 1, 'msg': ''},
            {'ok': False, 'grade_decimal': 0, 'msg': ''},
            {'ok': True, 'grade_decimal': 1, 'msg': ''},
            {'ok': False, 'grade_decimal': 0, 'msg': ''},
        ]
    }
    submissions = ['cat', '1', 'dog', '3', 'tiger', '2']
    assert grader(None, submissions) == expected_result

    grader = ListGrader(
        answers=[
            ['bat', 'ghost', 'pumpkin'],
            'Halloween'
        ],
        subgraders=[
            ListGrader(
                subgraders=StringGrader()
            ),
            StringGrader()
        ],
        ordered=True,
        grouping=[1, 1, 1, 2]
    )
    expected_result = {
        'overall_message': '',
        'input_list': [
            {'ok': False, 'grade_decimal': 0, 'msg': ''},
            {'ok': True, 'grade_decimal': 1, 'msg': ''},
            {'ok': True, 'grade_decimal': 1, 'msg': ''},
            {'ok': False, 'grade_decimal': 0, 'msg': ''},
        ]
    }
    submissions = ['Halloween', 'bat', 'pumpkin', 'ghost']
    assert grader(None, submissions) == expected_result

    grader = ListGrader(
        answers=[
            ['1', (['1', '0'], ['-1', '0'])],
            ['-1', (['0', '1'], ['0', '-1'])],
        ],
        subgraders=ListGrader(
            subgraders=[
                NumericalGrader(),
                SingleListGrader(
                    subgrader=NumericalGrader(),
                    ordered=True
                )
            ],
            ordered=True
        ),
        grouping=[1, 1, 2, 2]
    )
    expected_result = {
        'overall_message': '',
        'input_list': [
            {'ok': True, 'grade_decimal': 1, 'msg': ''},
            {'ok': True, 'grade_decimal': 1, 'msg': ''},
            {'ok': True, 'grade_decimal': 1, 'msg': ''},
            {'ok': True, 'grade_decimal': 1, 'msg': ''},
        ]
    }
    submissions = ['-1', '0, 1', '1', '-1, 0']
    assert grader(None, submissions) == expected_result

    grader = ListGrader(
        answers=[
            ['1', (['1', '0'], ['-1', '0'])],
            ['-1', (['0', '1'], ['0', '-1'])],
        ],
        subgraders=ListGrader(
            subgraders=[
                NumericalGrader(),
                ListGrader(
                    subgraders=NumericalGrader(),
                    ordered=True
                )
            ],
            ordered=True,
            grouping=[1, 2, 2]
        ),
        grouping=[1, 1, 1, 2, 2, 2]
    )
    expected_result = {
        'overall_message': '',
        'input_list': [
            {'ok': True, 'grade_decimal': 1, 'msg': ''},
            {'ok': True, 'grade_decimal': 1, 'msg': ''},
            {'ok': True, 'grade_decimal': 1, 'msg': ''},
            {'ok': True, 'grade_decimal': 1, 'msg': ''},
            {'ok': True, 'grade_decimal': 1, 'msg': ''},
            {'ok': True, 'grade_decimal': 1, 'msg': ''}
        ]
    }
    submissions = ['1', '-1', '0', '-1', '0', '1']
    assert grader(None, submissions) == expected_result
