"""
Tests for FormulaGrader and NumericalGrader
"""
from __future__ import print_function, division, absolute_import

from pytest import raises
import platform
from unittest import mock
import numpy as np
from voluptuous import Error, MultipleInvalid
from mitxgraders import (
    FormulaGrader,
    NumericalGrader,
    RealInterval,
    IntegerRange,
    DiscreteSet,
    ComplexRectangle,
    ComplexSector,
    SpecificFunctions,
    RandomFunction,
    ConfigError,
    DependentSampler,
)
from mitxgraders.exceptions import MissingInput, InvalidInput
from mitxgraders.sampling import set_seed
from mitxgraders.version import __version__ as VERSION
from mitxgraders.helpers.calc.exceptions import (
    CalcError, UndefinedVariable, UndefinedFunction
)
from mitxgraders import ListGrader
from mitxgraders.comparers import equality_comparer
from tests.helpers import log_results, round_decimals_in_string

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

def test_factorial():
    grader = FormulaGrader(answers='0')
    expect = (r"Error evaluating factorial\(\) or fact\(\) in input. "
              r"These functions cannot be used at negative integer values.")

    grader(None, 'fact(0.5) - sqrt(pi)/2')
    grader(None, 'fact(-0.5) + sqrt(pi)')
    grader(None, '0 + fact(3.2) - fact(2.2)*3')

    with raises(CalcError, match=expect):
        grader(None, "fact(-1)")
    with raises(CalcError, match=expect):
        grader(None, "fact(-2)")

def test_overriding_functions():
    grader = FormulaGrader(
        answers='tan(1)',
        user_functions={'sin': lambda x: x},
        suppress_warnings=True
    )
    assert grader(None, 'tan(1)')['ok']
    assert not grader(None, 'sin(1)/cos(1)')['ok']

def test_fg_expressions():
    """General test of FormulaGrader"""
    grader = FormulaGrader(
        answers="1+tan(3/2)",
        tolerance="0.1%"
    )
    assert grader(None, "(cos(3/2) + sin(3/2))/cos(3/2 + 2*pi)")['ok']
    # Checking tolerance
    assert grader(None, "0.01+(cos(3/2) + sin(3/2))/cos(3/2 + 2*pi)")['ok']
    assert not grader(None, "0.02+(cos(3/2) + sin(3/2))/cos(3/2 + 2*pi)")['ok']

def test_fg_invalid_input():
    grader = FormulaGrader(answers='2', variables=['m'])

    expect = "Invalid Input: 'pi' not permitted in answer as a function " + \
             r'\(did you forget to use \* for multiplication\?\)'
    with raises(CalcError, match=expect):
        grader(None, "pi(3)")

    expect = "Invalid Input: 'Im', 'Re' not permitted in answer as a function " + \
             r"\(did you mean 'im', 're'\?\)"
    with raises(CalcError, match=expect):
        grader(None, "Im(3) + Re(2)")

    expect = "Invalid Input: 'spin' not permitted in answer as a function"
    with raises(CalcError, match=expect):
        grader(None, "spin(3)")

    expect = "Invalid Input: 'R' not permitted in answer as a variable"
    with raises(CalcError, match=expect):
        grader(None, "R")

    expect = "Invalid Input: 'Q', 'R' not permitted in answer as a variable"
    with raises(CalcError, match=expect):
        grader(None, "R+Q")

    expect = "Invalid Input: 'pp' not permitted directly after a number"
    with raises(CalcError, match=expect):
        grader(None, "5pp")

    expect = "Invalid Input: 'mm', 'pp' not permitted directly after a number"
    with raises(CalcError, match=expect):
        grader(None, "5pp+6mm")

    expect = (r"Invalid Input: 'm' not permitted directly after a number "
              r"\(did you forget to use \* for multiplication\?\)")
    with raises(CalcError, match=expect):
        grader(None, "5m")

    expect = (r"There was an error evaluating csc\(...\). "
              r"Its input does not seem to be in its domain.")
    with raises(CalcError, match=expect):
        grader(None, 'csc(0)')

    expect = r"There was an error evaluating sinh\(...\). \(Numerical overflow\)."
    with raises(CalcError, match=expect):
        grader(None, 'sinh(10000)')

    expect = (r"There was an error evaluating arccosh\(...\). "
              r"Its input does not seem to be in its domain.")
    with raises(CalcError, match=expect):
        grader(None, 'arccosh(0)')

    expect = "Division by zero occurred. Check your input's denominators."
    with raises(CalcError, match=expect):
        grader(None, '1/0')

    expect = "Numerical overflow occurred. Does your input generate very large numbers?"
    with raises(CalcError, match=expect):
        grader(None, '2^10000')

