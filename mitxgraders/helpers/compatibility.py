"""
Helper functions to facilitate numpy ufuncs compatibility
"""


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
