from __future__ import print_function, division, absolute_import

from pytest import raises
import numpy as np
from mitxgraders.version import __version__
from mitxgraders import CalcError
from mitxgraders.formulagrader.integralgrader import SumGrader, SummationError
from mitxgraders.exceptions import InvalidInput, ConfigError, MissingInput
from mitxgraders.helpers.compatibility import UNICODE_PREFIX
from mitxgraders.sampling import DependentSampler
from mitxgraders.helpers.calc import evaluator, DEFAULT_VARIABLES
from tests.helpers import round_decimals_in_string

# Configuration Error Test
def test_wrong_number_of_inputs_raises_error():
    grader = SumGrader(
        answers={
            'lower': 'a',
            'upper': 'b',
            'summand': 'x^2',
            'summation_variable': 'x'
        },
        input_positions={
            'summand': 1,
            'lower': 2,
            'upper': 3
        },
        variables=['a', 'b']
    )
    student_input = ['a', 'b']
    expected_message = (r"Expected 3 student inputs but found 2. "
                        r"Inputs should  appear in order \[u?'summand', u?'lower', u?'upper'\].")
    with raises(ConfigError, match=expected_message):
        grader(None, student_input)

def test_duplicate_input_positions():
    expected_message = "Key input_positions has repeated indices."
    with raises(ConfigError, match=expected_message):
        SumGrader(
            answers={
                'lower': 'a',
                'upper': 'b',
                'summand': 'x^2',
                'summation_variable': 'x'
            },
            input_positions={
                'summand': 1,
                'lower': 2,
                'upper': 3,
                'summation_variable': 3
            },
            variables=['a', 'b']
        )

def test_skipped_input_positions():
    expected_message = ("Key input_positions values must be consecutive positive "
                        "integers starting at 1")
    with raises(ConfigError, match=expected_message):
        SumGrader(
            answers={
                'lower': 'a',
                'upper': 'b',
                'summand': 'x^2',
                'summation_variable': 'x'
            },
            input_positions={
                'summand': 1,
                'summation_variable': 3,
            },
            variables=['a', 'b']
        )


# Input Error Tests
def test_user_provided_summation_conflict_raises_error():
    grader = SumGrader(
        answers={
            'lower': 'a',
            'upper': 'b',
            'summand': 'x^2',
            'summation_variable': 'x'
        },
        variables=['a', 'b']
    )
    student_input = ['a', 'b', 'pi^2', 'pi']
    msg = ("Cannot use pi as summation variable; it is already has "
           "another meaning in this problem.")
    with raises(InvalidInput, match=msg):
        grader(None, student_input)

def test_user_provided_summation_variable_has_invalid_name():
    grader = SumGrader(
        answers={
            'lower': 'a',
            'upper': 'b',
            'summand': 'x^2',
            'summation_variable': 'x'
        },
        variables=['a', 'b']
    )
    student_input = ['a', 'b', '_x^2', '_x']
    msg = ("Summation variable _x is an invalid variable name."
           "Variable name should begin with a letter and contain alphanumeric"
           "characters or underscores thereafter, but may end in single quotes.")
    with raises(InvalidInput, match=msg):
        grader(None, student_input)

def test_empty_input_raises_error():
    grader = SumGrader(
        answers={
            'lower': 'a',
            'upper': 'b',
            'summand': 'x^2',
            'summation_variable': 'x'
        },
        variables=['a', 'b']
    )
    student_input = ['a', 'b', 'x^2', '']
    msg = ("Please enter a value for summation_variable, it cannot be empty.")
    with raises(MissingInput, match=msg):
        grader(None, student_input)

def test_reordered_inputs():
    grader = SumGrader(
        answers={
            'lower': '1',
            'upper': '2',
            'summand': 'x',
            'summation_variable': 'x'
        },
        input_positions={
            'summand': 1,
            'lower': 3,
            'upper': 2,
        }
    )
    student_input = ['x', '2', '1']
    expected_result = {'ok': True, 'grade_decimal': 1, 'msg': ''}
    assert grader(None, student_input) == expected_result

def test_with_single_input():
    grader = SumGrader(
        answers={
            'lower': '-1',
            'upper': '1',
            'summand': 'x^2',
            'summation_variable': 'x'
        },
        input_positions = {
            'summand': 1
        }
    )
    # The same answer as instructor
    student_input0 = 'x^2'
    # same, but with an extra odd function that sums to zero
    student_input1 = 'x^2 + x'
    assert grader(None, student_input0)['ok']
    assert grader(None, student_input1)['ok']

