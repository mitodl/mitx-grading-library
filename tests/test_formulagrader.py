"""
Tests for FormulaGrader and NumericalGrader
"""
from __future__ import division
import random
from graders import (
    NumericalGrader,
    FormulaGrader,
    RealInterval,
    IntegerRange,
    DiscreteSet,
    ComplexRectangle,
    ComplexSector,
    SpecificFunctions,
    RandomFunction,
    UndefinedVariable,
    UndefinedFunction,
    UnmatchedParentheses,
    ConfigError,
    InvalidInput
)
from graders.voluptuous import Error, MultipleInvalid
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
        random_functions=['re', 'im'],
        sample_from={
            'z': ComplexRectangle()
        }
    )
    learner_input = 're(z)^2 - im(z)^2 + 2*i*re(z)*im(z)'
    assert not grader(None, learner_input)['ok']

    grader = NumericalGrader(
        answers='tan(1)',
        user_functions={'sin': lambda x: x}
    )
    assert grader(None, 'tan(1)')['ok']
    assert not grader(None, 'sin(1)/cos(1)')['ok']

def test_real_interval():
    """Tests the RealInterval class"""
    start = random.random() * 20 - 10
    stop = random.random() * 20 - 10
    if start > stop:
        start, stop = stop, start

    # Right way around
    ri = RealInterval(start=start, stop=stop)
    for i in range(10):
        assert start <= ri.gen_sample() <= stop

    # Wrong way around
    ri = RealInterval(start=stop, stop=start)
    for i in range(10):
        assert start <= ri.gen_sample() <= stop

    # In a list
    ri = RealInterval([start, stop])
    for i in range(10):
        assert start <= ri.gen_sample() <= stop

    # No arguments
    ri = RealInterval()
    for i in range(10):
        assert 1 <= ri.gen_sample() <= 5

    # Rejects tuples
    with raises(Error, match="expected a dictionary. Got \(1, 3\)"):
        RealInterval((1, 3))

def test_int_range():
    """Tests the IntegerRange class"""
    start = random.randint(-20, 20)
    stop = random.randint(-20, 20)
    if start > stop:
        start, stop = stop, start
    mylist = list(range(start, stop + 1))

    # Right way around
    ii = IntegerRange(start=start, stop=stop)
    for i in range(10):
        assert ii.gen_sample() in mylist

    # Wrong way around
    ii = IntegerRange(start=stop, stop=start)
    for i in range(10):
        assert ii.gen_sample() in mylist

    # In a list
    ii = IntegerRange([start, stop])
    for i in range(10):
        assert ii.gen_sample() in mylist

    # No arguments
    ii = IntegerRange()
    for i in range(10):
        assert ii.gen_sample() in list(range(1, 6))

def test_complex_rect():
    """Tests the ComplexRectangle class"""
    restart = random.random() * 20 - 10
    restop = random.random() * 20 - 10
    if restart > restop:
        restart, restop = restop, restart

    imstart = random.random() * 20 - 10
    imstop = random.random() * 20 - 10
    if imstart > imstop:
        imstart, imstop = imstop, imstart

    cr = ComplexRectangle(re=[restart, restop], im=[imstart, imstop])

    for _ in range(20):
        sample = cr.gen_sample()
        assert restart <= np.real(sample) <= restop
        assert imstart <= np.imag(sample) <= imstop

def test_complex_sect():
    """Tests the ComplexSector class"""
    mstart = random.random() * 20
    mstop = random.random() * 20
    if mstart > mstop:
        mstart, mstop = mstop, mstart

    argstart = random.uniform(-np.pi, np.pi)
    argstop = random.uniform(-np.pi, np.pi)
    if argstart > argstop:
        argstart, argstop = argstop, argstart

    cs = ComplexSector(modulus=[mstart, mstop], argument=[argstart, argstop])

    for _ in range(20):
        sample = cs.gen_sample()
        assert mstart <= np.abs(sample) <= mstop
        assert argstart <= np.angle(sample) <= argstop

def test_random_func():
    """Tests the RandomFunction class"""
    center = 15
    amplitude = 2
    rf = RandomFunction(center=center, amplitude=amplitude)

    func = rf.gen_sample()

    for i in range(20):
        x = random.uniform(-10, 10)
        assert func(x) == func(x)
        assert center - amplitude <= func(x) <= center + amplitude

def test_discrete_set():
    """Tests the DiscreteSet class"""
    vals = tuple(np.random.rand(10))
    ds = DiscreteSet(vals)

    for _ in range(20):
        assert ds.gen_sample() in vals

    # Single value
    val = random.uniform(0, 10)
    ds = DiscreteSet(val)
    assert ds.gen_sample() == val

    # Rejects lists
    with raises(Error, match="expected Number @ data\[0\]. Got 1"):
        DiscreteSet([1, 2])

def test_specific_functions():
    """Tests the SpecificFunctions class"""
    funcs = [np.sin, np.cos, np.tan]
    sf = SpecificFunctions(funcs)

    for _ in range(20):
        assert sf.gen_sample() in funcs

    # Single functions
    ds = SpecificFunctions(np.abs)
    assert ds.gen_sample() == np.abs
    ds = SpecificFunctions(abs)
    assert ds.gen_sample() == abs