def test_fg_tolerance():
    """Test of FormulaGrader tolerance"""
    grader = FormulaGrader(answers="10", tolerance=0.1)

    assert not grader(None, '9.85')['ok']
    assert grader(None, '9.9')['ok']
    assert grader(None, '10')['ok']
    assert grader(None, '10.1')['ok']
    assert not grader(None, '10.15')['ok']

    grader = FormulaGrader(answers="10", tolerance="1%")

    assert not grader(None, '9.85')['ok']
    assert grader(None, '9.9')['ok']
    assert grader(None, '10')['ok']
    assert grader(None, '10.1')['ok']
    assert not grader(None, '10.15')['ok']

    grader = FormulaGrader(answers="10", tolerance=0)

    assert not grader(None, '9.999999')['ok']
    assert grader(None, '10')['ok']
    assert not grader(None, '10.000001')['ok']

    expect = (r"Cannot have a negative percentage for dictionary value @ "
              r"data\[u?'tolerance'\]. Got u?'-1%'")
    with raises(Error, match=expect):
        FormulaGrader(answers="10", tolerance="-1%")

def test_fg_userfunc():
    """Test a user function in FormulaGrader"""
    grader = FormulaGrader(
        answers="hello(2)",
        user_functions={"hello": lambda x: x**2-1}
    )
    assert grader(None, "5+hello(2)-2-3")['ok']
    assert not grader(None, "hello(1)")['ok']

def test_fg_percent():
    """Test a percentage suffix in FormulaGrader"""
    grader = FormulaGrader(
        answers="2%"
    )
    assert grader(None, "2%")['ok']
    assert grader(None, "0.02")['ok']
    with raises(CalcError, match="Invalid Input: 'm' not permitted directly after a number"):
        grader(None, "20m")

def test_fg_metric():
    """Test metric suffixes in FormulaGrader"""
    grader = FormulaGrader(
        answers="0.02",
        metric_suffixes=True
    )
    assert grader(None, "2%")['ok']
    assert grader(None, "0.02")['ok']
    assert grader(None, "20m")['ok']

def test_fg_userfunction():
    """Test FormulaGrader with user-defined functions"""
    grader = FormulaGrader(
        answers="sin(0.4)/cos(0.4)",
        user_functions={"hello": np.tan}
    )
    assert grader(None, "hello(0.4)")['ok']
    assert grader(None, "sin(0.4)/cos(0.4)")['ok']

    # Test with variable and function names with primes at the end
    grader = FormulaGrader(
        answers="sin(0.4)/cos(0.4)+t''^2",
        variables=["t''"],
        user_functions={"f'": np.tan}
    )
    assert grader(None, "f'(0.4)+t''^2")['ok']

    grader = FormulaGrader(
        answers="sin(0.4)/cos(0.4)",
        user_functions={"function2name_2go''''''": np.tan}
    )
    assert grader(None, "function2name_2go''''''(0.4)")['ok']

    # Primes aren't allowed in the middle
    expect = r"Invalid Input: Could not parse 'that'sbad\(1\)' as a formula"
    with raises(CalcError, match=expect):
        grader = FormulaGrader(
            answers="1",
            user_functions={"that'sbad": np.tan}
        )
        grader(None, "that'sbad(1)")

    expect = (r"1 is not a valid key, must be of type string for dictionary "
              r"value @ data\[u?'user_functions'\]. Got {{1: <ufunc 'tan'>}}").format(
              str_type=str)
    with raises(Error, match=expect):
        FormulaGrader(
            answers="1",
            user_functions={1: np.tan}
        )

def test_fg_userconstants():
    """Test FormulaGrader with user-defined constants"""
    grader = FormulaGrader(
        answers="5",
        user_constants={"hello": 5}
    )
    assert grader(None, "hello")['ok']

    expect = (r"1 is not a valid key, must be of type string for dictionary "
              r"value @ data\[u?'user_constants'\]. Got {1: 5}")
    with raises(Error, match=expect):
        FormulaGrader(
            answers="1",
            user_constants={1: 5}
        )
        
    # Test collisions
    with raises(ConfigError, match='will override default values'):
        grader = FormulaGrader(
            answers="5",
            user_constants={"i": 5}
        )
    
    # Test removals
    grader = FormulaGrader(
        answers="5",
        user_constants={"i": None}
    )
    with raises(UndefinedVariable, match="'i' not permitted"):
        grader(None, 'i')

    grader = FormulaGrader(
        answers="-1"
    )
    assert grader(None, "i^2")['ok']
    grader = FormulaGrader(
        answers="-1",
        user_constants={"i": None},
        variables=['i']
    )
    assert not grader(None, "i^2")['ok']

