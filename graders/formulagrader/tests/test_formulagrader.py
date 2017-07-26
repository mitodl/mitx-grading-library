from __future__ import division
from .. import formulagrader as fg
from pytest import approx

def test_square_root_of_negative_number():
    grader = fg.FormulaGrader({
        'answers':['2*i']
    })
    assert grader.cfn(None, 'sqrt(-4)')['ok']
    
def test_half_power_of_negative_number():
    grader = fg.FormulaGrader({
        'answers':['2*i']
    })
    assert grader.cfn(None, '(-4)^0.5')['ok']