def test_ng_expressions():
    """General test of NumericalGrader"""
    grader = NumericalGrader(
        answers="1+tan(3/2)"
    )
    assert grader(None, "(cos(3/2) + sin(3/2))/cos(3/2 + 2*pi)")['ok']
    # Checking tolerance
    assert grader(None, "0.01+(cos(3/2) + sin(3/2))/cos(3/2 + 2*pi)")['ok']
    assert not grader(None, "0.02+(cos(3/2) + sin(3/2))/cos(3/2 + 2*pi)")['ok']

def test_ng_invalid_input():
    grader = NumericalGrader(answers='2')

    expect = 'Invalid Input: pi not permitted in answer as a function ' + \
             '\(did you forget to use \* for multiplication\?\)'
    with raises(UndefinedFunction, match=expect):
        grader(None, "pi(3)")

    expect = 'Invalid Input: spin not permitted in answer as a function'
    with raises(UndefinedFunction, match=expect):
        grader(None, "spin(3)")

    expect = 'Invalid Input: R not permitted in answer as a variable'
    with raises(UndefinedVariable, match=expect):
        grader(None, "R")

    expect = 'Invalid Input: Parentheses are unmatched. 1 parentheses were opened but never closed.'
    with raises(UnmatchedParentheses, match=expect):
        grader(None, "5*(3")

    expect = 'Invalid Input: A closing parenthesis was found after segment 5\*\(3\), but ' + \
             'there is no matching opening parenthesis before it.'
    with raises(UnmatchedParentheses, match=expect):
        grader(None, "5*(3))")

    expect = "Invalid Input: Could not parse '5pp' as a formula"
    with raises(InvalidInput, match=expect):
        grader(None, "5pp")

    expect = "Error evaluating factorial\(\) or fact\(\) in input. " + \
             "These functions can only be used on positive integers."
    with raises(InvalidInput, match=expect):
        grader(None, "fact(-1)")
    with raises(InvalidInput, match=expect):
        grader(None, "fact(1.5)")

def test_ng_tolerance():
    """Test of NumericalGrader tolerance"""
    grader = NumericalGrader(answers="10", tolerance=0.1)

    assert not grader(None, '9.85')['ok']
    assert grader(None, '9.9')['ok']
    assert grader(None, '10')['ok']
    assert grader(None, '10.1')['ok']
    assert not grader(None, '10.15')['ok']

    grader = NumericalGrader(answers="10", tolerance="1%")

    assert not grader(None, '9.85')['ok']
    assert grader(None, '9.9')['ok']
    assert grader(None, '10')['ok']
    assert grader(None, '10.1')['ok']
    assert not grader(None, '10.15')['ok']

def test_ng_userfunc():
    """Test a user function in NumericalGrader"""
    grader = NumericalGrader(
        answers="hello(2)",
        user_functions={"hello": lambda x: x**2-1}
    )
    assert grader(None, "5+hello(2)-2-3")['ok']
    assert not grader(None, "hello(1)")['ok']

def test_ng_percent():
    """Test a percentage suffix in NumericalGrader"""
    grader = NumericalGrader(
        answers="2%"
    )
    assert grader(None, "2%")['ok']
    assert grader(None, "0.02")['ok']
    with raises(InvalidInput, match="Invalid Input: Could not parse '20m' as a formula"):
        grader(None, "20m")

def test_ng_metric():
    """Test metric suffixes in NumericalGrader"""
    grader = NumericalGrader(
        answers="0.02",
        metric_suffixes=True
    )
    assert grader(None, "2%")['ok']
    assert grader(None, "0.02")['ok']
    assert grader(None, "20m")['ok']

def test_ng_userfunction():
    """Test NumericalGrader with user-defined functions"""
    grader = NumericalGrader(
        answers="sin(0.4)/cos(0.4)",
        user_functions={"hello": np.tan}
    )
    assert grader(None, "hello(0.4)")['ok']
    assert grader(None, "sin(0.4)/cos(0.4)")['ok']

    # Test with function names with primes at the end
    grader = NumericalGrader(
        answers="sin(0.4)/cos(0.4)",
        user_functions={"f'": np.tan}
    )
    assert grader(None, "f'(0.4)")['ok']

    grader = NumericalGrader(
        answers="sin(0.4)/cos(0.4)",
        user_functions={"function2name_2go''''''": np.tan}
    )
    assert grader(None, "function2name_2go''''''(0.4)")['ok']

    # Primes aren't allowed in the middle
    expect = "Invalid Input: Could not parse 'that'sbad\(1\)' as a formula"
    with raises(InvalidInput, match=expect):
        grader = NumericalGrader(
            answers="1",
            user_functions={"that'sbad": np.tan}
        )
        grader(None, "that'sbad(1)")

    expect = "1 is not a valid name for a function \(must be a string\)"
    with raises(ConfigError, match=expect):
        NumericalGrader(
            answers="1",
            user_functions={1: np.tan}
        )