def test_blacklist_grading():
    grader = SumGrader(
        answers={
            'lower': '1',
            'upper': '10',
            'summand': 'x^2',
            'summation_variable': 'x'
        },
        blacklist=['sin', 'cos']
    )

    # Correct answer with forbidden functions raises error
    student_input0 = ['1', '10', 'x^2 * cos(0) + sin(0)', 'x']
    with raises(InvalidInput, match=r"Invalid Input: function\(s\) 'cos', 'sin' "
                                     "not permitted in answer"):
        grader(None, student_input0)

    # Incorrect answer with forbidden functions marked wrong
    student_input1 = ['1', '10', 'x^2 * cos(0) + sin(pi/2)', 'x']
    assert not grader(None, student_input1)['ok']

def test_whitelist_grading():
    grader = SumGrader(
        answers={
            'lower': '1',
            'upper': '10',
            'summand': 'x^2',
            'summation_variable': 'x'
        },
        whitelist=['sin', 'cos']
    )

    # Correct answer with forbidden functions raises error
    student_input0 = ['1', '10', 'x^2 * cos(0) + tan(0)*sec(0)', 'x']
    with raises(InvalidInput, match=r"Invalid Input: function\(s\) 'sec', 'tan' "
                                     "not permitted in answer"):
        grader(None, student_input0)

    # Incorrect answer with forbidden functions marked wrong
    student_input1 = ['1', '10', 'x^2 * cos(0) + tan(pi/4)', 'x']
    assert not grader(None, student_input1)['ok']


