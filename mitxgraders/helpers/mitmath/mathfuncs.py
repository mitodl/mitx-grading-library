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
from __future__ import division
import math
import numpy as np
import scipy.special as special
from mitxgraders.helpers.mitmath.specify_domain import SpecifyDomain
from mitxgraders.exceptions import StudentFacingError
from mitxgraders.helpers.mitmath.exceptions import FunctionEvalError

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

    Can be used with arrays, too:
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
    >>> factorial(0.5) # doctest: +ELLIPSIS
    0.8862269...
    >>> math.sqrt(math.pi)/2
    0.8862269...
    >>> factorial(3.2+4.1j)
    (1.0703272...-0.3028032...j)
    >>> factorial(2.2+4.1j)*(3.2+4.1j)
    (1.0703272...-0.3028032...j)

    Works with numpy arrays:
    >>> np.array_equal(
    ...     factorial(np.array([1, 2, 3, 4])),
    ...     np.array([1, 2, 6, 24])
    ... )
    True

    Really big numbers return inf:
    >>> factorial(500.5) == float('inf')
    True

    Throws errors at poles:
    >>> factorial(-2)                           # doctest: +ELLIPSIS
    Traceback (most recent call last):
    FunctionEvalError: Error evaluating factorial() or fact() in input...
    """

    try:
        is_integer = isinstance(z, int) or z.is_integer()
    except AttributeError:
        is_integer = False

    if is_integer and z < 0:
        msg = ("Error evaluating factorial() or fact() in input. These "
               "functions cannot be used at negative integer values.")
        raise FunctionEvalError(msg)

    value = special.gamma(z+1)
    # value is a numpy array; If it's 0d, we can just get its item:
    try:
        return value.item()
    except ValueError:
        return value

# Variables available by default
DEFAULT_VARIABLES = {
    'i': np.complex(0, 1),
    'j': np.complex(0, 1),
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
    'arccoth': arccoth
}

def has_one_scalar_input(display_name):
    return SpecifyDomain.make_decorator((1,), display_name=display_name)

SCALAR_FUNCTIONS = {key: has_one_scalar_input(key)(ELEMENTWISE_FUNCTIONS[key])
                    for key in ELEMENTWISE_FUNCTIONS}

ARRAY_FUNCTIONS = {
    're': real,
    'im': imag,
    'conj': np.conj,
    'norm': np.linalg.norm
}

def merge_dicts(*dict_args):
    """Merge an arbitrary number of dictionaries."""
    merged = {}
    for dict_arg in dict_args:
        merged.update(dict_arg)
    return merged

DEFAULT_FUNCTIONS = merge_dicts(SCALAR_FUNCTIONS, ARRAY_FUNCTIONS)

DEFAULT_SUFFIXES = {
    '%': 0.01
}

METRIC_SUFFIXES = {
    'k': 1e3, 'M': 1e6, 'G': 1e9, 'T': 1e12,
    'm': 1e-3, 'u': 1e-6, 'n': 1e-9, 'p': 1e-12
}

def within_tolerance(x, y, tolerance):
    """
    Check that |x-y| <= tolerance with appropriate norm.

    Args:
        x: number or array (np array_like)
        y: number or array (np array_like)
        tolerance: Number or PercentageString

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
    >>> A = np.matrix([[1,2],[-3,1]])
    >>> B = np.matrix([[1.1, 2], [-2.8, 1]])
    >>> diff = round(np.linalg.norm(A-B), 6)
    >>> diff
    0.223607
    >>> within_tolerance(A, B, 0.25)
    True

    If x - y raises a StudentFacingError, then subtraction of these types
    is intentionally not supported and (x, y) are not within_tolerance:
    >>> class Foo():
    ...     def __sub__(self, other): raise StudentFacingError()
    ...     def __rsub__(self, other): raise StudentFacingError()
    >>> within_tolerance(0, Foo(), '1%')
    False
    """
    # When used within graders, tolerance has already been
    # validated as a Number or PercentageString
    if isinstance(tolerance, str):
        # Construct percentage tolerance
        tolerance = tolerance.strip()
        tolerance = np.linalg.norm(x) * float(tolerance[:-1]) * 0.01

    try:
        difference = x - y
    except StudentFacingError:
        # Apparently, the answer and the student_input cannot be compared.
        return False

    return np.linalg.norm(difference) <= tolerance
