"""
Tests for our customizations of calc.py
"""

from mitxgraders.helpers.calc import evaluator

def test_primed_functions():
    varscope = {
        "a": 4,
        "b''":2.67
    }
    funcscope = {
        "f'" : lambda x: 3*pow(x,2)
    }
    suffscope = {}
    formula = "2*f'(3*a) - 4+b''^2"
    evaluation = evaluator(formula, varscope, funcscope, suffscope, case_sensitive=False)[0]
    assert evaluation == 2*funcscope["f'"](3*varscope["a"]) - 4 + pow(varscope["b''"],2)