# Debug Test
def test_debug_message():
    grader = SumGrader(
        answers={
            'lower': '1',
            'upper': '8',
            'summand': 'sin(s)',
            'summation_variable': 's'
        },
        debug=True,
        samples=2
    )
    student_input = ['1', '8', 'sin(x)', 'x']
    expected_message = (
        "<pre>MITx Grading Library Version {version}<br/>\n"
        "Student Responses:<br/>\n"
        "1<br/>\n"
        "8<br/>\n"
        "sin(x)<br/>\n"
        "x<br/>\n"
        "<br/>\n"
        "==============================================================<br/>\n"
        "SumGrader Debug Info<br/>\n"
        "==============================================================<br/>\n"
        "Functions available during evaluation and allowed in answer:<br/>\n"
        "{{{u}'abs': <function absolute at 0x...>,<br/>\n"
        " {u}'arccos': <function arccos at 0x...>,<br/>\n"
        " {u}'arccosh': <function arccosh at 0x...>,<br/>\n"
        " {u}'arccot': <function arccot at 0x...>,<br/>\n"
        " {u}'arccoth': <function arccoth at 0x...>,<br/>\n"
        " {u}'arccsc': <function arccsc at 0x...>,<br/>\n"
        " {u}'arccsch': <function arccsch at 0x...>,<br/>\n"
        " {u}'arcsec': <function arcsec at 0x...>,<br/>\n"
        " {u}'arcsech': <function arcsech at 0x...>,<br/>\n"
        " {u}'arcsin': <function arcsin at 0x...>,<br/>\n"
        " {u}'arcsinh': <function arcsinh at 0x...>,<br/>\n"
        " {u}'arctan': <function arctan at 0x...>,<br/>\n"
        " {u}'arctan2': <function arctan2 at 0x...>,<br/>\n"
        " {u}'arctanh': <function arctanh at 0x...>,<br/>\n"
        " {u}'ceil': <function ceil at 0x...>,<br/>\n"
        " {u}'conj': <ufunc 'conjugate'>,<br/>\n"
        " {u}'cos': <function cos at 0x...>,<br/>\n"
        " {u}'cosh': <function cosh at 0x...>,<br/>\n"
        " {u}'cot': <function cot at 0x...>,<br/>\n"
        " {u}'coth': <function coth at 0x...>,<br/>\n"
        " {u}'csc': <function csc at 0x...>,<br/>\n"
        " {u}'csch': <function csch at 0x...>,<br/>\n"
        " {u}'exp': <function exp at 0x...>,<br/>\n"
        " {u}'fact': <function factorial at 0x...>,<br/>\n"
        " {u}'factorial': <function factorial at 0x...>,<br/>\n"
        " {u}'floor': <function floor at 0x...>,<br/>\n"
        " {u}'im': <function imag at 0x...>,<br/>\n"
        " {u}'kronecker': <function kronecker at 0x...>,<br/>\n"
        " {u}'ln': <function log at 0x...>,<br/>\n"
        " {u}'log10': <function log10 at 0x...>,<br/>\n"
        " {u}'log2': <function log2 at 0x...>,<br/>\n"
        " {u}'max': <function max at 0x...>,<br/>\n"
        " {u}'min': <function min at 0x...>,<br/>\n"
        " {u}'re': <function real at 0x...>,<br/>\n"
        " {u}'sec': <function sec at 0x...>,<br/>\n"
        " {u}'sech': <function sech at 0x...>,<br/>\n"
        " {u}'sin': <function sin at 0x...>,<br/>\n"
        " {u}'sinh': <function sinh at 0x...>,<br/>\n"
        " {u}'sqrt': <function sqrt at 0x...>,<br/>\n"
        " {u}'tan': <function tan at 0x...>,<br/>\n"
        " {u}'tanh': <function tanh at 0x...>}}<br/>\n"
        "Functions available during evaluation and disallowed in answer:<br/>\n"
        "{{}}<br/>\n"
        "<br/>\n"
        "<br/>\n"
        "==============================================<br/>\n"
        "Summation Data for Sample Number 1 of 2<br/>\n"
        "==============================================<br/>\n"
        "Variables: {{{u}'e': 2.718282,<br/>\n"
        " {u}'i': 1j,<br/>\n"
        " {u}'infty': inf,<br/>\n"
        " {u}'j': 1j,<br/>\n"
        " {u}'pi': 3.141593}}<br/>\n"
        "<br/>\n"
        "Student Value: 1.543091<br/>\n"
        "Instructor Value: 1.543091<br/>\n"
        "<br/>\n"
        "<br/>\n"
        "==============================================<br/>\n"
        "Summation Data for Sample Number 2 of 2<br/>\n"
        "==============================================<br/>\n"
        "Variables: {{{u}'e': 2.718282,<br/>\n"
        " {u}'i': 1j,<br/>\n"
        " {u}'infty': inf,<br/>\n"
        " {u}'j': 1j,<br/>\n"
        " {u}'pi': 3.141593}}<br/>\n"
        "<br/>\n"
        "Student Value: 1.543091<br/>\n"
        "Instructor Value: 1.543091<br/>\n"
        "<br/>\n"
        "<br/>\n"
        "==========================================<br/>\n"
        "Comparison Data for All 2 Samples<br/>\n"
        "==========================================<br/>\n"
        "Comparer Function: EqualityComparer({{{u}'transform': <function identity_transform at 0x...>}})<br/>\n"
        "Comparison Results:<br/>\n"
        "[{{{u}'grade_decimal': 1.0, {u}'msg': {u}'', {u}'ok': True}},<br/>\n"
        " {{{u}'grade_decimal': 1.0, {u}'msg': {u}'', {u}'ok': True}}]<br/>\n"
        "</pre>"
    ).format(version=__version__, u=UNICODE_PREFIX)
    expected_message = round_decimals_in_string(expected_message)
    result = grader(None, student_input)
    assert result['ok'] is True
    assert result['grade_decimal'] == 1.0
    assert expected_message == round_decimals_in_string(result['msg'])

def test_error_catching():
    grader = SumGrader(
        answers={
            'lower': '1',
            'upper': '10',
            'summand': 'x^2',
            'summation_variable': 'x'
        },
        input_positions={
            'summand': 1,
            'lower': 2,
            'upper': 3
        }
    )
    student_input = ['1+', '1', '2']
    expected_message = r"Invalid Input: Could not parse '1\+' as a formula"
    with raises(CalcError, match=expected_message):
        grader(None, student_input)

    student_input = ['1/0', '1', '2']
    expected_message = ("Division by zero occurred. Check your input's denominators.")
    with raises(CalcError, match=expected_message):
        grader(None, student_input)


