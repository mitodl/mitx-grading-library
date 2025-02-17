"""
mathfuncs.py

Contains mathematical functions for use in interpreting formulas.

Contains some helper functions used in grading formulae:
* within_tolerance

Defines:
* DEFAULT_FUNCTIONS
* DEFAULT_VARIABLES
* DEFAULT_SUFFIXES
* METRIC_SUFFIXES
"""


from numbers import Number
import numpy as np
from mitxgraders.helpers.calc.specify_domain import SpecifyDomain
from mitxgraders.helpers.calc.exceptions import FunctionEvalError
from mitxgraders.helpers.calc.math_array import MathArray

# Normal Trig
def sec(arg):
    """Secant"""
    return 1 / np.cos(arg)

def csc(arg):
    """Cosecant"""
    return 1 / np.sin(arg)

def cot(arg):
    """Cotangent"""
    return 1 / np.tan(arg)

# Inverse Trig
# http://en.wikipedia.org/wiki/Inverse_trigonometric_functions#Relationships_among_the_inverse_trigonometric_functions
def arcsec(val):
    """Inverse secant"""
    return np.arccos(1. / val)

def arccsc(val):
    """Inverse cosecant"""
    return np.arcsin(1. / val)

def arccot(val):
    """Inverse cotangent"""
    if np.real(val) < 0:
        return -np.pi / 2 - np.arctan(val)
    else:
        return np.pi / 2 - np.arctan(val)

# Hyperbolic Trig
def sech(arg):
    """Hyperbolic secant"""
    return 1 / np.cosh(arg)

def csch(arg):
    """Hyperbolic cosecant"""
    return 1 / np.sinh(arg)

def coth(arg):
    """Hyperbolic cotangent"""
    return 1 / np.tanh(arg)

# And their inverses
def arcsech(val):
    """Inverse hyperbolic secant"""
    return np.arccosh(1. / val)

def arccsch(val):
    """Inverse hyperbolic cosecant"""
    return np.arcsinh(1. / val)

def arccoth(val):
    """Inverse hyperbolic cotangent"""
    return np.arctanh(1. / val)

# NOTE: tests are in a separate file, NOT doctests.
# see https://bugs.python.org/issue6835
@SpecifyDomain.make_decorator((1,), (1,))
def arctan2(x, y):
    """
    Returns the an angle in range (-pi, pi] whose tangent is y/x, taking into
    account the quadrant that (x, y) is in.
    """
    if x == 0 and y == 0:
        raise FunctionEvalError("arctan2(0, 0) is undefined")

    return np.arctan2(y, x)

# NOTE: tests are in a separate file, NOT doctests.
# see https://bugs.python.org/issue6835
@SpecifyDomain.make_decorator((1,), (1,))
def kronecker(x, y):
    """
    Returns 1 if x==y, and 0 otherwise.
    Note that this should really only be used for integer expressions.
    """
    if x == y:
        return 1
    return 0

def content_if_0d_array(obj):
    """
    If obj is a 0d numpy array, return its contents. Otherwise, return item.

    Usage:
    ======

    >>> content_if_0d_array(5) == 5
    True
    >>> content_if_0d_array(np.array(5)) == 5
    True
    >>> content_if_0d_array(np.array([1, 2, 3]))
    array([1, 2, 3])
    """
    return obj.item() if isinstance(obj, np.ndarray) and obj.ndim == 0 else obj

def real(z):
    """
    Returns the real part of z.
    >>> real(2+3j)
    2.0

    If the input is a number, a number is returned:
    >>> isinstance(real(2+3j), float)
    True

    Can be used with arrays, too:               # doctest: +NORMALIZE_WHITESPACE
    >>> real(np.array([1+10j, 2+20j, 3+30j]))
    array([ 1.,  2.,  3.])
    """
    # np.real seems to return 0d arrays for numerical inputs. For example,
    # np.real(2+3j) is a 0d array.
    return content_if_0d_array(np.real(z))

def imag(z):
    """
    Returns the imaginary part of z.
    >>> imag(2+3j)
    3.0

    If the input is a number, a number is returned:
    >>> isinstance(imag(2+3j), float)
    True

    Can be used with arrays, too:
    >>> imag(np.array([1+10j, 2+20j, 3+30j]))
    array([ 10.,  20.,  30.])
    """
    return content_if_0d_array(np.imag(z))

