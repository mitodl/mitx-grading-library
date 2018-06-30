"""
Tests for FormulaGrader and NumericalGrader
"""
from __future__ import division
from pytest import raises
from mock import Mock
import numpy as np
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
    InvalidInput,
)
from mitxgraders.voluptuous import Error, MultipleInvalid
from mitxgraders.sampling import set_seed
from mitxgraders.version import __version__ as VERSION

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

    expect = 'Invalid Input: Im, Re not permitted in answer as a function ' + \
             '\(did you mean im, re\?\)'
    with raises(CalcError, match=expect):
        grader(None, "Im(3) + Re(2)")

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
             "These functions can only be used on nonnegative integers."
    with raises(CalcError, match=expect):
        grader(None, "fact(-1)")
    with raises(CalcError, match=expect):
        grader(None, "fact(1.5)")

    expect = ("There was an error evaluating csc\(...\). "
              "Its input does not seem to be in its domain.")
    with raises(CalcError, match=expect):
        grader(None, 'csc(0)')

    expect = "There was an error evaluating sinh\(...\). \(Numerical overflow\)."
    with raises(CalcError, match=expect):
        grader(None, 'sinh(10000)')

    expect = ("There was an error evaluating arccosh\(...\). "
              "Its input does not seem to be in its domain.")
    with raises(CalcError, match=expect):
        grader(None, 'arccosh(0)')

    expect = "Division by zero occurred. Check your input's denominators."
    with raises(CalcError, match=expect):
        grader(None, '1/0')

    expect = "Numerical overflow occurred. Does your input contain very large numbers?"
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

def test_fg_blacklist_grading():
    """Test FormulaGrader with blacklists and whitelists"""
    grader = FormulaGrader(
        answers="sin(0.4)/cos(0.4)",
        user_functions={"hello": np.tan},
        blacklist=['tan'],
        case_sensitive=False
    )
    assert grader(None, "hello(0.4)")['ok']
    # Incorrect answers with forbidden function are marked wrong:
    assert not grader(None, "cos(0.4)/sin(0.4)")['ok']
    # Correct answers with forbidden function raise error:
    assert grader(None, "sin(0.4)/cos(0.4)")['ok']
    expect = "Invalid Input: function(s) 'tan' not permitted in answer"
    with raises(InvalidInput, message=expect):
        grader(None, "tan(0.4)")
    expect = "Invalid Input: function(s) 'TAN', 'Tan' not permitted in answer"
    with raises(InvalidInput, message=expect):
        grader(None, "(TAN(0.4) + Tan(0.4))/2")

def test_fg_whitelist_grading():
    grader = FormulaGrader(
        answers="sin(0.4)/cos(0.4)",
        user_functions={"hello": np.tan},
        whitelist=['cos', 'sin'],
        case_sensitive=False
    )
    assert grader(None, "hello(0.4)")['ok']


    assert grader(None, "sin(0.4)/cos(0.4)")['ok']
    # Incorrect answers with forbidden function are marked wrong:
    assert not grader(None, "cos(0.4)/sin(0.4)")['ok']
    # Correct answers with forbidden function raise error:
    expect = "Invalid Input: function(s) 'tan' not permitted in answer"
    with raises(InvalidInput, message=expect):
        grader(None, "tan(0.4)")
    expect = "Invalid Input: function(s) 'tan' not permitted in answer"
    with raises(InvalidInput, message=expect):
        grader(None, "TAN(0.4)")

    grader = FormulaGrader(
        answers="1",
        whitelist=[None]
    )
    assert grader(None, "1")['ok']
    expect = "Invalid Input: function(s) 'cos' not permitted in answer"
    with raises(InvalidInput, message=expect):
        grader(None, "cos(0)")

def test_fg_blacklist_whitelist_config_errors():
    with raises(ConfigError, message="Cannot whitelist and blacklist at the same time"):
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
        answers="2*sin(x)*cos(x)",
        variables=['x'],
        forbidden_strings=['+ x', '- x', '*x'],
        case_sensitive=False
    )
    assert grader(None, '2*sin(x)*cos(x)')['ok']

    # If the answer is mathematically correct AND contains forbidden strings, raise an error:
    with raises(InvalidInput, match="Invalid Input: This particular answer is forbidden"):
        grader(None, "sin(2 * x)")
    with raises(InvalidInput, match="Invalid Input: This particular answer is forbidden"):
        grader(None, "sin(x    +    x)")
    with raises(InvalidInput, match="Invalid Input: This particular answer is forbidden"):
        grader(None, "sin(3*X    -X)")

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

def test_fg_custom_comparers():

    def is_coterminal_and_large(comparer_params, student_input, utils):
        answer = comparer_params[0]
        min_value = comparer_params[1]
        reduced = student_input % (360)
        return utils.within_tolerance(answer, reduced) and student_input > min_value

    mock = Mock(side_effect=is_coterminal_and_large,
                # The next two kwargs ensure that the Mock behaves nicely for inspect.getargspec
                spec=is_coterminal_and_large,
                func_code=is_coterminal_and_large.func_code,)

    grader = FormulaGrader(
        answers={
            'comparer': mock,
            'comparer_params': ['150 + 50', '360 * 2'],
        },
        tolerance='1%'
    )
    assert grader(None, '200 + 3*360') == {'grade_decimal': 1, 'msg': '', 'ok': True}
    mock.assert_called_with([200, 720], 1280, grader.comparer_utils)

    assert grader(None, '199 + 3*360') == {'grade_decimal': 1, 'msg': '', 'ok': True}
    assert grader(None, '197 + 3*360') == {'grade_decimal': 0, 'msg': '', 'ok': False}

