"""
Tests for the various sampling classes
"""
from __future__ import division
import random
from mitxgraders import (
    RealInterval,
    IntegerRange,
    DiscreteSet,
    ComplexRectangle,
    ComplexSector,
    SpecificFunctions,
    RandomFunction,
    DependentSampler,
    ConfigError
)
from mitxgraders.sampling import gen_symbols_samples
from mitxgraders.voluptuous import Error
from pytest import raises, approx
import numpy as np

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
    if start == stop:
        stop += 1
    mylist = list(range(start, stop + 1))

    # Right way around
    ii = IntegerRange(start=start, stop=stop)
    for i in range(10):
        assert ii.gen_sample() in mylist

    # Wrong way around
    ii = IntegerRange(start=stop, stop=start)
    for i in range(10):
        assert ii.gen_sample() in mylist

    # With only one selection
    ii = IntegerRange(start=4, stop=4)
    assert ii.gen_sample() == 4

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

    with raises(Exception, match="Expected 2 arguments, but received 1"):
        RandomFunction(input_dim=2).gen_sample()(1)

    with raises(Exception, match="Expected 1 arguments, but received 2"):
        RandomFunction(input_dim=1).gen_sample()(1, 2)

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

def test_docs():
    """Make sure that the documentation examples work"""
    # Generate random real numbers between 3 and 7
    sampler = RealInterval(start=3, stop=7)
    # This is equivalent to
    sampler = RealInterval([3, 7])
    # The default is [1, 5]
    sampler = RealInterval()

    # Generate random integers between 3 and 7 inclusive
    sampler = IntegerRange(start=3, stop=7)
    # This is equivalent to
    sampler = IntegerRange([3, 7])
    # The default is [1, 5]
    sampler = IntegerRange()

    # Select random numbers from (1, 3, 5, 7, 9)
    sampler = DiscreteSet((1, 3, 5, 7, 9))
    # Always select 3.5
    sampler = DiscreteSet(3.5)

    # Select random complex numbers from 0 to 1 + i
    sampler = ComplexRectangle(re=[0, 1], im=[0, 1])
    # The default is re=[1, 3], im=[1, 3]
    sampler = ComplexRectangle()

    # Select random complex numbers from inside the unit circle
    sampler = ComplexSector(modulus=[0, 1], argument=[-np.pi, np.pi])
    # The default is modulus=[1, 3], argument=[0, pi/2]
    sampler = ComplexSector()

    # Test dependent sampling
    sampler = DependentSampler(depends=["x", "y", "z"], formula="sqrt(x^2+y^2+z^2)")

    # Select either sin or cos randomly
    functionsampler = SpecificFunctions([np.cos, np.sin])
    # Always select a single lambda function
    functionsampler = SpecificFunctions(lambda x: x*x)

    # Generate a random function
    functionsampler = RandomFunction(center=1, amplitude=2)
    # The default is center=0, amplitude=10
    functionsampler = RandomFunction()

    # Generate a random sinusoid
    functionsampler = RandomFunction(num_terms=1)

    # Generate a function that takes in two values and outputs a 3D vector
    functionsampler = RandomFunction(input_dim=2, output_dim=3)

def test_dependent_sampler():
    """Tests the DependentSampler class"""
    # Test basic usage and multiple samples
    result = gen_symbols_samples(
        ["a", "b"],
        2,
        {
            'a': IntegerRange([1, 1]),
            'b': DependentSampler(depends=["a"], formula="a+1")
        }
    )
    assert result == [{"a": 1, "b": 2.0}, {"a": 1, "b": 2.0}]

    result = gen_symbols_samples(
        ["a", "b", "c", "d"],
        1,
        {
            'a': RealInterval([1, 1]),
            'd': DependentSampler(depends=["c"], formula="c+1"),
            'c': DependentSampler(depends=["b"], formula="b+1"),
            'b': DependentSampler(depends=["a"], formula="a+1")
        }
    )[0]
    assert result["b"] == 2 and result["c"] == 3 and result["d"] == 4

    result = gen_symbols_samples(
        ["x", "y", "z", "r"],
        1,
        {
            'x': RealInterval([-5, 5]),
            'y': RealInterval([-5, 5]),
            'z': RealInterval([-5, 5]),
            'r': DependentSampler(depends=["x", "y", "z"], formula="sqrt(x^2+y^2+z^2)")
        }
    )[0]
    assert result["x"]**2 + result["y"]**2 + result["z"]**2 == approx(result["r"]**2)

    with raises(ConfigError, match="Circularly dependent DependentSamplers detected: x, y"):
        gen_symbols_samples(
            ["x", "y"],
            1,
            {
                'x': DependentSampler(depends=["y"], formula="1"),
                'y': DependentSampler(depends=["x"], formula="1")
            }
        )

    with raises(ConfigError, match=r"Formula error in dependent sampling formula: 1\+\(2"):
        gen_symbols_samples(
            ["x"],
            1,
            {
                'x': DependentSampler(depends=[], formula="1+(2")
            }
        )

    with raises(Exception, match="DependentSampler must be invoked with compute_sample."):
        DependentSampler(depends=[], formula="1").gen_sample()
