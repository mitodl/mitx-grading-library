import inspect


def get_number_of_args(callable_obj):
    """
    Get number of positional arguments of function or callable object.
    Based on inspect.signature

    Examples
    ========

    Works for simple functions:
    >>> def f(x, y):
    ...     return x + y
    >>> get_number_of_args(f)
    2

    Positional arguments only:
    >>> def f(x, y, z=5):
    ...     return x + y
    >>> get_number_of_args(f)
    2

    Works with bound and unbound object methods
    >>> class Foo:
    ...     def do_stuff(self, x, y, z):
    ...         return x*y*z
    >>> get_number_of_args(Foo.do_stuff) # unbound, is NOT automatically passed self as argument
    4
    >>> foo = Foo()
    >>> get_number_of_args(foo.do_stuff) # bound, is automatically passed self as argument
    3

    Works for callable objects instances:
    >>> class Bar:
    ...     def __call__(self, x, y):
    ...         return x + y
    >>> bar = Bar()
    >>> get_number_of_args(bar) # bound instance, is automatically passed self as argument
    2

    Works on built-in functions (assuming their docstring is correct)
    >>> get_number_of_args(pow)
    2

    Works on numpy ufuncs
    >>> import numpy as np
    >>> get_number_of_args(np.sin)
    1

    Works on RandomFunctions (tested in unit tests due to circular imports)
    """
    if hasattr(callable_obj, "nin"):
        # Matches RandomFunction or numpy ufunc
        # Sadly, even Py3's inspect.signature can't handle numpy ufunc...
        return callable_obj.nin

    params = inspect.signature(callable_obj).parameters
    empty = inspect.Parameter.empty
    return sum([params[key].default == empty for key in params])
