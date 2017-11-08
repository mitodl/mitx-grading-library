from mitxgraders.plugins.integralgrader import IntegralGrader, IntegrationError
from mitxgraders.baseclasses import InvalidInput, ConfigError
from pytest import raises
from mitxgraders.version import __version__

# Configuration Error Test
def test_wrong_number_of_inputs_raises_error():
    grader = IntegralGrader(
        answers={
            'lower':'a',
            'upper':'b',
            'integrand':'x^2',
            'integration_variable':'x'
        },
        input_positions={
            'integrand':1,
            'lower':2,
            'upper':3
        },
        variables=['a', 'b']
    )
    student_input = ['a', 'b']
    expected_message = ("Expected 3 student inputs but found 2. "
                        "Inputs should  appear in order ['integrand', 'lower', 'upper'].")
    with raises(ConfigError, msg=expected_message):
        grader(None, student_input)

def test_duplicate_input_positions():
    expected_message = "Key input_positions has repeated indices."
    with raises(ConfigError, msg=expected_message):
        IntegralGrader(
            answers={
                'lower':'a',
                'upper':'b',
                'integrand':'x^2',
                'integration_variable':'x'
            },
            input_positions={
                'integrand':1,
                'lower':2,
                'upper':3,
                'integration_variable':3
            },
            variables=['a', 'b']
        )

def test_skipped_input_positions():
    expected_message = ("Key input_positions values must be consecutive positive "
                        "integers starting at 1")
    with raises(ConfigError, msg=expected_message):
        IntegralGrader(
            answers={
                'lower':'a',
                'upper':'b',
                'integrand':'x^2',
                'integration_variable':'x'
            },
            input_positions={
                'integrand':1,
                'integration_variable':3,
            },
            variables=['a', 'b']
        )


# Input Error Tests
def test_user_provided_integration_conflict_raises_error():
    grader = IntegralGrader(
        answers={
            'lower':'a',
            'upper':'b',
            'integrand':'x^2',
            'integration_variable':'x'
        },
        variables=['a', 'b']
    )
    student_input = ['a', 'b', 'pi^2', 'pi']
    msg = ("Cannot use pi as integration variable; it is already has "
           "another meaning in this problem.")
    with raises(InvalidInput, match=msg):
        grader(None, student_input)

def test_user_provided_integration_variable_has_invalid_name():
    grader = IntegralGrader(
        answers={
            'lower':'a',
            'upper':'b',
            'integrand':'x^2',
            'integration_variable':'x'
        },
        variables=['a', 'b']
    )
    student_input = ['a', 'b', '_x^2', '_x']
    msg = ("Integration variable _x is an invalid variable name."
           "Variable name should begin with a letter and contain alphanumeric"
           "characters or underscores thereafter, but may end in single quotes.")
    with raises(InvalidInput, match=msg):
        grader(None, student_input)

def test_empty_input_raises_error():
    grader = IntegralGrader(
        answers={
            'lower':'a',
            'upper':'b',
            'integrand':'x^2',
            'integration_variable':'x'
        },
        variables=['a', 'b']
    )
    student_input = ['a', 'b', 'x^2', '']
    msg = ("Please enter a value for integration_variable, it cannot be empty.")
    with raises(InvalidInput, match=msg):
        grader(None, student_input)

# Integral Evaluation successful tests
def test_quadratic_integral_finite():
    grader = IntegralGrader(
        answers={
            'lower':'a',
            'upper':'b',
            'integrand':'x^2',
            'integration_variable':'x'
        },
        variables=['a', 'b'],
    )
    # The same answer as instructor
    student_input0 = ['a', 'b', 'x^2', 'x']
    # u = ln(x)
    student_input1 = ['ln(a)', 'ln(b)', 'e^(3*u)', 'u']
    expected_result = {'ok':True, 'grade_decimal':1, 'msg':''}
    assert grader(None, student_input0) == expected_result
    assert grader(None, student_input1) == expected_result

def test_convergent_improper_integral_on_infinite_domain():
    grader = IntegralGrader(
        answers={
            'lower':'1',
            'upper':'infty',
            'integrand':'1/x^5',
            'integration_variable':'x'
        },
        variables=['a', 'b'],
    )
    # The same answer as instructor
    student_input0 = ['1', 'infty', '1/x^5', 'x']
    # tan(u) = x
    student_input1 = ['pi/4', 'pi/2', '1/tan(u)^5*sec(u)^2', 'u']
    # The numerical value, integrated over interval with width 1
    student_input2 = ['0', '1', '1/4', 't']
    expected_result = {'ok':True, 'grade_decimal':1, 'msg':''}
    assert grader(None, student_input0) == expected_result
    assert grader(None, student_input1) == expected_result
    assert grader(None, student_input2) == expected_result

def test_convergent_improper_integral_on_finite_domain_with_poles():
    grader = IntegralGrader(
        answers={
            'lower':'-1',
            'upper':'1',
            'integrand':'1/sqrt(1-x^2)',
            'integration_variable':'x'
        }
    )
    # The same answer as instructor
    student_input0 = ['-1', '1', '1/sqrt(1-t^2)', 't']
    # x = cos(u)
    student_input1 = ['-pi/2', 'pi/2', '1/cos(u)*cos(u)', 'u']
    expected_result = {'ok':True, 'grade_decimal':1, 'msg':''}
    assert grader(None, student_input0) == expected_result
    assert grader(None, student_input1) == expected_result


