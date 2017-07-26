from __future__ import division
from ..formulagrader import *
from pytest import approx

def test_square_root_of_negative_number():
    grader = FormulaGrader({
        'answers':['2*i']
    })
    assert grader.cfn(None, 'sqrt(-4)')['ok']
    
def test_half_power_of_negative_number():
    grader = FormulaGrader({
        'answers':['2*i']
    })
    assert grader.cfn(None, '(-4)^0.5')['ok']
    
def test_overriding_default_functions():
    grader = FormulaGrader({
        'answers':['z^2'],
        'variables':['z'],
        'functions':['re', 'im'],
        'sample_from': {
            'z' : ComplexRectangle()
        }
    })
    learner_input = 're(z)^2 - im(z)^2 + 2*i*re(z)*im(z)'
    assert not grader.cfn(None, learner_input)['ok']