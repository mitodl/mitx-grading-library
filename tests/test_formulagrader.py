"""
Tests for FormulaGrader and NumericalGrader
"""
from __future__ import division
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
    CalcError,
    ConfigError,
    InvalidInput
)
from mitxgraders.voluptuous import Error, MultipleInvalid
from pytest import raises
import numpy as np

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

def test_overriding_functions():
    grader = FormulaGrader(
        answers='z^2',
        variables=['z'],
        user_functions={'re': RandomFunction(), 'im': RandomFunction()},
        sample_from={
            'z': ComplexRectangle()
        }
    )
    learner_input = 're(z)^2 - im(z)^2 + 2*i*re(z)*im(z)'
    assert not grader(None, learner_input)['ok']

    grader = FormulaGrader(
        answers='tan(1)',
        user_functions={'sin': lambda x: x}
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
    grader = FormulaGrader(answers='2')

    expect = 'Invalid Input: pi not permitted in answer as a function ' + \
             '\(did you forget to use \* for multiplication\?\)'
    with raises(CalcError, match=expect):
        grader(None, "pi(3)")

    expect = 'Invalid Input: spin not permitted in answer as a function'
    with raises(CalcError, match=expect):
        grader(None, "spin(3)")

    expect = 'Invalid Input: R not permitted in answer as a variable'
    with raises(CalcError, match=expect):
        grader(None, "R")

    expect = 'Invalid Input: Parentheses are unmatched. 1 parentheses were opened but never closed.'
    with raises(CalcError, match=expect):
        grader(None, "5*(3")

    expect = 'Invalid Input: A closing parenthesis was found after segment 5\*\(3\), but ' + \
             'there is no matching opening parenthesis before it.'
    with raises(CalcError, match=expect):
        grader(None, "5*(3))")

    expect = "Invalid Input: Could not parse '5pp' as a formula"
    with raises(CalcError, match=expect):
        grader(None, "5pp")

    expect = "Error evaluating factorial\(\) or fact\(\) in input. " + \
             "These functions can only be used on positive integers."
    with raises(CalcError, match=expect):
        grader(None, "fact(-1)")
    with raises(CalcError, match=expect):
        grader(None, "fact(1.5)")

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

    expect = "Cannot have a negative percentage for dictionary value @ " + \
             "data\['tolerance'\]. Got '-1%'"
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
    with raises(CalcError, match="Invalid Input: Could not parse '20m' as a formula"):
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

    # Test with function names with primes at the end
    grader = FormulaGrader(
        answers="sin(0.4)/cos(0.4)",
        user_functions={"f'": np.tan}
    )
    assert grader(None, "f'(0.4)")['ok']

    grader = FormulaGrader(
        answers="sin(0.4)/cos(0.4)",
        user_functions={"function2name_2go''''''": np.tan}
    )
    assert grader(None, "function2name_2go''''''(0.4)")['ok']

    # Primes aren't allowed in the middle
    expect = "Invalid Input: Could not parse 'that'sbad\(1\)' as a formula"
    with raises(CalcError, match=expect):
        grader = FormulaGrader(
            answers="1",
            user_functions={"that'sbad": np.tan}
        )
        grader(None, "that'sbad(1)")

    expect = "1 is not a valid name for a function \(must be a string\)"
    with raises(ConfigError, match=expect):
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

    expect = "1 is not a valid name for a constant \(must be a string\)"
    with raises(ConfigError, match=expect):
        FormulaGrader(
            answers="1",
            user_constants={1: 5}
        )

def test_fg_blackwhite():
    """Test FormulaGrader with blacklists and whitelists"""
    grader = FormulaGrader(
        answers="sin(0.4)/cos(0.4)",
        user_functions={"hello": np.tan},
        blacklist=['tan'],
        case_sensitive=False
    )
    assert grader(None, "hello(0.4)")['ok']
    assert grader(None, "sin(0.4)/cos(0.4)")['ok']
    expect = 'Invalid Input: tan not permitted in answer as a function'
    with raises(CalcError, match=expect):
        grader(None, "tan(0.4)")
    expect = 'Invalid Input: TAN not permitted in answer as a function'
    with raises(CalcError, match=expect):
        grader(None, "TAN(0.4)")

    grader = FormulaGrader(
        answers="sin(0.4)/cos(0.4)",
        user_functions={"hello": np.tan},
        whitelist=['cos', 'sin'],
        case_sensitive=False
    )
    assert grader(None, "hello(0.4)")['ok']
    assert grader(None, "sin(0.4)/cos(0.4)")['ok']
    expect = 'Invalid Input: tan not permitted in answer as a function'
    with raises(CalcError, match=expect):
        grader(None, "tan(0.4)")
    expect = 'Invalid Input: TAN not permitted in answer as a function'
    with raises(CalcError, match=expect):
        grader(None, "TAN(0.4)")

    grader = FormulaGrader(
        answers="1",
        whitelist=[None]
    )
    assert grader(None, "1")['ok']
    expect = "Invalid Input: cos not permitted in answer as a function"
    with raises(CalcError, match=expect):
        grader(None, "cos(0)")
    assert not grader.functions   # Check for an empty dictionary

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

def test_fg_case_sensitive():
    """Test FormulaGrader with case insensitive input"""
    grader = FormulaGrader(
        answers="sin(pi)",
        case_sensitive=False,
        tolerance=1e-15
    )
    assert grader(None, "sin(pi)")['ok']
    assert grader(None, "0")['ok']
    assert grader(None, "Sin(Pi)")['ok']
    assert grader(None, "SIN(PI)")['ok']

def test_fg_forbidden():
    """Test FormulaGrader with forbidden strings in input"""
    grader = FormulaGrader(
        answers="sin(3*pi/2)",
        forbidden_strings=['3*pi', 'pi*3', 'pi/2'],
        case_sensitive=False
    )
    assert grader(None, '-1')['ok']
    with raises(InvalidInput, match="Invalid Input: This particular answer is forbidden"):
        grader(None, "3 * pi")
    with raises(InvalidInput, match="Invalid Input: This particular answer is forbidden"):
        grader(None, "pi * 3")
    with raises(InvalidInput, match="Invalid Input: This particular answer is forbidden"):
        grader(None, "sin(3*PI   /2)")
    with raises(InvalidInput, match="Invalid Input: This particular answer is forbidden"):
        grader(None, "sin(PI*3/      2)")

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
        required_functions=['sin', 'cos'],
        case_sensitive=False
    )
    assert grader(None, 'SIN(x)/COS(x)')['ok']
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

    with raises(MultipleInvalid, match="extra keys not allowed @ data\['w'\]"):
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


