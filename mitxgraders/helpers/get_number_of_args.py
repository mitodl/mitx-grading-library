import inspect
import six

def get_builtin_positional_args(obj):
    """
    Get the number of position arguments on a built-in function by inspecting
    its docstring. (Built-in functions cannot be inspected by inspect.inspect.getargspec.)

    NOTE:
        - works in Python 3, but intended for Python 2

    >>> pow.__doc__     # doctest: +ELLIPSIS
    'pow(x, y[, z]) -> number...
    >>> get_builtin_positional_args(pow)
    2
    """
    # Built-in functions cannot be inspected by
    # inspect.inspect.getargspec. We have to try and parse
    # the __doc__ attribute of the function.
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

def get_number_of_args_py2(callable_obj):
    """
    Get number of positional arguments of function or callable object.

    NOTES:
        - Seems to work in Python 3, but is based on inspect.getargspec which
          raises a DeprecationWarning in Python 3.
        - in Python 3, use the much simpler signature-based
          get_number_of_args_py3 funciton instead.
        - Cannot handle class constructors

    Usage
    =====
    See documentation for get_number_of_args.

    Note, however, that this function cannot handle class constructors:

    >>> class Foo(object):
    ...     def __init__(self, x, y):
    ...         pass
    >>> try:                                                # doctest: +ELLIPSIS
    ...     get_number_of_args_py2(Foo)
    ... except ValueError as error:
    ...     print(error)
    Cannot detect number of arguments for <class '...Foo'>


    """

    if inspect.isbuiltin(callable_obj):
        # Built-in function
        func = callable_obj
        return get_builtin_positional_args(func)
    elif hasattr(callable_obj, "nin"):
        # Matches RandomFunction or numpy ufunc
        return callable_obj.nin
    else:
        if inspect.isfunction(callable_obj) or inspect.ismethod(callable_obj):
            # Assume object is a function
            func = callable_obj
            # see https://docs.python.org/2/library/inspect.html#inspect.inspect.getargspec
            # defaults might be None, or something weird for Mock functions
        elif inspect.isclass(callable_obj):
            # We don't need this anyway
            raise ValueError("Cannot detect number of arguments for {}".format(callable_obj))
        else:
            # callable object instance
            func = callable_obj.__call__

        args, _, _, defaults = inspect.getargspec(func)

    try:
        num_args = len(args) - len(defaults)
    except TypeError:
        num_args = len(args)

    # If func is a bound method, remove one argument
    # (in Python 2.7, unbound methods have __self__ = None)
    try:
        if func.__self__ is not None:
            num_args += -1
    except AttributeError:
        pass

    return num_args

def get_number_of_args_py3(callable_obj):
    """
    Get number of positional arguments of function or callable object.

    NOTES:
        - based on inspect.signature
        - in Python 2, use getargspec-based get_number_of_args_py2 instead
    """
    if hasattr(callable_obj, "nin"):
        # Matches RandomFunction or numpy ufunc
        # Sadly, even Py3's inspect.signature can't handle numpy ufunc...
        return callable_obj.nin

    params = inspect.signature(callable_obj).parameters
    empty = inspect.Parameter.empty
    return sum([params[key].default == empty for key in params])

def get_number_of_args(callable_obj):
    """
    Get number of positional arguments of function or callable object.

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

    Note about class constructors: In Python 2, get_number_of_args(Bar) will
    raise an error; in Python 3, the number of arguments of __init__ is returned.

    Works on built-in functions (assuming their docstring is correct)
    >>> import math
    >>> get_number_of_args(math.sin)
    1

    Works on numpy ufuncs
    >>> import numpy as np
    >>> get_number_of_args(np.sin)
    1

    Works on RandomFunctions (tested in unit tests due to circular imports)
    """
    if six.PY2:
        return get_number_of_args_py2(callable_obj)
    return get_number_of_args_py3(callable_obj)