def test_fg_blacklist_grading():
    """Test FormulaGrader with blacklists and whitelists"""
    grader = FormulaGrader(
        answers="sin(0.4)/cos(0.4)",
        user_functions={"hello": np.tan},
        blacklist=['tan']
    )
    assert grader(None, "hello(0.4)")['ok']
    # Incorrect answers with forbidden function are marked wrong:
    assert not grader(None, "cos(0.4)/sin(0.4)")['ok']
    # Correct answers with forbidden function raise error:
    assert grader(None, "sin(0.4)/cos(0.4)")['ok']
    expect = r"Invalid Input: function\(s\) 'tan' not permitted in answer"
    with raises(InvalidInput, match=expect):
        grader(None, "tan(0.4)")
    expect = r"Invalid Input: 'TAN', 'Tan' not permitted in answer as a function \(did you mean 'tan'\?\)"
    with raises(UndefinedFunction, match=expect):
        grader(None, "(TAN(0.4) + Tan(0.4))/2")

def test_fg_whitelist_grading():
    grader = FormulaGrader(
        answers="sin(0.4)/cos(0.4)",
        user_functions={"hello": np.tan},
        whitelist=['cos', 'sin']
    )
    assert grader(None, "hello(0.4)")['ok']

    assert grader(None, "sin(0.4)/cos(0.4)")['ok']
    # Incorrect answers with forbidden function are marked wrong:
    assert not grader(None, "cos(0.4)/sin(0.4)")['ok']
    # Correct answers with forbidden function raise error:
    expect = r"Invalid Input: function\(s\) 'tan' not permitted in answer"
    with raises(InvalidInput, match=expect):
        grader(None, "tan(0.4)")
    expect = r"Invalid Input: 'TAN' not permitted in answer as a function \(did you mean 'tan'\?\)"
    with raises(UndefinedFunction, match=expect):
        grader(None, "TAN(0.4)")

    grader = FormulaGrader(
        answers="1",
        whitelist=[None]
    )
    assert grader(None, "1")['ok']
    expect = r"Invalid Input: function\(s\) 'cos' not permitted in answer"
    with raises(InvalidInput, match=expect):
        grader(None, "cos(0)")

def test_fg_blacklist_whitelist_config_errors():
    with raises(ConfigError, match="Cannot whitelist and blacklist at the same time"):
        FormulaGrader(
            answers="5",
            blacklist=['tan'],
            whitelist=['tan']
        )

    with raises(ConfigError, match="Unknown function in blacklist: test"):
        FormulaGrader(
            answers="5",
            blacklist=['test']
        )

    with raises(ConfigError, match="Unknown function in whitelist: test"):
        FormulaGrader(
            answers="5",
            whitelist=['test']
        )

def test_fg_forbidden():
    """Test FormulaGrader with forbidden strings in input"""
    grader = FormulaGrader(
        answers="2*sin(x)*cos(x)",
        variables=['x'],
        forbidden_strings=['+ x', '- x', '*x']
    )
    assert grader(None, '2*sin(x)*cos(x)')['ok']

    # If the answer is mathematically correct AND contains forbidden strings, raise an error:
    with raises(InvalidInput, match="Invalid Input: This particular answer is forbidden"):
        grader(None, "sin(2 * x)")
    with raises(InvalidInput, match="Invalid Input: This particular answer is forbidden"):
        grader(None, "sin(x    +    x)")
    with raises(InvalidInput, match="Invalid Input: This particular answer is forbidden"):
        grader(None, "sin(3*x    -x)")

    # If the answer is mathematically incorrect AND contains a forbidden string, mark it wrong
    assert not grader(None, "sin(3*x)")['ok']

def test_fg_variables():
    """General test of FormulaGrader using variables"""
    grader = FormulaGrader(
        answers="1+x^2+y^2",
        variables=['x', 'y']
    )
    assert grader(None, '(x+y+1)^2 - 2*x-2*y-2*x*y')['ok']

def test_fg_required():
    """Test FormulaGrader with required functions in input"""
    grader = FormulaGrader(
        answers="sin(x)/cos(x)",
        variables=['x'],
        required_functions=['sin', 'cos']
    )
    assert grader(None, 'sin(x)/cos(x)')['ok']
    with raises(InvalidInput, match="Invalid Input: Answer must contain the function sin"):
        grader(None, "tan(x)")