def test_ng_userconstants():
    """Test NumericalGrader with user-defined constants"""
    grader = NumericalGrader(
        answers="5",
        user_constants={"hello": 5}
    )
    assert grader(None, "hello")['ok']

    expect = "1 is not a valid name for a constant \(must be a string\)"
    with raises(ConfigError, match=expect):
        NumericalGrader(
            answers="1",
            user_constants={1: 5}
        )

def test_ng_blackwhite():
    """Test NumericalGrader with blacklists and whitelists"""
    grader = NumericalGrader(
        answers="sin(0.4)/cos(0.4)",
        user_functions={"hello": np.tan},
        blacklist=['tan'],
        case_sensitive=False
    )
    assert grader(None, "hello(0.4)")['ok']
    assert grader(None, "sin(0.4)/cos(0.4)")['ok']
    expect = 'Invalid Input: tan not permitted in answer as a function'
    with raises(UndefinedFunction, match=expect):
        grader(None, "tan(0.4)")
    expect = 'Invalid Input: TAN not permitted in answer as a function'
    with raises(UndefinedFunction, match=expect):
        grader(None, "TAN(0.4)")

    grader = NumericalGrader(
        answers="sin(0.4)/cos(0.4)",
        user_functions={"hello": np.tan},
        whitelist=['cos', 'sin'],
        case_sensitive=False
    )
    assert grader(None, "hello(0.4)")['ok']
    assert grader(None, "sin(0.4)/cos(0.4)")['ok']
    expect = 'Invalid Input: tan not permitted in answer as a function'
    with raises(UndefinedFunction, match=expect):
        grader(None, "tan(0.4)")
    expect = 'Invalid Input: TAN not permitted in answer as a function'
    with raises(UndefinedFunction, match=expect):
        grader(None, "TAN(0.4)")

    grader = NumericalGrader(
        answers="1",
        whitelist=[None]
    )
    assert grader(None, "1")['ok']
    expect = "Invalid Input: cos not permitted in answer as a function"
    with raises(UndefinedFunction, match=expect):
        grader(None, "cos(0)")
    assert not grader.functions   # Check for an empty dictionary

    with raises(ConfigError, match="Cannot whitelist and blacklist at the same time"):
        NumericalGrader(
            answers="5",
            blacklist=['tan'],
            whitelist=['tan']
        )

    with raises(ConfigError, match="Unknown function in blacklist: test"):
        NumericalGrader(
            answers="5",
            blacklist=['test']
        )

    with raises(ConfigError, match="Unknown function in whitelist: test"):
        NumericalGrader(
            answers="5",
            whitelist=['test']
        )

def test_ng_case_sensitive():
    """Test NumericalGrader with case insensitive input"""
    grader = NumericalGrader(
        answers="sin(pi)",
        case_sensitive=False,
        tolerance=1e-15
    )
    assert grader(None, "sin(pi)")['ok']
    assert grader(None, "0")['ok']
    assert grader(None, "Sin(Pi)")['ok']
    assert grader(None, "SIN(PI)")['ok']

def test_ng_forbidden():
    """Test NumericalGrader with forbidden strings in input"""
    grader = NumericalGrader(
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

def test_ng_required():
    """Test NumericalGrader with required functions in input"""
    grader = NumericalGrader(
        answers="sin(3)/cos(3)",
        required_functions=['sin', 'cos'],
        case_sensitive=False
    )
    assert grader(None, 'SIN(3)/COS(3)')['ok']
    with raises(InvalidInput, match="Invalid Input: Answer must contain the function sin"):
        grader(None, "tan(3)")

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
        random_functions=['hello']
    )
    assert grader(None, 'hello(x)')['ok']
    assert isinstance(grader.config["functions_from"]['hello'], RandomFunction)

    with raises(MultipleInvalid, match="extra keys not allowed @ data\['w'\]"):
        grader = FormulaGrader(random_functions=['x'], functions_from={'w': 2})

    grader = FormulaGrader(
        answers="hello(x)",
        variables=['x'],
        random_functions=['hello'],
        functions_from={'hello': lambda x: x*x}
    )
    assert isinstance(grader.config["functions_from"]['hello'], SpecificFunctions)
    assert grader(None, 'hello(x)')['ok']

    grader = FormulaGrader(
        answers="hello(x)",
        variables=['x'],
        random_functions=['hello'],
        functions_from={'hello': RandomFunction()}
    )
    assert grader(None, 'hello(x)')['ok']

    grader = FormulaGrader(
        answers="hello(x)",
        variables=['x'],
        random_functions=['hello'],
        functions_from={'hello': [np.sin, np.cos, np.tan]}
    )
    assert isinstance(grader.config["functions_from"]['hello'], SpecificFunctions)
    assert grader(None, 'hello(x)')['ok']

    grader = FormulaGrader(
        answers="hello(x)",
        variables=['x'],
        random_functions=['hello'],
        functions_from={'hello': SpecificFunctions([np.sin, np.cos, np.tan])}
    )
    assert isinstance(grader.config["functions_from"]['hello'], SpecificFunctions)
    assert grader(None, 'hello(x)')['ok']
