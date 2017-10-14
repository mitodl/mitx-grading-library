"""
Tests for FormulaGrader and NumericalGrader
"""
from __future__ import division
from graders import *
from pytest import approx, raises

def test_square_root_of_negative_number():
    grader = FormulaGrader(
        answers='2*i'
    )
    assert grader(None, 'sqrt(-4)')['ok']

def test_half_power_of_negative_number():
    grader = FormulaGrader(
        answers='2*i'
    )
    assert grader(None, '(-4)^0.5')['ok']

def test_overriding_default_functions():
    grader = FormulaGrader(
        answers='z^2',
        variables=['z'],
        functions=['re', 'im'],
        sample_from={
            'z': ComplexRectangle()
        }
    )
    learner_input = 're(z)^2 - im(z)^2 + 2*i*re(z)*im(z)'
    assert not grader(None, learner_input)['ok']

def test_invalid_input():
    grader = FormulaGrader(answers='2')

    with raises(UndefinedFunction) as err:
        grader(None, "pi(3)")
    expect = 'Invalid Input: pi not permitted in answer as a function (did you forget to use * for multiplication?)'
    assert err.value.args[0] == expect

    with raises(UndefinedFunction) as err:
        grader(None, "spin(3)")
    expect = 'Invalid Input: spin not permitted in answer as a function'
    assert err.value.args[0] == expect

    with raises(UndefinedVariable) as err:
        grader(None, "R")
    expect = 'Invalid Input: R not permitted in answer as a variable'
    assert err.value.args[0] == expect
