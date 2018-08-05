# Mathematical Functions

## FormulaGrader Default Functions

!!! note
    Below, expressions marked with a * may require our [AsciiMath renderer definitions](renderer.md) to display properly in edX.

By default, all of the following functions are made available to students in `FormulaGrader` problems.

- `sin(x)` Sine
- `cos(x)` Cosine
- `tan(x)` Tangent
- `sec(x)` Secant
- `csc(x)` Cosecant
- `cot(x)` Cotangent
- `sqrt(x)` Square Root
- `log10(x)` Log (base 10)*
- `log2(x)` Log (base 2)*
- `ln(x)` Natural logarithm
- `exp(x)` Exponential
- `arccos(x)` Inverse Cosine
- `arcsin(x)` Inverse Sine
- `arctan(x)` Inverse Tangent
- `arcsec(x)` Inverse Secant*
- `arccsc(x)` Inverse Cosecant*
- `arccot(x)` Inverse Cotangent*
- `abs(x)` Absolute value (real) or modulus (complex)
- `factorial(x)` and `fact(x)` Factorial*
    - domain: all complex numbers except negative integers. Large outputs may raise `OverflowError`s.
- `sinh(x)` Hyperbolic Sine
- `cosh(x)` Hyperbolic Cosine
- `tanh(x)` Hyperbolic Tangent
- `sech(x)` Hyperbolic Secant
- `csch(x)` Hyperbolic Cosecant
- `coth(x)` Hyperbolic Cotangent
- `arcsinh(x)` Inverse Hyperbolic Sine*
- `arccosh(x)` Inverse Hyperbolic Cosine*
- `arctanh(x)` Inverse Hyperbolic Tangent*
- `arcsech(x)` Inverse Hyperbolic Secant*
- `arccsch(x)` Inverse Hyperbolic Cosecant*
- `arccoth(x)` Inverse Hyperbolic Cotangent*
- `re(x)` Real part of a complex expression*
- `im(x)` Imaginary part of a complex expression*
- `conj(x)` Complex conjugate of a complex expression*

## MatrixGrader Default Functions

In `MatrixGrader` problems, all `FormulaGrader` functions are available by default, as are the following extra functions:

- `abs(x)`: absolute value; input can be number or vector
- `adj(x)`: conjugate transpose, same as `ctrans(x)`
- `cross(x, y)`: cross product, inputs must be 3-component vectors
- `ctrans(x)`: conjugate transpose, same as `adj(x)`
- `det(x)`: determinant, input must be square matrix
- `norm(x)`: Frobenius norm, works for scalars, vectors, and matrices
- `tr(x)`: transpose, input must be square matrix
- `trace(x)`: trace

## The `specify_domain` decorator

The `mitxgraders` library provides `specify_domain` as a way to provide students with useful error messages when adding extra functions to a `MatrixGrader` problem.

### An Example

Suppose we have a `MatrixGrader` problem in which we want to provide students with a function `rot(vector, axis, angle)` that rotates a vector about a given axis by a given angle. We can provide such a function with the `user_functions` configuration key.

```pycon
>>> import numpy as np
>>> from mitxgraders import *

>>> def rot(vec, axis, angle):
...     """
...     Rotate vec by angle around axis. Implemented by Euler-Rodrigues formula:
...     https://en.wikipedia.org/wiki/Euler-Rodrigues_formula
...
...     Arguments:
...         vec: a 3-component MathArray to rotate
...         axis: a 3-component MathArray to rotate around
...         angle: a number
...     """
...     vec = np.array(vec)
...     unit_axis = np.array(axis)/np.linalg.norm(axis)
...     a = np.cos(angle/2)
...     omega = unit_axis * np.sin(angle/2)
...     crossed = np.cross(omega, vec)
...     result = vec + 2*a*crossed + 2*np.cross(omega, crossed)
...     return MathArray(result)

>>> grader_1 = MatrixGrader(
...    answers='rot(v, [0, 0, 1], theta)',
...    variables=['v', 'theta'],
...    sample_from={
...        'v': RealVectors(shape=3),
...    },
...    user_functions={
...        'rot': rot
...    }
... )

```

#### The Problem

Our `rot(vec, axis, angle)` function works, but if students supply the function above with arguments of incorrect type, they receive unhelpful error messages:

```pycon
>>> try:
...     grader_1(None, 'rot(v, theta, [0, 0, 1])')
... except StudentFacingError as error:
...     print(error.message)
There was an error evaluating rot(...). Its input does not seem to be in its domain.

```

#### A solution

To provide students with more useful error messages, we can use `specify_domain`, a decorator function imported from `mitxgraders`. [Decorator Functions](https://dbader.org/blog/python-decorators) are "higher-order functions" that take functions as input and produce functions as output, usually modifying the input function's behavior. In our case, `specify_domain` will modify the behavior of `rot` so as to provide more helpful `StudentFacingError`s.

Here we go:

```pycon
>>> @specify_domain(input_shapes=[[3], [3], [1]], display_name='rot')
... def rot_with_error_messages(vec, axis, angle):
...     # rot(vec, axis, angle) defined above
...     return rot(vec, axis, angle)

>>> # Define new grader using rot_with_error_messages
>>> grader_2 = MatrixGrader(
...    answers='rot(v, [0, 0, 1], theta)',
...    variables=['v', 'theta'],
...    sample_from={
...        'v': RealVectors(shape=3),
...    },
...    user_functions={
...        'rot': rot_with_error_messages
...    }
... )

```

Now if a student calls `rot` with incorrect inputs, they receive a more helpful message:

```pycon
>>> try:
...     grader_2(None, 'rot(v, theta, [0, 0, 1])')
... except StudentFacingError as error:
...     print(error.message.replace('<br/>', '\n'))
There was an error evaluating function rot(...)
1st input is ok: received a vector of length 3 as expected
2nd input has an error: received a scalar, expected a vector of length 3
3rd input has an error: received a vector of length 3, expected a scalar

```

### Configuring specify_domain

The decorator `specify_domain` accepts optional keyword arguments and should be called in either of two equivalent ways:

```pycon
>>> @specify_domain(keyword_arguments)                # doctest: +SKIP
... def target_function(x, y, z):
...     pass # do whatever you want
>>> # or, equivalently:
>>> def target_function(x, y ,z):                     
...     pass # do whatever you want
>>> decorated_function = specify_domain(keyword_arguments)(target_function) # doctest: +SKIP
```

The keyword arguments are:

- `input_shapes`: A list that indicates the shape of each input to the target function. This list **must** have the same length as the number of arguments in the target function. Each list element should be one of the following:
    - `1`: indicates input is scalar
    - `k` (positive integer > 1): indicates input is a k-component vector
    - `[k1, k2, ...]`, list of positive integers: means input is an array of shape (k1, k2, ...)
    - `(k1, k2, ...)`, tuple of positive integers: equivalent to `[k1, k2, ...]`
    - `'square'` (string): indicates a square matrix of any dimension
- `display_name` (str): Function name to be used in error messages
    defaults to `None`, meaning that the function's `__name__` attribute is used.

So, for example,

```pycon
>>> @specify_domain(input_shapes=[1, [3, 2], 4], display_name='myfunc')
... def some_function(x, A, v):
...     pass

```
specifies that the function `some_func` must be called with three arguments:

- 1st argument: scalar,
- 2nd argument: 3 by 2 matrix, and a
- 3rd argument: 4-component vector.