def factorial(z):
    """
    Factorial function over complex numbers, using the gamma function.
    Note that math.factorial will return long ints, which are problematic when running
    into overflow issues. The gamma function just returns inf.

    Usage
    =====

    Non-negative integer input returns floats:
    >>> factorial(4)
    24.0

    Floats and complex numbers use scipy's gamma function:
    >>> import math
    >>> factorial(0.5) # doctest: +ELLIPSIS
    0.8862269...
    >>> math.sqrt(math.pi)/2 # doctest: +ELLIPSIS
    0.8862269...
    >>> factorial(3.2+4.1j) # doctest: +ELLIPSIS
    (1.0703272...-0.3028032...j)
    >>> factorial(2.2+4.1j)*(3.2+4.1j) # doctest: +ELLIPSIS
    (1.0703272...-0.3028032...j)

    Works with numpy arrays:
    >>> np.array_equal(
    ...     factorial(np.array([1, 2, 3, 4])),
    ...     np.array([1, 2, 6, 24])
    ... )
    True

    Really big numbers return inf:
    >>> factorial(500) == float('inf')
    True
    >>> factorial(500.5) == float('inf')
    True

    Throws errors at poles:
    >>> try:                                                # doctest: +ELLIPSIS
    ...     factorial(-2)
    ... except FunctionEvalError as error:
    ...     print(error)
    Error evaluating factorial() or fact() in input...
    """

    try:
        is_integer = isinstance(z, int) or z.is_integer()
    except AttributeError:
        is_integer = False

    if is_integer and z < 0:
        msg = ("Error evaluating factorial() or fact() in input. These "
               "functions cannot be used at negative integer values.")
        raise FunctionEvalError(msg)

    # lazy import this module for performance reasons
    import scipy.special as special

    value = special.gamma(z+1)
    # value is a numpy array; If it's 0d, we can just get its item:
    try:
        return value.item()
    except ValueError:
        return value

@SpecifyDomain.make_decorator((3,), (3,))
def cross(a, b):
    return MathArray([
        a[1]*b[2] - b[1]*a[2],
        a[2]*b[0] - b[2]*a[0],
        a[0]*b[1] - b[0]*a[1]
    ])

# Variables available by default
DEFAULT_VARIABLES = {
    'i': complex(0, 1),
    'j': complex(0, 1),
    'e': np.e,
    'pi': np.pi
}

# These act element-wise on numpy arrays
ELEMENTWISE_FUNCTIONS = {
    'sin': np.sin,
    'cos': np.cos,
    'tan': np.tan,
    'sec': sec,
    'csc': csc,
    'cot': cot,
    # We use scimath variants which give complex results when needed. For example:
    #   np.sqrt(-4+0j) = 2j
    #   np.sqrt(-4) = nan, but
    #   np.lib.scimath.sqrt(-4) = 2j
    'sqrt': np.lib.scimath.sqrt,
    'log10': np.lib.scimath.log10,
    'log2': np.lib.scimath.log2,
    'ln': np.lib.scimath.log,
    'exp': np.exp,
    'arccos': np.lib.scimath.arccos,
    'arcsin': np.lib.scimath.arcsin,
    'arctan': np.arctan,
    'arcsec': arcsec,
    'arccsc': arccsc,
    'arccot': arccot,
    'abs': np.abs,
    'fact': factorial,
    'factorial': factorial,
    'sinh': np.sinh,
    'cosh': np.cosh,
    'tanh': np.tanh,
    'sech': sech,
    'csch': csch,
    'coth': coth,
    'arcsinh': np.arcsinh,
    'arccosh': np.arccosh,
    'arctanh': np.lib.scimath.arctanh,
    'arcsech': arcsech,
    'arccsch': arccsch,
    'arccoth': arccoth,
    'floor': np.floor,
    'ceil': np.ceil
}

def has_one_scalar_input(display_name):
    return SpecifyDomain.make_decorator((1,), display_name=display_name)

def has_at_least_2_scalar_inputs(display_name):
    return SpecifyDomain.make_decorator((1,), display_name=display_name, min_length=2)

SCALAR_FUNCTIONS = {key: has_one_scalar_input(key)(ELEMENTWISE_FUNCTIONS[key])
                    for key in ELEMENTWISE_FUNCTIONS}

SCALAR_FUNCTIONS['arctan2'] = arctan2
SCALAR_FUNCTIONS['kronecker'] = kronecker

MULTI_SCALAR_FUNCTIONS = {
    'min': has_at_least_2_scalar_inputs('min')(min),
    'max': has_at_least_2_scalar_inputs('max')(max)
}

ARRAY_FUNCTIONS = {
    're': real,
    'im': imag,
    'conj': np.conj
}

def has_one_square_input(display_name):
    return SpecifyDomain.make_decorator('square', display_name=display_name)

def array_abs(obj):
    """
    Takes absolute value of numbers or vectors and suggests norm(...) instead
    for matrix/tensors.

    NOTE: The decision to limit abs(...) to scalars and vectors was motivated
    by pedagogy not software.
    """
    if isinstance(obj, MathArray) and obj.ndim > 1:
        msg = ("The abs(...) function expects a scalar or vector. To take the "
               "norm of a {}, try norm(...) instead.".format(
               MathArray.get_shape_name(obj.ndim)))
        raise FunctionEvalError(msg)
    return np.linalg.norm(obj)

ARRAY_ONLY_FUNCTIONS = {
    'norm': np.linalg.norm,
    'abs': array_abs,
    'trans': np.transpose,
    'det': has_one_square_input('det')(np.linalg.det),
    'trace': has_one_square_input('trace')(np.trace),
    'ctrans': lambda x: np.conj(np.transpose(x)),
    'adj': lambda x: np.conj(np.transpose(x)),
    'cross': cross
}

def merge_dicts(*source_dicts):
    """Create a new dictionary and merge sources into it."""
    target = {}
    for source in source_dicts:
        target.update(source)
    return target