def test_fg_sampling():
    """Test various sampling methods in FormulaGrader"""
    grader = FormulaGrader(
        answers="x^2+y^2+z^2",
        variables=['x', 'y', 'z', 'w'],
        sample_from={
            'x': 2,
            'y': (1, 3, 5),
            'z': [1, 5]
        }
    )
    assert grader(None, 'x^2+y^2+z^2')['ok']
    assert isinstance(grader.config["sample_from"]['x'], DiscreteSet)
    assert isinstance(grader.config["sample_from"]['y'], DiscreteSet)
    assert isinstance(grader.config["sample_from"]['z'], RealInterval)
    assert isinstance(grader.config["sample_from"]['w'], RealInterval)

    with raises(MultipleInvalid, match=r"extra keys not allowed @ data\[u?'w'\]"):
        grader = FormulaGrader(variables=['x'], sample_from={'w': 2})

    grader = FormulaGrader(
        answers="z^2",
        variables=['z'],
        sample_from={'z': ComplexSector()}
    )
    assert grader(None, '(z-1)*(z+1)+1')['ok']

    grader = FormulaGrader(
        answers="z^2",
        variables=['z'],
        sample_from={'z': ComplexRectangle()}
    )
    assert grader(None, '(z-1)*(z+1)+1')['ok']

    grader = FormulaGrader(
        answers="z^2",
        variables=['z'],
        sample_from={'z': IntegerRange()}
    )
    assert grader(None, '(z-1)*(z+1)+1')['ok']

    grader = FormulaGrader(
        answers="z^2",
        variables=['z'],
        sample_from={'z': RealInterval()}
    )
    assert grader(None, '(z-1)*(z+1)+1')['ok']

    grader = FormulaGrader(
        answers="z^2",
        variables=['z'],
        sample_from={'z': DiscreteSet((1, 3, 5))}
    )
    assert grader(None, '(z-1)*(z+1)+1')['ok']

def test_fg_function_sampling():
    """Test random functions in FormulaGrader"""
    grader = FormulaGrader(
        answers="hello(x)",
        variables=['x'],
        user_functions={'hello': RandomFunction()}
    )
    assert grader(None, 'hello(x)')['ok']
    assert isinstance(grader.random_funcs['hello'], RandomFunction)

    grader = FormulaGrader(
        answers="hello(x)",
        variables=['x'],
        user_functions={'hello': [lambda x: x*x]}
    )
    assert isinstance(grader.random_funcs['hello'], SpecificFunctions)
    assert grader(None, 'hello(x)')['ok']

    grader = FormulaGrader(
        answers="hello(x)",
        variables=['x'],
        user_functions={'hello': [np.sin, np.cos, np.tan]}
    )
    assert isinstance(grader.random_funcs['hello'], SpecificFunctions)
    assert grader(None, 'hello(x)')['ok']

    grader = FormulaGrader(
        answers="hello(x)",
        variables=['x'],
        user_functions={'hello': SpecificFunctions([np.sin, np.cos, np.tan])}
    )
    assert isinstance(grader.random_funcs['hello'], SpecificFunctions)
    assert grader(None, 'hello(x)')['ok']

def test_fg_custom_comparers():

    def is_coterminal_and_large(comparer_params, student_input, utils):
        answer = comparer_params[0]
        min_value = comparer_params[1]
        reduced = student_input % (360)
        return utils.within_tolerance(answer, reduced) and student_input > min_value

    grader = FormulaGrader(
        answers={
            'comparer': is_coterminal_and_large,
            'comparer_params': ['150 + 50', '360 * 2'],
        },
        tolerance='1%'
    )
    assert grader(None, '200 + 3*360') == {'grade_decimal': 1, 'msg': '', 'ok': True}

    assert grader(None, '199 + 3*360') == {'grade_decimal': 1, 'msg': '', 'ok': True}
    assert grader(None, '197 + 3*360') == {'grade_decimal': 0, 'msg': '', 'ok': False}

def test_fg_config_expect():

    # If trying to use comparer, a detailed validation error is raised
    expect = ("to have 3 arguments, instead it has 2 for dictionary value @ "
              r"data\[u?'answers'\]\[0\]\[u?'expect'\]\[0\]\[u?'comparer'\]")
    with raises(Error, match=expect):
        FormulaGrader(
            answers={
                'comparer': lambda x, y: x + y,
                'comparer_params': ['150 + 50', '360 * 2']
            }
        )

    # If not, a simpler error is raised:
    expect = ("Something's wrong with grader's 'answers' configuration key. "
              "Please see documentation for accepted formats.")
    with raises(Error, match=expect):
        FormulaGrader(answers=5)

def squareit(x):
    return x**2

