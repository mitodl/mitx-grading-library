"""
Helper functions to facilitate python2-python3 compatibility
"""
from __future__ import print_function, division, absolute_import, unicode_literals

import six
import functools

def wraps(wrapped,
          assigned=functools.WRAPPER_ASSIGNMENTS,
          updated=functools.WRAPPER_UPDATES):
    """
    A light wrapper around functools.wraps to facilitate compatibility with
    Python 3, and numpy ufuncs.

    Uses __name__ as __qualname__ if __qualname__ doesn't exist
    (this helps with numpy ufuncs, which do not have a __qualname__)

    References:
        functools source:
        https://github.com/python/cpython/blob/master/Lib/functools.py
    """
    pruned_assigned = tuple(attr for attr in assigned if hasattr(wrapped, attr))
    wrapper = functools.wraps(wrapped, pruned_assigned, updated)
    def _wrapper(f):
        _f = wrapper(f)
        if '__qualname__' not in pruned_assigned and '__name__' in pruned_assigned:
            _f.__qualname__ = _f.__name__
        return _f
    return _wrapper

def coerce_string_keys_to_text_type(thedict):
    """
    Ensures that dictionary string keys are text strings.
    """
    result = {}
    for key in thedict:
        if isinstance(key, six.string_types):
            new_key = str(key)
            result[new_key] = thedict[key]
        else:
            result[key] = thedict[key]

    return result
