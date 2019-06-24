from __future__ import print_function, division, absolute_import

import sys, re
from functools import wraps

def log_results(results):
    """
    Generate a decorator that logs function calls to results.

    Arguments:
        results: list into which results are logged
    Returns:
        Decorator that logs result of each call to function to results

    Usage:
    >>> results = []
    >>> @log_results(results)
    ... def f(x, y):
    ...     return x + y
    >>> f(2, 3); f(20, 30);
    5
    50
    >>> results
    [5, 50]
    """

    def make_decorator(results):
        def decorator(func):
            @wraps(func)
            def _func(*args, **kwargs):
                result = func(*args,**kwargs)
                results.append(result)
                return result

            return _func
        return decorator

    return make_decorator(results)

def round_decimals_in_string(string, round_to=6):
    """
    Round all decimals in a string to a specified number of places.

    Usage
    =====
    >>> s = "pi is 3.141592653589793 and e is 2.71828182845904523536028747 and one is 1.000"
    >>> round_decimals_in_string(s)
    'pi is 3.141593 and e is 2.718282 and one is 1.000'

    Note that the final occurrence of 1.000 was not rounded.
    """
    pattern = "([0-9]*\.[0-9]{{{round_to}}}[0-9]*)".format(round_to=round_to)
    def replacer(match):
        number = float(match.group(1))
        formatter = "{{0:.{round_to}f}}".format(round_to=round_to)
        return formatter.format(number)

    return re.sub(pattern, replacer, string)

if sys.version_info >= (3,):
    import unittest.mock as mock
else:
    import mock