def test_fg_debug_log():
    set_seed(0)
    grader = FormulaGrader(
        answers='x^2 + f(y) + z',
        variables=['x', 'y', 'z'],
        sample_from={
            'z': ComplexRectangle()
        },
        blacklist=['sin', 'cos', 'tan'],
        user_functions={
            'f': RandomFunction(),
            'square': squareit
            },
        samples=2,
        debug=True
    )
    result = grader(None, 'z + x*x + f(y)')

    message = (
    "<pre>MITx Grading Library Version {version}<br/>\n"
    "Running on edX using python {python_version}<br/>\n"
    "Student Response:<br/>\n"
    "z + x*x + f(y)<br/>\n"
    "<br/>\n"
    "==============================================================<br/>\n"
    "FormulaGrader Debug Info<br/>\n"
    "==============================================================<br/>\n"
    "Functions available during evaluation and allowed in answer:<br/>\n"
    "{{'abs': <function absolute at 0x...>,<br/>\n"
    " 'arccos': <function arccos at 0x...>,<br/>\n"
    " 'arccosh': <function arccosh at 0x...>,<br/>\n"
    " 'arccot': <function arccot at 0x...>,<br/>\n"
    " 'arccoth': <function arccoth at 0x...>,<br/>\n"
    " 'arccsc': <function arccsc at 0x...>,<br/>\n"
    " 'arccsch': <function arccsch at 0x...>,<br/>\n"
    " 'arcsec': <function arcsec at 0x...>,<br/>\n"
    " 'arcsech': <function arcsech at 0x...>,<br/>\n"
    " 'arcsin': <function arcsin at 0x...>,<br/>\n"
    " 'arcsinh': <function arcsinh at 0x...>,<br/>\n"
    " 'arctan': <function arctan at 0x...>,<br/>\n"
    " 'arctan2': <function arctan2 at 0x...>,<br/>\n"
    " 'arctanh': <function arctanh at 0x...>,<br/>\n"
    " 'ceil': <function ceil at 0x...>,<br/>\n"
    " 'conj': &lt;ufunc 'conjugate'&gt;,<br/>\n"
    " 'cosh': <function cosh at 0x...>,<br/>\n"
    " 'cot': <function cot at 0x...>,<br/>\n"
    " 'coth': <function coth at 0x...>,<br/>\n"
    " 'csc': <function csc at 0x...>,<br/>\n"
    " 'csch': <function csch at 0x...>,<br/>\n"
    " 'exp': <function exp at 0x...>,<br/>\n"
    " 'f': <function random_function at 0x...>,<br/>\n"
    " 'fact': <function factorial at 0x...>,<br/>\n"
    " 'factorial': <function factorial at 0x...>,<br/>\n"
    " 'floor': <function floor at 0x...>,<br/>\n"
    " 'im': <function imag at 0x...>,<br/>\n"
    " 'kronecker': <function kronecker at 0x...>,<br/>\n"
    " 'ln': <function log at 0x...>,<br/>\n"
    " 'log10': <function log10 at 0x...>,<br/>\n"
    " 'log2': <function log2 at 0x...>,<br/>\n"
    " 'max': <function max at 0x...>,<br/>\n"
    " 'min': <function min at 0x...>,<br/>\n"
    " 're': <function real at 0x...>,<br/>\n"
    " 'sec': <function sec at 0x...>,<br/>\n"
    " 'sech': <function sech at 0x...>,<br/>\n"
    " 'sinh': <function sinh at 0x...>,<br/>\n"
    " 'sqrt': <function sqrt at 0x...>,<br/>\n"
    " 'square': <function squareit at 0x...>,<br/>\n"
    " 'tanh': <function tanh at 0x...>}}<br/>\n"
    "Functions available during evaluation and disallowed in answer:<br/>\n"
    "{{'cos': <function cos at 0x...>,<br/>\n"
    " 'sin': <function sin at 0x...>,<br/>\n"
    " 'tan': <function tan at 0x...>}}<br/>\n"
    "<br/>\n"
    "<br/>\n"
    "==========================================<br/>\n"
    "Evaluation Data for Sample Number 1 of 2<br/>\n"
    "==========================================<br/>\n"
    "Variables:<br/>\n"
    "{{'e': 2.718281828459045,<br/>\n"
    " 'i': 1j,<br/>\n"
    " 'j': 1j,<br/>\n"
    " 'pi': 3.141592653589793,<br/>\n"
    " 'x': 3.195254015709299,<br/>\n"
    " 'y': 3.860757465489678,<br/>\n"
    " 'z': (2.205526752143288+2.0897663659937935j)}}<br/>\n"
    "Student Eval: (14.7111745179+2.08976636599j)<br/>\n"
    "Compare to:  [(14.711174517877566+2.0897663659937935j)]<br/>\n"
    "<br/>\n"
    "<br/>\n"
    "==========================================<br/>\n"
    "Evaluation Data for Sample Number 2 of 2<br/>\n"
    "==========================================<br/>\n"
    "Variables:<br/>\n"
    "{{'e': 2.718281828459045,<br/>\n"
    " 'i': 1j,<br/>\n"
    " 'j': 1j,<br/>\n"
    " 'pi': 3.141592653589793,<br/>\n"
    " 'x': 2.694619197355619,<br/>\n"
    " 'y': 3.5835764522666245,<br/>\n"
    " 'z': (1.875174422525385+2.7835460015641598j)}}<br/>\n"
    "Student Eval: (11.9397106851+2.78354600156j)<br/>\n"
    "Compare to:  [(11.93971068506166+2.7835460015641598j)]<br/>\n"
    "<br/>\n"
    "<br/>\n"
    "==========================================<br/>\n"
    "Comparison Data for All 2 Samples<br/>\n"
    "==========================================<br/>\n"
    "Comparer Function: EqualityComparer({{'transform': <function identity_transform at 0x...>}})<br/>\n"
    "Comparison Results:<br/>\n"
    "[{{'grade_decimal': 1.0, 'msg': '', 'ok': True}},<br/>\n"
    " {{'grade_decimal': 1.0, 'msg': '', 'ok': True}}]<br/>\n"
    "</pre>"
    ).format(version=VERSION, python_version=platform.python_version())
    message = message.replace("<func", "&lt;func").replace("...>", "...&gt;")
    expected = round_decimals_in_string(message)
    result_msg = round_decimals_in_string(result['msg']).replace(
        'test_fg_debug_log.<locals>.', '')
    assert expected == result_msg

