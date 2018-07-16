"""
validatorfuncs.py

Stand-alone validator functions for use in voluptuous Schema
"""
from numbers import Number
from inspect import getargspec, isbuiltin
from voluptuous import All, Range, NotIn, Invalid, Schema, Any, Required, Length, truth, Coerce

def Positive(thetype):
    """Demand a positive number type"""
    if thetype == int:
        return All(thetype, Range(1, float('inf')))
    else:
        return All(thetype, Range(0, float('inf')), NotIn([0]))

def NonNegative(thetype):
    """Demand a non-negative number type"""
    return All(thetype, Range(0, float('inf')))

def PercentageString(value):
    """Validate that a string can be interpreted as a positive percentage."""
    if isinstance(value, str):
        work = value.strip()
        if work.endswith("%"):
            try:
                percent = float(work[:-1])
                if percent < 0:
                    raise Invalid("Cannot have a negative percentage")
                return "{percent}%".format(percent=percent)
            except Invalid:
                raise
            except:
                pass

    raise Invalid("Not a valid percentage string")

def number_range_alternate(number_type=Number):
    """
    Validator function that coerces a list [start, stop] into a dictionary
    Uses specific type number_type
    """
    def validatorfunc(config_as_list):
        alternate_form = Schema(All(
            [number_type, number_type],
            Length(min=2, max=2)
        ))
        config_as_list = alternate_form(config_as_list)
        return {'start': config_as_list[0], 'stop': config_as_list[1]}
    return validatorfunc

def NumberRange(number_type=Number):
    """
    Schema that allows for a start and stop, or alternatively, a list [start, stop]
    The type of number can be restricted by specifying number_type=int, for example
    """
    return Schema(Any(
        {
            Required('start', default=1): number_type,
            Required('stop', default=5): number_type
        },
        number_range_alternate(number_type)
    ))

def ListOfType(given_type, validator=None):
    """
    Validator that allows for a single given_type or a list of given_type.
    Also allows an extra validator to be applied to each item in the resulting list.
    """
    def func(config_input):
        # Wrap an individual given_type in a list
        if not isinstance(config_input, list):
            config_input = [config_input]
        # Apply the schema
        if validator:
            schema = Schema(All([given_type], Length(min=1), [validator]))
        else:
            schema = Schema(All([given_type], Length(min=1)))
        return schema(config_input)
    return func

def all_unique(iterable):
    """
    Voluptuous validator; tests whether all items in an iterable are unique

    Usage
    =====

    Returns the input if all items are unique:
    >>> iterable = ['a', 0, '1', '5']
    >>> all_unique(iterable) == iterable
    True

    Raises an error if any items are duplicated:
    >>> iterable = ['a', 0, '1', 'a', '5', 0, '0']
    >>> all_unique(iterable)
    Traceback (most recent call last):
    Invalid: items should be unique, but have unexpected duplicates: ['a', 0]
    """
    seen = set()
    duplicates = set()
    for item in iterable:
        if item in seen:
            duplicates.add(item)
        else:
            seen.add(item)

    if duplicates:
        msg = 'items should be unique, but have unexpected duplicates: {duplicates}'
        raise Invalid(msg.format(iterable=iterable, duplicates=list(duplicates)))

    return iterable

def has_keys_of_type(thetype):
    """
    Create a voluptuous validator to check that dict keys are all of thetype.

    Arguments
        thetype (type): specifies dict key types

    Usage:
    ======

    Returns argument if valid:
    >>> valid = {'0': 'a', '1': 'b', 'cat': [1, 2]}
    >>> validator = has_keys_of_type(str)
    >>> validator(valid) == valid
    True

    Raises error if argument has invalid keys:
    >>> invalid_keys = {'0': 'a', 1: 'b', 'cat': [1, 2]}
    >>> validator(invalid_keys)
    Traceback (most recent call last):
    Invalid: 1 is not a valid key, must be of <type 'str'>

    or if argument is not a dictionary:
    >>> not_dict = 5
    >>> validator(not_dict)
    Traceback (most recent call last):
    Invalid: expected a dictionary with keys of <type 'str'>
    """
    def validator(thedict):
        if not isinstance(thedict, dict):
            raise Invalid('expected a dictionary with keys of {}'.format(thetype))
        for key in thedict:
            if not isinstance(key, thetype):
                raise Invalid("{key} is not a valid key, must be of {thetype}"
                              .format(key=key, thetype=thetype))

        return thedict
    return validator