# Test options
def test_numbered_vars():
    grader = SumGrader(
        answers={
            'lower': '0',
            'upper': '1',
            'summand': 'a_{2}*x',
            'summation_variable': 'x'
        },
        numbered_vars=['a'],
    )
    # Correct answers
    correct_input = ['0', '1', 't*a_{2}', 't']
    # Incorrect answers
    wrong_input = ['0', '1', 't*a_{3}', 't']

    correct_result = grader(None, correct_input)
    wrong_result = grader(None, wrong_input)

    assert correct_result == {'ok': True, 'grade_decimal': 1, 'msg': ''}
    assert wrong_result == {'ok': False, 'grade_decimal': 0, 'msg': ''}

def test_suffixes():
    grader = SumGrader(
        answers={
            'lower': '1',
            'upper': '1k',
            'summand': '1%',
            'summation_variable': 'x'
        },
        metric_suffixes=True
    )
    assert grader(None, ['1', '10', '1', 't']) == {'ok': True, 'grade_decimal': 1, 'msg': ''}

def test_instructor_vars():
    """Ensures that instructor variables are not available to students"""
    grader = SumGrader(
        answers={
            'lower': '0',
            'upper': '1',
            'summand': 'c*t',
            'summation_variable': 't'
        },
        input_positions={
            'summand': 1
        },
        variables=['x', 'c'],
        sample_from={
            'x': [-3.14159, 3.14159],
            'c': DependentSampler(depends=["x"], formula="cos(x)")
        },
        instructor_vars=['c', 'pi', 'nothere']  # nothere will be ignored
    )

    assert grader(None, 'cos(x)*t')['ok']
    with raises(CalcError, match="'c' not permitted in answer as a variable"):
        grader(None, 'c*t')
    with raises(CalcError, match="'pi' not permitted in answer as a variable"):
        grader(None, 'pi*t')

def test_forbidden():
    """Ensures that answers don't contain forbidden strings"""
    grader = SumGrader(
        answers={
            'lower': '0',
            'upper': '1',
            'summand': '2*t',
            'summation_variable': 't'
        },
        forbidden_strings=['+'],
        forbidden_message='No addition!'
    )
    assert grader(None, ['0', '1', '2*t', 't'])['ok']
    with raises(InvalidInput, match="No addition!"):
        grader(None, ['0', '1', 't+t', 't'])
    with raises(InvalidInput, match="No addition!"):
        grader(None, ['0', '0+1', '2*t', 't'])

def test_required_funcs():
    """Ensures that required functions must be used"""
    grader = SumGrader(
        answers={
            'lower': '0',
            'upper': '1',
            'summand': 'tan(x)',
            'summation_variable': 'x'
        },
        input_positions={
            'summand': 1
        },
        required_functions=['tan']
    )

    assert grader(None, 'tan(x)')['ok']
    with raises(InvalidInput, match="Answer must contain the function tan"):
        grader(None, 'sin(x)/cos(x)')

def test_infinities():
    grader = SumGrader(
        answers={
            'lower': '0',
            'upper': 'infty',
            'summand': 'x^n/fact(n)',
            'summation_variable': 'n'
        },
        variables=['x']
    )
    assert grader(None, ['0', 'infty', 'x^n/fact(n)', 'n'])['ok']
    assert grader(None, ['infty', '0', 'x^n/fact(n)', 'n'])['ok']
    assert grader(None, ['0', '-infty', 'x^(-n)/fact(-n)', 'n'])['ok']
    assert grader(None, ['-infty', '0', 'x^(-n)/fact(-n)', 'n'])['ok']

    grader = SumGrader(
        answers={
            'lower': '1',
            'upper': 'infty',
            'summand': '1/n^4',
            'summation_variable': 'n'
        },
        input_positions = {
            'summand': 1
        }
    )
    assert grader(None, '1/n^4')['ok']


# Test summation capabilities
def test_summation():
    grader = SumGrader(
        answers={
            'lower': '0',
            'upper': '1',
            'summand': 'x',
            'summation_variable': 'x'
        },
        input_positions={
            'summand': 1
        }
    )
    # Here we bypass the class entirely to just test the summation capabilities.

    def summand(x):
        return x
    assert 6 == grader.perform_summation(summand, lower=1, upper=3, even_odd=0)
    assert 9 == grader.perform_summation(summand, lower=1, upper=5, even_odd=1)
    assert 6 == grader.perform_summation(summand, lower=1, upper=5, even_odd=2)
    assert 1e3*(1e3+1)/2 == grader.perform_summation(summand, lower=1, upper=float('inf'), even_odd=0)

    def summand(x):
        return x**2
    assert 14 == grader.perform_summation(summand, lower=1, upper=3, even_odd=0)