def test_fg_evaluates_siblings_appropriately():
    grader=ListGrader(
        answers=['sibling_3 + 1', 'sibling_1^2', 'x'],
        subgraders=FormulaGrader(variables=['x']),
        ordered=True
    )
    # All correct!
    result = grader(None, ['x + 1', 'x^2 + 2*x + 1', 'x'])
    expected = {
        'input_list': [
            {'grade_decimal': 1, 'msg': '', 'ok': True},
            {'grade_decimal': 1, 'msg': '', 'ok': True},
            {'grade_decimal': 1, 'msg': '', 'ok': True}],
        'overall_message': ''
    }
    assert result == expected

    # First input wrong, but other two consistent
    result = grader(None, ['x + 2', 'x^2 + 4*x + 4', 'x'])
    expected = {
        'input_list': [
            {'grade_decimal': 0, 'msg': '', 'ok': False},
            {'grade_decimal': 1, 'msg': '', 'ok': True},
            {'grade_decimal': 1, 'msg': '', 'ok': True}],
        'overall_message': ''
    }
    assert result == expected

    # Cannot grade, missing a required input
    match='Cannot grade answer, a required input is missing.'
    with raises(MissingInput, match=match):
        result = grader(None, ['', 'x^2 + 2*x + 1', 'x'])

def test_fg_evals_numbered_variables_in_siblings():
    subgrader = FormulaGrader(
        numbered_vars=['x']
    )
    grader = ListGrader(
        answers=['x_{1}', 'x_{2} + sibling_1'],
        subgraders=subgrader,
        ordered=True
    )

    results = []
    side_effect = log_results(results)(subgrader.get_sibling_formulas)
    with mock.patch.object(subgrader, 'get_sibling_formulas', side_effect=side_effect):
        grader(None, ['x_{0}+1', 'x_{1} + 1'])
        # get_sibling_formulas should be called twice, once for each input
        assert len(results) == 2
        # the first call should not provide any sibling formulas
        assert results[0] == {}
        # The second call should provide only the first sibling formula
        assert results[1] == {'sibling_1': 'x_{0}+1'}

def test_siblings_in_dependent_samplers():
    grader = ListGrader(
        answers=['1', 'x'],
        subgraders=[
            FormulaGrader(),
            FormulaGrader(variables=['x'], sample_from={'x': DependentSampler(formula='sibling_1+1')})
        ],
        ordered=True
    )

    submission = ['1', '2']
    expected_result = {
        'overall_message': '',
        'input_list': [
            {'ok': True, 'grade_decimal': 1, 'msg': ''},
            {'ok': True, 'grade_decimal': 1, 'msg': ''},
        ]
    }
    assert grader(None, submission) == expected_result

    submission = ['2', '3']
    expected_result = {
        'overall_message': '',
        'input_list': [
            {'ok': False, 'grade_decimal': 0, 'msg': ''},
            {'ok': True, 'grade_decimal': 1, 'msg': ''},
        ]
    }
    assert grader(None, submission) == expected_result

def test_ng_config():
    """Test that the NumericalGrader config bars unwanted entries"""
    expect = r"not a valid value for dictionary value @ data\[u?'failable_evals'\]. Got 1"
    with raises(Error, match=expect):
        NumericalGrader(
            answers="1",
            failable_evals=1
        )

    expect = r"not a valid value for dictionary value @ data\[u?'samples'\]. Got 2"
    with raises(Error, match=expect):
        NumericalGrader(
            answers="1",
            samples=2
        )

    expect = (r"length of value must be at most 0 for dictionary value "
              r"@ data\[u?'variables'\]. Got \[u?'x'\]")
    with raises(Error, match=expect):
        NumericalGrader(
            answers="1",
            variables=["x"]
        )

    expect = (r"extra keys not allowed @ data\[u?'sample_from'\]\[u?'x'\]. Got "
              r"RealInterval\({u?'start': 1, u?'stop': 5}\)")
    with raises(Error, match=expect):
        NumericalGrader(
            answers="1",
            sample_from={"x": RealInterval()}
        )

    expect = (r"not a valid value for dictionary value @ data\[u?'user_functions'\]\[u?'f'\]. "
              r"Got RandomFunction")
    with raises(Error, match=expect):
        NumericalGrader(
            answers="1",
            user_functions={"f": RandomFunction()}
        )

    expect = (r"not a valid value for dictionary value @ data\[u?'user_functions'\]\[u?'f'\]. " + \
              r"Got \[<ufunc 'sin'>, <ufunc 'cos'>\]")
    with raises(Error, match=expect):
        NumericalGrader(
            answers="1",
            user_functions={"f": [np.sin, np.cos]}
        )