def test_author_provided_integration_variable():
    grader = IntegralGrader(
        answers={
            'lower':'a',
            'upper':'b',
            'integrand':'x^2',
            'integration_variable':'x'
        },
        input_positions={
            'lower': 1,
            'upper': 2,
            'integrand': 3
        },
        variables=['a', 'b']
    )
    student_input = ['a', 'b', 'x^2']
    expected_result = {'ok':True, 'grade_decimal':1, 'msg':''}
    assert grader(None, student_input) == expected_result

def test_reordered_inputs():
    grader = IntegralGrader(
        answers={
            'lower':'a',
            'upper':'b',
            'integrand':'x^2',
            'integration_variable':'x'
        },
        input_positions={
            'integrand':1,
            'lower':3,
            'upper':2,
        },
        variables=['a', 'b']
    )
    student_input = ['x^2', 'b', 'a']
    expected_result = {'ok':True, 'grade_decimal':1, 'msg':''}
    assert grader(None, student_input) == expected_result

def test_integration_options_are_passed_correctly():
    grader0 = IntegralGrader(
        answers={
            'lower':'-1',
            'upper':'2',
            'integrand':'1/x',
            'integration_variable':'x'
        }
    )
    # grader1 will pass options to scipy.integrate.quad so as to
    # avoid the singularity at x=0
    grader1 = IntegralGrader(
        answers={
            'lower':'-1',
            'upper':'2',
            'integrand':'1/x',
            'integration_variable':'x'
        },
        integrator_options={
            'points': [0]
        }
    )
    student_input = ['-1', '2', '1/x', 'x']
    expected_result = {'ok':True, 'grade_decimal':1, 'msg':''}
    msg = ("There appears to be an error with the integral you entered: "
           "The integral is probably divergent, or slowly convergent.")
    # grader0 should raise an error because of singularity
    with raises(IntegrationError, match=msg):
        grader0(None, student_input)
    # grader1 avoids the singularity and should work
    assert grader1(None, student_input) == expected_result

# Integral Evaluation Error tests
def test_divergent_integral_infinite_domain_raises_error():
    msg = ("There appears to be an error with the integral you entered: "
           "The integral is probably divergent, or slowly convergent.")
    with raises(IntegrationError, match=msg):
        grader = IntegralGrader(
            answers={
                'lower':'1',
                'upper':'infty',
                'integrand':'1/x^2',
                'integration_variable':'x'
            }
        )
        student_input = ['0', '1', '1/x^2', 'x']
        grader(None, student_input)

# Debug Test
def test_debug_message():
    grader = IntegralGrader(
        answers= {
            'lower':'1',
            'upper':'8',
            'integrand':'sin(s)',
            'integration_variable':'s'
        },
        debug=True,
        samples=2
    )
    student_input = ['1', '8', 'sin(x)','x']
    expected_message = (
        "<pre>"
        "MITx Grading Library Version VERSION\n"
        "Student Responses:\n"
        "1\n"
        "8\n"
        "sin(x)\n"
        "x\n"
        "\n"
        "Integration Data for Sample Number 0\n"
        "Variables: {'infty': inf, 'e': 2.718281828459045, 'i': 1j, 'j': 1j, 's': 5.530375019455111, 'x': 5.530375019455111, 'pi': 3.141592653589793}\n"
        "==============================================\n"
        "Student Integration Data\n"
        "=============================================\n"
        "Numerical Value: 0.685802339677\n"
        "Error Estimate: 5.23517337969e-14\n"
        "Number of integrand evaluations: 21\n"
        "\n"
        "\n"
        "Author Integration Data\n"
        "=============================================\n"
        "Numerical Value: 0.685802339677\n"
        "Error Estimate: 5.23517337969e-14\n"
        "Number of integrand evaluations: 21\n"
        "\n"
        "\n"
        "Integration Data for Sample Number 1\n"
        "Variables: {'infty': inf, 'e': 2.718281828459045, 'i': 1j, 'j': 1j, 's': 5.530375019455111, 'x': 5.530375019455111, 'pi': 3.141592653589793}\n"
        "==============================================\n"
        "Student Integration Data\n"
        "=============================================\n"
        "Numerical Value: 0.685802339677\n"
        "Error Estimate: 5.23517337969e-14\n"
        "Number of integrand evaluations: 21\n"
        "\n"
        "\n"
        "Author Integration Data\n"
        "=============================================\n"
        "Numerical Value: 0.685802339677\n"
        "Error Estimate: 5.23517337969e-14\n"
        "Number of integrand evaluations: 21\n"
        "</pre>"
    ).replace("VERSION", __version__).replace("\n", "<br/>\n")
    expected_result = {'ok':True, 'grade_decimal':1, 'msg':expected_message}
    assert grader(None, student_input) == expected_result
