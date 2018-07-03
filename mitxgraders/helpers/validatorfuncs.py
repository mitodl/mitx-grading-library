"""
validatorfuncs.py

Stand-alone validator functions for use in voluptuous Schema
"""
from numbers import Number
from inspect import getargspec
from voluptuous import All, Range, NotIn, Invalid, Schema, Any, Required, Length, truth

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

@truth
def is_callable(obj):
    """Returns true if obj is callable"""
    return callable(obj)

def get_number_of_args(callable_obj):
    """
    Get number of arguments of function or callable object.

    Examples
    ========

    Works for simple functions:
    >>> def f(x, y):
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
    """

    try:
        # assume object is a function
        func = callable_obj
        num_args = len(getargspec(func)[0])
    except TypeError:
        # otherwise it is a callable object
        func = callable_obj.__call__
        num_args = len(getargspec(func)[0])

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