def test_docs():
    """Test that the documentation examples work as expected"""
    grader = FormulaGrader(
        answers='1+x^2+y',
        variables=['x', 'y']
    )
    assert grader(None, '1+x^2+y')['ok']

    grader = FormulaGrader(
        answers='1+x^2+y+z/2',
        variables=['x', 'y', 'z'],
        sample_from={
            'x': ComplexRectangle(),
            'y': [2, 6],
            'z': (1, 3, 4, 8)
        }
    )
    assert grader(None, '1+x^2+y+z/2')['ok']

    grader = FormulaGrader(
        answers='a_{0} + a_{1}*x + 1/2*a_{2}*x^2',
        variables=['x'],
        numbered_vars=['a'],
        sample_from={
            'x': [-5, 5],
            'a': [-10, 10]
        }
    )
    assert grader(None, 'a_{0} + a_{1}*x + 1/2*a_{2}*x^2')['ok']

    grader = FormulaGrader(
        answers='1+x^2',
        variables=['x'],
        samples=10
    )
    assert grader(None, '1+x^2')['ok']

    grader = FormulaGrader(
        answers='1+x^2',
        variables=['x'],
        samples=10,
        failable_evals=1
    )
    assert grader(None, '1+x^2')['ok']

    grader = FormulaGrader(
        answers='abs(z)^2',
        variables=['z'],
        sample_from={
            'z': ComplexRectangle()
        }
    )
    assert grader(None, 'abs(z)^2')['ok']

    grader = FormulaGrader(
        answers='sqrt(1 - cos(x)^2)',
        variables=['x'],
        sample_from={'x': [0, np.pi]},
        blacklist=['sin']
    )
    assert grader(None, 'sqrt(1 - cos(x)^2)')['ok']

    grader = FormulaGrader(
        answers='sin(x)/cos(x)',
        variables=['x'],
        whitelist=['sin', 'cos']
    )
    assert grader(None, 'sin(x)/cos(x)')['ok']

    grader = FormulaGrader(
        answers='pi/2-x',
        variables=['x'],
        whitelist=[None]
    )
    assert grader(None, 'pi/2-x')['ok']

    grader = FormulaGrader(
        answers='2*sin(theta)*cos(theta)',
        variables=['theta'],
        required_functions=['sin', 'cos']
    )
    assert grader(None, '2*sin(theta)*cos(theta)')['ok']

    grader = FormulaGrader(
        answers='x*x',
        variables=['x'],
        user_functions={'f': lambda x: x*x}
    )
    assert grader(None, 'x^2')['ok']

    grader = FormulaGrader(
        answers="f''(x)",
        variables=['x'],
        user_functions={"f''": lambda x: x*x}
    )
    assert grader(None, "f''(x)")['ok']

    grader = FormulaGrader(
        answers="x^2",
        variables=['x'],
        user_functions={"sin": lambda x: x*x},
        suppress_warnings=True
    )
    assert grader(None, 'sin(x)')['ok']

    grader = FormulaGrader(
        answers="f(x)",
        variables=['x'],
        user_functions={"f": [np.sin, np.cos]}
    )
    assert grader(None, 'f(x)')['ok']

    grader = FormulaGrader(
        answers="f''(x) + omega^2*f(x)",
        variables=['x', 'omega'],
        user_functions={
            "f": RandomFunction(),
            "f''": RandomFunction()
        }
    )
    assert grader(None, "f''(x)+omega^2*f(x)")['ok']

    grader = FormulaGrader(
        answers='1/sqrt(1-v^2/c^2)',
        variables=['v'],
        user_constants={
            'c': 3e8
        }
    )
    assert grader(None, '1/sqrt(1-v^2/c^2)')['ok']

    grader = FormulaGrader(
        answers='2*sin(theta)*cos(theta)',
        variables=['theta'],
        forbidden_strings=['*theta', 'theta*', 'theta/', '+theta', 'theta+', '-theta', 'theta-'],
        forbidden_message="Your answer should only use trigonometric functions acting on theta, not multiples of theta"
    )
    assert grader(None, '2*sin(theta)*cos(theta)')['ok']

    grader = FormulaGrader(
        answers='2*sin(theta)*cos(theta)',
        variables=['theta'],
        tolerance=0.00001
    )
    assert grader(None, '2*sin(theta)*cos(theta)')['ok']

    grader = FormulaGrader(
        answers='2*m',
        variables=['m'],
        metric_suffixes=True
    )
    assert grader(None, '2*m')['ok']
    assert not grader(None, '2m')['ok']

    def is_coterminal(comparer_params_eval, student_eval, utils):
        answer = comparer_params_eval[0]
        reduced = student_eval % (360)
        return utils.within_tolerance(answer, reduced)

    grader = FormulaGrader(
        answers={
            'comparer': is_coterminal,
            'comparer_params': ['b^2/a'],
        },
        variables=['a', 'b'],
        tolerance='1%'
    )
    assert grader(None, 'b^2/a')['ok']
    assert grader(None, 'b^2/a + 720')['ok']
    assert not grader(None, 'b^2/a + 225')['ok']

