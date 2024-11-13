import inspect
import six

def get_builtin_positional_args_py2(obj):
    """
    Get the number of position arguments on a built-in function by inspecting
    its docstring. (Built-in functions cannot be inspected by inspect.inspect.getargspec.)

    NOTES:
        - Only works in Python 2: depends on structure of builtin docstrings,
          which changed from py2 to py3
    """
    # Built-in functions cannot be inspected by
    # inspect.inspect.getargspec. We have to try and parse
    # the __doc__ attribute of the function.
    # In Python 2, builtin docstrings begin with a line that reveals
    # the signature, for example, pow.__doc__ looks like:
    # """
    # pow(...)
    # pow(x, y[, z]) -> number
    #
    # With two arguments, equivalent to x**y...
    # """
    docstr = obj.__doc__
    if docstr:
        items = docstr.split('\n')
        if items:
            func_descr = items[0]
            s = func_descr.replace(obj.__name__, '')
            idx1 = s.find('(')
            idx_default = s.find('[')
            idx2 = s.find(')') if idx_default == -1 else idx_default
            if idx1 != -1 and idx2 != -1 and (idx2 > idx1+1):
                argstring = s[idx1+1:idx2]
                # This gets the argument string
                # Count the number of commas!
                return argstring.count(",") + 1
    return 0  # pragma: no cover

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
