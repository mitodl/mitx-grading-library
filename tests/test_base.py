"""
Tests of base class functionality
"""
from __future__ import division
import math
import random
from pytest import raises, approx
from voluptuous import Error, Invalid, truth
from mitxgraders import ListGrader, StringGrader, ConfigError, FormulaGrader, CalcError, __version__
from mitxgraders.helpers import validatorfuncs
from mitxgraders.helpers.calc import evaluator, UnableToParse, UndefinedVariable
from mitxgraders.helpers.mathfunc import (cot, arcsec, arccsc, arccot, sech, csch, coth,
                                          arcsech, arccsch, arccoth, sec, csc)

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

def test_calcpy():
    """Tests of calc.py that aren't covered elsewhere"""

    # Test unhandled exception
    def badfunc(a):
        raise ValueError("Badness!")
    with raises(CalcError, match=r"There was an error evaluating f\(...\). Its input does not seem to be in its domain."):
        evaluator("1+f(2)", {}, {"f": badfunc}, {})

    # Test formula with None
    result = evaluator(None, {}, {}, {})
    assert result[0] == approx(float('nan'), nan_ok=True)
    assert result[1] == set()

    # Test formulae with parallel operator
    result = evaluator("1 || 1 || 1", {}, {}, {})
    assert result[0] == 1/3
    assert result[1] == set()

    result = evaluator("1 || 1 || 0", {}, {}, {})
    assert result[0] == approx(float('nan'), nan_ok=True)
    assert result[1] == set()

    # Test incorrect case variables
    with raises(UndefinedVariable, match=r"Invalid Input: X not permitted in answer as a variable \(did you mean x\?\)"):
        evaluator("X", {"x": 1}, {}, {})

def test_validators():
    """Tests of validatorfuncs.py that aren't covered elsewhere"""
    # PercentageString
    with raises(Invalid, match="Not a valid percentage string"):
        validatorfuncs.PercentageString("mess%")

    # ListOfType
    testfunc = validatorfuncs.ListOfType(int)
    assert testfunc([1, 2, 3]) == [1, 2, 3]

    # TupleOfType
    @truth
    def testvalidator(obj):
        """Returns true"""
        return True
    testfunc = validatorfuncs.TupleOfType(int, testvalidator)
    assert testfunc((-1,)) == (-1,)

def test_math():
    """Test the math functions that we've implemented"""
    x = random.uniform(0, 1)
    assert cot(x) == approx(1/math.tan(x))
    assert sec(x) == approx(1/math.cos(x))
    assert csc(x) == approx(1/math.sin(x))
    assert sech(x) == approx(1/math.cosh(x))
    assert csch(x) == approx(1/math.sinh(x))
    assert coth(x) == approx(1/math.tanh(x))
    assert arcsec(sec(x)) == approx(x)
    assert arccsc(csc(x)) == approx(x)
    assert arccot(cot(x)) == approx(x)
    assert arcsech(sech(x)) == approx(x)
    assert arccsch(csch(x)) == approx(x)
    assert arccoth(coth(x)) == approx(x)

    x = random.uniform(-1, 0)
    assert cot(x) == approx(1/math.tan(x))
    assert sec(x) == approx(1/math.cos(x))
    assert csc(x) == approx(1/math.sin(x))
    assert sech(x) == approx(1/math.cosh(x))
    assert csch(x) == approx(1/math.sinh(x))
    assert coth(x) == approx(1/math.tanh(x))
    assert -arcsec(sec(x)) == approx(x)
    assert arccsc(csc(x)) == approx(x)
    assert arccot(cot(x)) == approx(x)
    assert -arcsech(sech(x)) == approx(x)
    assert arccsch(csch(x)) == approx(x)
    assert arccoth(coth(x)) == approx(x)

def test_varnames():
    """Test variable names in calc.py"""
    # Tensor variable names
    assert evaluator("U^{ijk}", {"U^{ijk}":2}, {}, {})[0] == 2
    assert evaluator("U_{ijk}/2", {"U_{ijk}":2}, {}, {})[0] == 1
    assert evaluator("U_{ijk}^{123}", {"U_{ijk}^{123}":2}, {}, {})[0] == 2
    assert evaluator("U_{ijk}^{123}'''''", {"U_{ijk}^{123}'''''":2}, {}, {})[0] == 2
    assert evaluator("U_{ijk}^2", {"U_{ijk}":2}, {}, {})[0] == 4
    assert evaluator("U^{ijk}^2", {"U^{ijk}":2}, {}, {})[0] == 4
    assert evaluator("U_{ijk}^{123}^2", {"U_{ijk}^{123}":2}, {}, {})[0] == 4
    # Regular variable names
    assert evaluator("U_cat/2 + Th3_dog__7a_", {"U_cat":2, "Th3_dog__7a_":4}, {}, {})[0] == 5
    # tensor subscripts need braces
    with raises(UnableToParse):
        assert evaluator("U_123^{ijk}", {}, {}, {})
    with raises(UnableToParse):
        assert evaluator("T_1_{123}^{ijk}", {}, {}, {})