def test_fg_config_expect():

    # If trying to use comparer, a detailed validation error is raised
    expect = ("to have 3 arguments, instead it has 2 for dictionary value @ "
              "data\['answers'\]\[0\]\['expect'\]\['comparer'\]")
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

def test_fg_debug_log():
    set_seed(0)
    grader = FormulaGrader(
        answers='x^2 + f(y) + z',
        variables=['x', 'y', 'z'],
        sample_from={
            'z': ComplexRectangle()
        },
        blacklist=['sin', 'cos'],
        user_functions={'f': RandomFunction()},
        samples=2,
        debug=True
    )
    result = grader(None, 'z + x*x + f(y)')

    message = (
        "<pre>MITx Grading Library Version {version}<br/>\n"
        "Student Response:<br/>\n"
        "z + x*x + f(y)<br/>\n"
        "<br/>\n"
        "==============================================================<br/>\n"
        "FormulaGrader Debug Info<br/>\n"
        "==============================================================<br/>\n"
        "Functions available during evaluation and allowed in answer:<br/>\n"
        "{{   'abs': <function f at 0x...>,<br/>\n"
        "    'arccos': <function f at 0x...>,<br/>\n"
        "    'arccosh': <function f at 0x...>,<br/>\n"
        "    'arccot': <function f at 0x...>,<br/>\n"
        "    'arccoth': <function f at 0x...>,<br/>\n"
        "    'arccsc': <function f at 0x...>,<br/>\n"
        "    'arccsch': <function f at 0x...>,<br/>\n"
        "    'arcsec': <function f at 0x...>,<br/>\n"
        "    'arcsech': <function f at 0x...>,<br/>\n"
        "    'arcsin': <function f at 0x...>,<br/>\n"
        "    'arcsinh': <function f at 0x...>,<br/>\n"
        "    'arctan': <function f at 0x...>,<br/>\n"
        "    'arctanh': <function f at 0x...>,<br/>\n"
        "    'conj': <function f at 0x...>,<br/>\n"
        "    'cosh': <function f at 0x...>,<br/>\n"
        "    'cot': <function f at 0x...>,<br/>\n"
        "    'coth': <function f at 0x...>,<br/>\n"
        "    'csc': <function f at 0x...>,<br/>\n"
        "    'csch': <function f at 0x...>,<br/>\n"
        "    'exp': <function f at 0x...>,<br/>\n"
        "    'f': <function f at 0x...>,<br/>\n"
        "    'fact': <function f at 0x...>,<br/>\n"
        "    'factorial': <function f at 0x...>,<br/>\n"
        "    'im': <function f at 0x...>,<br/>\n"
        "    'ln': <function f at 0x...>,<br/>\n"
        "    'log10': <function f at 0x...>,<br/>\n"
        "    'log2': <function f at 0x...>,<br/>\n"
        "    're': <function f at 0x...>,<br/>\n"
        "    'sec': <function f at 0x...>,<br/>\n"
        "    'sech': <function f at 0x...>,<br/>\n"
        "    'sinh': <function f at 0x...>,<br/>\n"
        "    'sqrt': <function f at 0x...>,<br/>\n"
        "    'tan': <function f at 0x...>,<br/>\n"
        "    'tanh': <function f at 0x...>}}<br/>\n"
        "Functions available during evaluation and disallowed in answer:<br/>\n"
        "{{   'cos': <function f at 0x...>, 'sin': <function f at 0x...>}}<br/>\n"
        "<br/>\n"
        "<br/>\n"
        "==========================================<br/>\n"
        "Evaluation Data for Sample Number 1 of 2<br/>\n"
        "==========================================<br/>\n"
        "Variables:<br/>\n"
        "{{   'e': 2.718281828459045,<br/>\n"
        "    'i': 1j,<br/>\n"
        "    'j': 1j,<br/>\n"
        "    'pi': 3.141592653589793,<br/>\n"
        "    'x': 3.195254015709299,<br/>\n"
        "    'y': 3.860757465489678,<br/>\n"
        "    'z': (2.205526752143288+2.0897663659937935j)}}<br/>\n"
        "Student Eval: (14.7111745179+2.08976636599j)<br/>\n"
        "Compare to:  [(14.711174517877566+2.0897663659937935j)]<br/>\n"
        "Comparer Function: <function default_equality_comparer at 0x...><br/>\n"
        "Comparison Satisfied: True<br/>\n"
        "<br/>\n"
        "<br/>\n"
        "==========================================<br/>\n"
        "Evaluation Data for Sample Number 2 of 2<br/>\n"
        "==========================================<br/>\n"
        "Variables:<br/>\n"
        "{{   'e': 2.718281828459045,<br/>\n"
        "    'i': 1j,<br/>\n"
        "    'j': 1j,<br/>\n"
        "    'pi': 3.141592653589793,<br/>\n"
        "    'x': 2.694619197355619,<br/>\n"
        "    'y': 3.5835764522666245,<br/>\n"
        "    'z': (1.875174422525385+2.7835460015641598j)}}<br/>\n"
        "Student Eval: (11.9397106851+2.78354600156j)<br/>\n"
        "Compare to:  [(11.939710685061661+2.7835460015641598j)]<br/>\n"
        "Comparer Function: <function default_equality_comparer at 0x...><br/>\n"
        "Comparison Satisfied: True<br/>\n"
        "</pre>"
    ).format(version=VERSION)
    assert result['msg'] == message


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

    def is_coterminal(comparer_params_evals, student_eval, utils):
        answer = comparer_params_evals[0]
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
