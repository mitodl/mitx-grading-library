import numpy as np
"""
Contains the power function used by MathArray and parsing.py
"""

# This is used in calc.py's eval_power function also.
def robust_pow(base, exponent):
    """
    Calculates __pow__, and tries other approachs if that doesn't work.

    Usage:
    ======

    >>> robust_pow(5, 2)
    25
    >>> robust_pow(0.5, -1)
    2.0

    If base is negative and power is fractional, complex results are returned:
    >>> almost_j = robust_pow(-1, 0.5)
    >>> np.allclose(almost_j, 1j)
    True
    """
    try:
        return base ** exponent
    except ValueError:
        return np.lib.scimath.power(base, exponent)
