from pytest import fixture, raises
import numpy as np
from voluptuous import Invalid, Error
from mitxgraders.helpers.specify_domain import SpecifyDomain, DomainError
from mitxgraders.helpers.math_array import equal_as_arrays, random_math_array

def get_somefunc(display_name=None):

    if display_name:
        # Takes: scalar, [2, 3] matrix, 3-component vector, 2-component vector
        @SpecifyDomain(input_shapes=[1, [2, 3], 3, 2], display_name=display_name)
        def somefunc(w, x, y, z):
            return w*x*y + z
    else:
        # Takes: scalar, [2, 3] matrix, 3-component vector, 2-component vector
        @SpecifyDomain(input_shapes=[1, [2, 3], 3, 2])
        def somefunc(w, x, y, z):
            return w*x*y + z

    return somefunc

def get_somefunc_from_static_method(display_name=None):
    """
    Uses SpecifyDomain.make_decorator to decorate the function
    """
    shapes = [
        (1,), # scalar
        (2, 3), # 2 by 3 matrix
        (3,), # vector of length 3
        (2,) # vector of length 2
    ]
    if display_name:
        # Takes: scalar, [2, 3] matrix, 3-component vector, 2-component vector

        @SpecifyDomain.make_decorator(*shapes, display_name=display_name)
        def somefunc(w, x, y, z):
            return w*x*y + z
    else:
        # Takes: scalar, [2, 3] matrix, 3-component vector, 2-component vector
        @SpecifyDomain.make_decorator(*shapes)
        def somefunc(w, x, y, z):
            return w*x*y + z

    return somefunc

def test_correct_arguments_get_passed_to_function():
    f = get_somefunc()

    w = np.random.uniform(-10, 10)
    x = random_math_array([2, 3])
    y = random_math_array([3])
    z = random_math_array([2])

    assert equal_as_arrays(f(w, x, y, z), w*x*y + z)

def test_incorrect_arguments_raise_errors():
    f = get_somefunc()
    F = get_somefunc_from_static_method()

    w = np.random.uniform(-10, 10)
    x = random_math_array([2, 2])
    y = np.random.uniform(-10, 10)
    z = random_math_array([2])

    match = ("There was an error evaluating function {0}\(...\)"
             "\n\t1st input is ok: received a scalar as expected"
             "\n\t2nd input has an error: received a matrix of shape \(rows: 2, cols: 2\), "
             "expected a matrix of shape \(rows: 2, cols: 3\)"
             "\n\t3rd input has an error: received a scalar, expected a vector of length 3"
             "\n\t4th input is ok: received a vector of length 2 as expected")
    with raises(DomainError, match=match.format('somefunc')):
        f(w, x, y, z)
    with raises(DomainError, match=match.format('somefunc')):
        F(w, x, y, z)

    # Test dispaly name
    g = get_somefunc('puppy')
    G = get_somefunc_from_static_method('puppy')
    with raises(DomainError, match=match.format('puppy')):
        g(w, x, y, z)
    with raises(DomainError, match=match.format('puppy')):
        G(w, x, y, z)

def test_incorrect_number_of_inputs_raises_useful_error():
    f = get_somefunc()
    match = 'There was an error evaluating function somefunc\(...\): expected 4 inputs, but received 2.'
    with raises(DomainError, match=match):
        f(1, 2)

def test_author_facing_decorator_raises_errors_with_invalid_config():

    match = "required key not provided @ data\['input_shapes'\]. Got None"
    with raises(Error, match=match):
        @SpecifyDomain()
        def f():
            pass

    match = ("Expected shape specification to be a positive integer or list of "
             "positive integers @ data\['input_shapes'\]\[1\]. Got 0")
    with raises(Error, match=match):
        @SpecifyDomain(input_shapes=[5,0,[1, 2]])
        def g():
            pass
