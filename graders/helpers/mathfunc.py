"""
mathfunc.py

Contains mathematical functions for use in interpreting formulas.

Contains some helper functions used in grading formulae:
* within_tolerance
* construct_functions
* construct_constants
* construct_suffixes

Defines:
* DEFAULT_FUNCTIONS
* DEFAULT_VARIABLES
* DEFAULT_SUFFIXES
* METRIC_SUFFIXES
"""
from __future__ import division
import math
import numpy as np
from graders.baseclasses import ConfigError
from graders.sampling import SpecificFunctions, FunctionSamplingSet

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


# Variables available by default
DEFAULT_VARIABLES = {
    'i': np.complex(0, 1),
    'j': np.complex(0, 1),
    'e': np.e,
    'pi': np.pi
}

# Functions available by default
# We use scimath variants which give complex results when needed. For example:
#   np.sqrt(-4+0j) = 2j
#   np.sqrt(-4) = nan, but
#   np.lib.scimath.sqrt(-4) = 2j
DEFAULT_FUNCTIONS = {
    'sin': np.sin,
    'cos': np.cos,
    'tan': np.tan,
    'sec': sec,
    'csc': csc,
    'cot': cot,
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
    'fact': math.factorial,
    'factorial': math.factorial,
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
    # lambdas because sometimes np.real/imag returns an array,
    're': lambda x: float(np.real(x)),
    'im': lambda x: float(np.imag(x)),
    'Re': lambda x: float(np.real(x)),
    'Im': lambda x: float(np.imag(x)),
    'conj': np.conj,
}

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
    """
    # When used within graders, tolerance has already been
    # validated as a Number or PercentageString
    if isinstance(tolerance, str):
        # Construct percentage tolerance
        tolerance = tolerance.strip()
        tolerance = np.linalg.norm(x) * float(tolerance[:-1]) * 0.01
    return np.linalg.norm(x-y) <= tolerance

def construct_functions(whitelist, blacklist, user_funcs):
    """
    Returns the dictionary of available functions

    Arguments:
        whitelist (list): List of function names to allow, ignored if empty.
            To disallow all functions, use whitelist = [None].

        blacklist (list): List of function names to disallow. whitelist and blacklist
            cannot be used in conjunction.

        user_funcs (dict): Dictionary of "name": function pairs specifying user-defined
            functions to include.
    """
    if whitelist:
        if blacklist:
            raise ConfigError("Cannot whitelist and blacklist at the same time")

        functions = {}
        for f in whitelist:
            if f is None:
                # This allows for you to have whitelist = [None], which removes
                # all functions from the function list
                continue
            try:
                functions[f] = DEFAULT_FUNCTIONS[f]
            except KeyError:
                raise ConfigError("Unknown function in whitelist: " + f)
    else:
        # Treat no blacklist as blacklisted with an empty list
        functions = DEFAULT_FUNCTIONS.copy()
        for f in blacklist:
            try:
                del functions[f]
            except KeyError:
                raise ConfigError("Unknown function in blacklist: " + f)

    # Add in any custom functions to the functions and random_funcs lists
    random_funcs = {}
    for f in user_funcs:
        if not isinstance(f, str):
            msg = str(f) + " is not a valid name for a function (must be a string)"
            raise ConfigError(msg)
        # Check if we have a random function or a normal function
        if isinstance(user_funcs[f], list):
            # A list of functions; convert to a SpecificFunctions class
            random_funcs[f] = SpecificFunctions(user_funcs[f])
        elif isinstance(user_funcs[f], FunctionSamplingSet):
            random_funcs[f] = user_funcs[f]
        else:
            # f is a normal function
            functions[f] = user_funcs[f]

    return functions, random_funcs

def construct_constants(user_consts):
    """
    Returns the dictionary of available constants
    user_consts is a dictionary of "name": value pairs of constants to add to the defaults
    """
    constants = DEFAULT_VARIABLES.copy()

    # Add in any user constants
    for var in user_consts:
        if not isinstance(var, str):
            msg = str(var) + " is not a valid name for a constant (must be a string)"
            raise ConfigError(msg)
        constants[var] = user_consts[var]

    return constants

def construct_suffixes(metric=False):
    """
    Returns the dictionary of available suffixes.
    Setting metric=True adds in the metric suffixes.
    """
    suffixes = DEFAULT_SUFFIXES.copy()
    if metric:
        suffixes.update(METRIC_SUFFIXES)
    return suffixes