@truth
def is_callable(obj):
    """Returns true if obj is callable"""
    return callable(obj)

def get_builtin_positional_args(obj):
    """
    Get the number of position arguments on a built-in function by inspecting
    its docstring. (Built-in functions cannot be inspected by inspect.getargspec.)

    >>> pow.__doc__     # doctest: +ELLIPSIS
    'pow(x, y[, z]) -> number...
    >>> get_builtin_positional_args(pow)
    2
    """
    # Built-in functions cannot be inspected by
    # inspect.getargspec. We have to try and parse
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

    Works for bound and unbound callable objects
    >>> class Bar:
    ...     def __call__(self, x, y):
    ...         return x + y
    >>> get_number_of_args(Bar) # unbound, is NOT automatically passed self as argument
    3
    >>> bar = Bar()
    >>> get_number_of_args(bar) # bound, is automatically passed self as argument
    2

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
    if isbuiltin(callable_obj):
        # Built-in function
        func = callable_obj
        return get_builtin_positional_args(func)
    elif hasattr(callable_obj, "nin"):
        # Matches RandomFunction or numpy ufunc
        return callable_obj.nin
    else:
        try:
            # Assume object is a function
            func = callable_obj
            # see https://docs.python.org/2/library/inspect.html#inspect.getargspec
            # defaults might be None, or something weird for Mock functions
            args, _, _, defaults = getargspec(func)
        except TypeError:
            # Callable object
            func = callable_obj.__call__
            args, _, _, defaults = getargspec(func)

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

def is_callable_with_args(num_args):
    """
    Validates that a function is callable and takes num_args arguments

    Examples:
    >>> def func(x, y): return x + y
    >>> is_callable_with_args(2)(func) == func
    True
    >>> is_callable_with_args(3)(func) == func # doctest: +ELLIPSIS
    Traceback (most recent call last):
    Invalid: Expected function... to have 3 arguments, instead it has 2

    Callable objects work, too:
    >>> class Foo:
    ...     def __call__(self, x):
    ...         return x
    >>> foo = Foo()
    >>> is_callable_with_args(1)(foo) == foo
    True
    >>> is_callable_with_args(1)(Foo) # doctest: +ELLIPSIS
    Traceback (most recent call last):
    Invalid: Expected function... to have 1 arguments, instead it has 2
    """
    def _validate(func):
        # first, check that the function is callable
        is_callable(func)  # raises an error if not callable
        f_args = get_number_of_args(func)
        if not f_args == num_args:
            msg = "Expected function {func} to have {num_args} arguments, instead it has {f_args}"
            raise Invalid(msg.format(func=func, num_args=num_args, f_args=f_args))
        return func

    return _validate

def TupleOfType(given_type, validator=None):
    """
    Validator that allows for a single given_type or a tuple of given_type.
    Also allows an extra validator to be applied to each item in the resulting tuple.
    """
    def func(config_input):
        # Wrap an individual given_type in a tuple
        if not isinstance(config_input, tuple):
            config_input = (config_input,)
        # Apply the schema
        if validator:
            schema = Schema(All((given_type,), Length(min=1), (validator, )))
        else:
            schema = Schema(All((given_type,), Length(min=1)))
        return schema(config_input)
    return func

def is_shape_specification(min_dim=1, max_dim=None):
    """
    Validates shape specification for arrays.

    Valid inputs are standardized to tuples:
    >>> vec_or_mat = Schema(is_shape_specification(min_dim=1, max_dim=2))
    >>> map(vec_or_mat, [3, (3,), [3], (4, 2), [4, 2] ])
    [(3,), (3,), (3,), (4, 2), (4, 2)]

    Invalid inputs raise a useful error:
    >>> vec_or_mat(0)                               # doctest: +ELLIPSIS
    Traceback (most recent call last):
    MultipleInvalid: expected shape specification to be a positive integer,...
    """

    msg = ('expected shape specification to be a positive integer, or a '
           'list/tuple of positive integers (min length {0}, max length {1})'
           .format(min_dim, max_dim))
    return All(
        Any(
            All(Positive(int), lambda x: (x, )),
            (Positive(int), ),
            All([Positive(int)], Coerce(tuple)),
            msg=msg
        ),
        Length(min=min_dim, max=max_dim),
    )