def test_convergence():
    # Test that we get convergence to well-known functions
    # Here we bypass the class entirely to just test the summation capabilities.
    grader = SumGrader(
        answers={
            'lower': '0',
            'upper': '1',
            'summand': 'x',
            'summation_variable': 'x'
        },
        input_positions={
            'summand': 1
        }
    )

    x = 0.1

    def exp_summand(n):
        value, _ = evaluator('x^n/fact(n)', {'n': n, 'x': x})
        return value

    result = grader.perform_summation(exp_summand, lower=0, upper=float('inf'), even_odd=0, infty_val=100)
    expect = np.exp(x)
    assert abs(result - expect) < 1e-14

    def sin_summand(n):
        value, _ = evaluator('(-1)^((n-1)/2)*x^n/fact(n)', {'n': n, 'x': x})
        return value

    result = grader.perform_summation(sin_summand, lower=0, upper=float('inf'), even_odd=1, infty_val=100)
    expect = np.sin(x)
    assert abs(result - expect) < 1e-14

    def cos_summand(n):
        value, _ = evaluator('(-1)^(n/2)*x^n/fact(n)', {'n': n, 'x': x})
        return value

    result = grader.perform_summation(cos_summand, lower=0, upper=float('inf'), even_odd=2, infty_val=100)
    expect = np.cos(x)
    assert abs(result - expect) < 1e-14

def test_vector_sums():
    grader = SumGrader(
        answers={
            'lower': '0',
            'upper': '10',
            'summand': '[1, t, t^2]',
            'summation_variable': 't'
        }
    )

    assert grader(None, ['0', '10', '[1, 0, 0] + t*[0, 1, t]', 't'])['ok']

def test_matrix_sums():
    grader = SumGrader(
        answers={
            'lower': '0',
            'upper': 'infty',
            'summand': '[[0, 1], [1, 0]]^n/fact(n)',
            'summation_variable': 'n'
        }
    )

    assert grader(None, ['0', 'infty', '[[0, 1], [1, 0]]^n/fact(n)', 'n'])['ok']

# Test errors
def test_bad_answer():
    grader = SumGrader(
        answers={
            'lower': '0',
            'upper': '1',
            'summand': '1/t',
            'summation_variable': 't'
        }
    )
    with raises(ConfigError, match="Summation Error with author's stored answer: Division by zero occurred."):
        grader(None, ['0', '1', 't', 't'])

def test_bad_var():
    grader = SumGrader(
        answers={
            'lower': '0',
            'upper': '1',
            'summand': 't',
            'summation_variable': 't'
        },
        variables=['x']
    )
    with raises(SummationError, match="Summation variable x conflicts with another previously-defined variable."):
        grader(None, ['0', '1', 'x', 'x'])

def test_complex_limits():
    grader = SumGrader(
        answers={
            'lower': '0',
            'upper': '1',
            'summand': 't',
            'summation_variable': 't'
        }
    )
    with raises(SummationError, match="Summation limits must be real but have evaluated to complex numbers."):
        grader(None, ['0', '1+i', 'x', 'x'])
    with raises(SummationError, match="Summation limits must be real but have evaluated to complex numbers."):
        grader(None, ['1+i', '0', 'x', 'x'])

def test_noninteger_limits():
    grader = SumGrader(
        answers={
            'lower': '0',
            'upper': '1',
            'summand': 't',
            'summation_variable': 't'
        }
    )
    with raises(SummationError, match="Upper summation limit does not evaluate to an integer."):
        grader(None, ['0', '1/2', 'x', 'x'])
    with raises(SummationError, match="Lower summation limit does not evaluate to an integer."):
        grader(None, ['1/3', '0', 'x', 'x'])

def test_bad_inf_sums():
    grader = SumGrader(
        answers={
            'lower': '0',
            'upper': '1',
            'summand': 't',
            'summation_variable': 't'
        }
    )
    with raises(SummationError, match="Cannot sum from infty to infty."):
        grader(None, ['infty', 'infty', 'x', 'x'])
    with raises(SummationError, match="Cannot sum from -infty to -infty."):
        grader(None, ['-infty', '-infty', 'x', 'x'])