def test_empty_input():
    """Make sure that empty input doesn't crash"""
    grader = FormulaGrader(answers="1")
    assert not grader(None, '')['ok']

def test_errors():
    """
    Test unhandled error catching.
    Div by zero is the only one I'm aware of at the moment!
    """
    grader = FormulaGrader(
        answers='4'
    )
    with raises(CalcError, match="Division by zero occurred. Check your input's denominators."):
        grader(None, '1/0')

def test_numbered_vars():
    """Test that numbered variables work"""
    grader = FormulaGrader(
        answers='a_{0}+a_{1}+a_{-1}',
        variables=['a_{0}'],
        numbered_vars=['a'],
        sample_from={
            'a_{0}': [-5, 5],
            'a': [-10, 10]
        }
    )
    assert grader(None, 'a_{0}+a_{1}+a_{-1}')['ok']
    with raises(UndefinedVariable, match="'a' not permitted in answer as a variable"):
        grader(None, 'a')

def test_whitespace_stripping():
    """Test that formulas work regardless of whitespace"""
    grader = FormulaGrader(
        variables=['x_{ab}'],
        answers='x _ { a b }'
    )
    assert grader(None, 'x_{a b}')['ok']

def test_default_comparer():
    """Tests setting and resetting default_comparer"""

    def silly_comparer(comparer_params_eval, student_eval, utils):
        return utils.within_tolerance(1, student_eval)

    FormulaGrader.set_default_comparer(silly_comparer)
    silly_grader = FormulaGrader(answers='pi')
    FormulaGrader.reset_default_comparer()
    grader = FormulaGrader(answers='pi')

    silly_grader.config['answers'][0]['expect'][0]['comparer'] is silly_comparer
    assert silly_grader(None, '1')['ok']
    grader.config['answers'][0]['expect'][0]['comparer'] is equality_comparer
    assert not grader(None, '1')['ok']
    assert grader(None, '3.141592653')['ok']

def test_instructor_vars():
    """Ensures that instructor variables are not available to students"""
    grader = FormulaGrader(
        answers='sin(x)/cos(x)',
        variables=['x', 's', 'c'],
        numbered_vars=['y'],
        sample_from={
            'x': [-3.14159, 3.14159],
            's': DependentSampler(depends=["x"], formula="sin(x)"),
            'c': DependentSampler(depends=["x"], formula="cos(x)")
        },
        instructor_vars=['x', 'pi', 'y_{0}', 'nothere']  # nothere will be ignored
    )

    assert grader(None, 's/c')['ok']
    assert not grader(None, 'y_{1}')['ok']
    with raises(UndefinedVariable, match="'x' not permitted in answer as a variable"):
        grader(None, 'tan(x)')
    with raises(UndefinedVariable, match="'pi' not permitted in answer as a variable"):
        grader(None, 'pi')
    with raises(UndefinedVariable, match=r"'y_\{0\}' not permitted in answer as a variable"):
        grader(None, 'y_{0}')

def test_dependentsampler():
    # Ensure that dependentsampler can make use of user-defined functions
    grader = FormulaGrader(
        answers='y',
        variables=['x', 'y'],
        user_functions={'f': lambda x: x**2},
        sample_from={
            'y': DependentSampler(depends=["x"], formula="f(x)")
        }
    )
    assert grader(None, 'y')['ok']
    assert grader(None, 'x^2')['ok']

def test_infinity():
    grader = FormulaGrader(
        answers="infty",
        allow_inf=True
    )
    assert grader(None, 'infty')['ok']
    assert not grader(None, '-infty')['ok']
    assert grader.default_variables['infty'] == float('inf')

    grader = FormulaGrader(
        answers='infty',
        user_constants={'infty': float('inf')}
    )
    assert 'infty' not in grader.default_variables
    with raises(CalcError, match='Numerical overflow occurred. Does your expression generate very large numbers?'):
        grader(None, 'infty')