def test_ng_config():
    """Test that the NumericalGrader config bars unwanted entries"""
    expect = "not a valid value for dictionary value @ data\['failable_evals'\]. Got 1"
    with raises(Error, match=expect):
        NumericalGrader(
            answers="1",
            failable_evals=1
        )

    expect = "not a valid value for dictionary value @ data\['samples'\]. Got 2"
    with raises(Error, match=expect):
        NumericalGrader(
            answers="1",
            samples=2
        )

    expect = "not a valid value for dictionary value @ data\['variables'\]. Got \['x'\]"
    with raises(Error, match=expect):
        NumericalGrader(
            answers="1",
            variables=["x"]
        )

    expect = "not a valid value for dictionary value @ data\['sample_from'\]. " + \
             "Got {'x': RealInterval\({'start': 1, 'stop': 5}\)}"
    with raises(Error, match=expect):
        NumericalGrader(
            answers="1",
            sample_from={"x": RealInterval()}
        )

    expect = "not a valid value for dictionary value @ data\['user_functions'\]\['f'\]. " + \
             "Got RandomFunction\({'input_dim': 1, 'output_dim': 1, 'num_terms': 3, " + \
             "'amplitude': 10, 'center': 0}\)"
    with raises(Error, match=expect):
        NumericalGrader(
            answers="1",
            user_functions={"f": RandomFunction()}
        )

    expect = "not a valid value for dictionary value @ data\['user_functions'\]\['f'\]. " + \
             "Got \[<ufunc 'sin'>, <ufunc 'cos'>\]"
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
        user_functions={"sin": lambda x: x*x}
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
        answers='2*sin(theta)*cos(theta)',
        variables=['theta'],
        case_sensitive=False
    )
    assert grader(None, '2*Sin(theta)*Cos(theta)')['ok']

    grader = FormulaGrader(
        answers='2*m',
        variables=['m'],
        metric_suffixes=True
    )
    assert grader(None, '2*m')['ok']
    assert not grader(None, '2m')['ok']