DEFAULT_FUNCTIONS = merge_dicts(SCALAR_FUNCTIONS, MULTI_SCALAR_FUNCTIONS, ARRAY_FUNCTIONS)

DEFAULT_SUFFIXES = {
    '%': 0.01
}

METRIC_SUFFIXES = {
    'k': 1e3, 'M': 1e6, 'G': 1e9, 'T': 1e12,
    'm': 1e-3, 'u': 1e-6, 'n': 1e-9, 'p': 1e-12
}

pauli = {
    'sigma_x': MathArray([
        [0, 1],
        [1, 0]
    ]),
    'sigma_y': MathArray([
        [0, -1j],
        [1j, 0]
    ]),
    'sigma_z': MathArray([
        [1, 0],
        [0, -1]
    ])
}

cartesian_xyz = {
    'hatx': MathArray([1, 0, 0]),
    'haty': MathArray([0, 1, 0]),
    'hatz': MathArray([0, 0, 1])
}

cartesian_ijk = {
    'hati': MathArray([1, 0, 0]),
    'hatj': MathArray([0, 1, 0]),
    'hatk': MathArray([0, 0, 1])
}

def percentage_as_number(percent_str):
    """
    Convert a percentage string to a number.

    Args:
        percent_str: A percent string, for example '5%' or '1.2%'

    Usage
    =====
    >>> percentage_as_number('8%')
    0.08
    >>> percentage_as_number('250%')
    2.5
    >>> percentage_as_number('-10%')
    -0.1
    """
    return float(percent_str.strip()[:-1]) * 0.01

def within_tolerance(x, y, tolerance):
    """
    Check that |x-y| <= tolerance with appropriate norm.

    Args:
        x: number or array (np array_like)
        y: number or array (np array_like)
        tolerance: Number or PercentageString

    NOTE: Calculates x - y; may raise an error for incompatible shapes.

    Usage
    =====

    The tolerance can be a number:
    >>> within_tolerance(10, 9.01, 1)
    True
    >>> within_tolerance(10, 9.01, 0.5)
    False

    If tolerance is a percentage, it is a percent of (the norm of) x:
    >>> within_tolerance(10, 9.01, '10%')
    True
    >>> within_tolerance(9.01, 10, '10%')
    False

    Works for vectors and matrices:
    >>> A = np.array([[1,2],[-3,1]])
    >>> B = np.array([[1.1, 2], [-2.8, 1]])
    >>> diff = round(np.linalg.norm(A-B), 6)
    >>> diff
    0.223607
    >>> within_tolerance(A, B, 0.25)
    True

    Also works for infinities (ignores tolerance in this case)
    >>> inf = float('inf')
    >>> within_tolerance(inf, inf, 0)
    True
    >>> within_tolerance(-inf, -inf, 0)
    True
    >>> within_tolerance(inf, -inf, 0)
    False
    >>> within_tolerance(1, inf, '100%')
    False
    >>> within_tolerance(inf, 1, '100%')
    False

    However, cannot handle infinities in matrices.
    """
    # Handle infinities separately, ignoring any tolerance
    # Only do this for numbers, not matrices
    inf = float('inf')
    if isinstance(x, Number):
        if x == inf or y == inf or x == -inf or y == -inf:
            return x == y

    # When used within graders, tolerance has already been
    # validated as a Number or PercentageString
    if isinstance(tolerance, str):
        tolerance = np.linalg.norm(x) * percentage_as_number(tolerance)

    difference = x - y

    return np.linalg.norm(difference) <= tolerance

def is_nearly_zero(x, tolerance, reference=None):
    """
    Check that x is within tolerance of zero. If tolerance is provided as a
    percentage, a reference value is requied.

    Args:
        x: number or array (np array_like)
        reference: None number or array (np array_like), only used when
              tolerance is provided as a percentage
        tolerance: Number or PercentageString

    Usage
    =====
    >>> is_nearly_zero(0.4, 0.5)
    True
    >>> is_nearly_zero(0.4, 0.3)
    False
    >>> is_nearly_zero(0.4, '5%', reference=10)
    True
    >>> is_nearly_zero(0.4, '3%', reference=10)
    False

    Works for arrays, too:
    >>> x = np.array([[1, 1], [0, -1]])
    >>> np.linalg.norm(x)                                   # doctest: +ELLIPSIS
    1.732050...
    >>> is_nearly_zero(x, '18%', reference=10)
    True
    >>> is_nearly_zero(x, '17%', reference=10)
    False

    A ValueError is raised when percentage tolerance is used without reference:
    >>> try:
    ...     is_nearly_zero(0.4, '3%')
    ... except ValueError as error:
    ...     print(error)
    When tolerance is a percentage, reference must not be None.
    """
    # When used within graders, tolerance has already been
    # validated as a Number or PercentageString
    if isinstance(tolerance, str):
        if reference is None:
            raise ValueError('When tolerance is a percentage, reference must '
                'not be None.')
        tolerance = np.linalg.norm(reference) * percentage_as_number(tolerance)

    return np.linalg.norm(x) <= tolerance
