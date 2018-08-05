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

### Example usage

Suppose you have a `MatrixGrader` problem where you want to provide students with a function `rot(vector, axis, angle)` that rotates a vector about a given axis by a given angle. You can provide such a function with the `user_functions` configuration key.

```pycon
>>> import numpy as np
>>> from mitxgraders import MatrixGrader, RealMatrices

>>> def rot(vec, axis, angle):
...     """
...     Rotate vec by angle around axis. Implemented by Euler-Rodrigues formula:
...     https://en.wikipedia.org/wiki/Euler-Rodrigues_formula
...     """
...     unit_axis = axis/np.linalg.norm(axis)
...     a = np.cos(angle/2)
...     omega = unit_axis * np.sin(angle/2)
...     crossed = np.cross(omega, vec)
...
...     return vec + 2*a*crossed + 2*np.cross(omega, crossed)
>>> grader = MatrixGrader(
...    answers='rot(a, [0, 0, 1], theta)',
...    variables=['a', 'theta'],
...    sample_from={
...        'a': RealVectors(shape=3),
...    },
...    user_functions={
...        'rot': rot
...    }
)
>>> grader(None, 'rot(a, [0, 0, 1], 2*pi + theta)')
```
