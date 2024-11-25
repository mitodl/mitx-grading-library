"""
Tests for FormulaGrader and NumericalGrader
"""


from pytest import raises
from voluptuous import Error

from mitxgraders import IntervalGrader, NumericalGrader, FormulaGrader, StringGrader
from mitxgraders.exceptions import ConfigError, InvalidInput

def test_usage():
    grader = IntervalGrader()
    assert grader("[1, 2)", "[1, 2)")['ok']
    assert grader("[1, 2)", "[1, 2]")['grade_decimal'] == 0.5
    assert grader("(1, 2)", "[1, 2]")['grade_decimal'] == 0
    assert grader("(1, 2)", "(2, 3)")['grade_decimal'] == 0

    grader = IntervalGrader(partial_credit=False)
    assert grader("[1, 2)", "[1, 2]")['grade_decimal'] == 0

def test_errors():
    msg = r"Invalid opening bracket. The opening_brackets configuration allows for '\[', '\(' as opening brackets."
    with raises(ConfigError, match=msg):
        grader = IntervalGrader(answers=['{','1','2',']'])

    msg = r"Invalid closing bracket. The closing_brackets configuration allows for '\]', '\)' as closing brackets."
    with raises(ConfigError, match=msg):
        grader = IntervalGrader(answers=['(','1','2','}'])

    msg = r"Answer list must have 4 entries: opening bracket, lower bound, upper bound, closing bracket."
    with raises(ConfigError, match=msg):
        grader = IntervalGrader(answers=['(','2','}'])
    with raises(ConfigError, match=msg):
        grader = IntervalGrader(answers=['(','2','3','5','}'])

    msg = r"Opening bracket must be a single character."
    with raises(ConfigError, match=msg):
        grader = IntervalGrader(answers=['(a','2','3','}'])

    msg = r"Closing bracket must be a single character."
    with raises(ConfigError, match=msg):
        grader = IntervalGrader(answers=['(','2','3','}a'])

    msg = r'Unable to read interval from answer: "abcd"'
    with raises(ConfigError, match=msg):
        grader = IntervalGrader()
        grader('abcd', '1, 2, 3')

    msg = r'Unable to read interval from answer: "2, 3"'
    with raises(ConfigError, match=msg):
        grader = IntervalGrader()
        grader('[1,2]', '2, 3')

    msg = r"Invalid opening bracket: '{'. Valid options are: '\[', '\('."
    with raises(InvalidInput, match=msg):
        grader = IntervalGrader()
        grader('[1,2]', '{1, 2}')

    msg = r"Invalid closing bracket: '}'. Valid options are: '\]', '\)'."
    with raises(InvalidInput, match=msg):
        grader = IntervalGrader()
        grader('[1,2]', '[1, 2}')

def test_messages():    
    grader = IntervalGrader(answers=[('[', {'expect': '(', 'msg': 'testing'}), '1', '2', ')'])
    assert grader("[1, 2)", "(1, 2)")['msg'] == 'testing'

    grader = IntervalGrader(answers=[('[', {'expect': '(', 'msg': 'testing'}), {'expect': '1', 'msg': 'yay!'}, '2', ')'])
    assert grader("[1, 2)", "(1, 2)")['msg'] == 'yay!<br/>\ntesting'

def test_subgraders():
    assert IntervalGrader() == IntervalGrader(subgrader=NumericalGrader(tolerance=1e-13, allow_inf=True))

    # Make sure this instantiates
    IntervalGrader(subgrader=FormulaGrader(tolerance=1e-13))

    with raises(Error):
        IntervalGrader(subgrader=StringGrader())

def test_inferring_answers():
    grader = IntervalGrader()
    grader1 = IntervalGrader(answers="(1,2]")
    grader2 = IntervalGrader(answers=["(", "1", "2", "]"])
    assert grader1 == grader2

    assert grader("(1,2]", "(1,2]") == grader1("(1,2]", "(1,2]")
    assert grader("(1,2]", "(1,2)") == grader1("(1,2]", "(1,2)")

def test_multiple_answers():
    grader = IntervalGrader(answers={'expect': ("(1,2]", '(3,4]')})

    expected_result = {'ok': True, 'grade_decimal': 1, 'msg': ''}
    assert grader(None, "(1,2]") == expected_result
    assert grader(None, "(3,4]") == expected_result

def test_formulas():
    grader = IntervalGrader(
        answers="(x, y^2 + 1)",
        subgrader=FormulaGrader(variables=['x', 'y'])
    )
    assert grader(None, '(x, y^2+1]')['grade_decimal'] == 0.5

def test_infinite_interval():
    grader = IntervalGrader(
        answers="(0, infty)"
    )
    assert grader(None, '(0, infty)')['ok']
