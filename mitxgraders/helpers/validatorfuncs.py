"""
validatorfuncs.py

Stand-alone validator functions for use in voluptuous Schema
"""
from __future__ import print_function, division, absolute_import, unicode_literals

from numbers import Number
import six
from voluptuous import All, Range, NotIn, Invalid, Schema, Any, Required, Length, truth, Coerce
from mitxgraders.helpers.compatibility import ensure_text
from mitxgraders.helpers.get_number_of_args import get_number_of_args

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
    if isinstance(value, six.string_types):
        work = value.strip()
        if work.endswith("%"):
            try:
                percent = float(work[:-1])
                if percent < 0:
                    raise Invalid("Cannot have a negative percentage")
                return "{percent}%".format(percent=percent)
            except Invalid:
                raise
            except Exception:
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
    >>> try:
    ...     all_unique(iterable)
    ... except Invalid as error:
    ...     print(error)
    items should be unique, but have unexpected duplicates: ['a', 0]
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
    >>> validator = has_keys_of_type(six.text_type)
    >>> validator(valid) == valid
    True

    Raises error if argument has invalid keys:
    >>> validator = has_keys_of_type(int)
    >>> invalid_keys = {0: 'a', 1: 'b', 3.14: 'dog'}
    >>> try:                                                # doctest: +ELLIPSIS
    ...     validator(invalid_keys)
    ... except Invalid as error:
    ...     print(error)
    3.14 is not a valid key, must be of <... 'int'>

    or if argument is not a dictionary:
    >>> not_dict = 5
    >>> try:                                                # doctest: +ELLIPSIS
    ...     validator(not_dict)
    ... except Invalid as error:
    ...     print(error)
    expected a dictionary with keys of <... 'int'>
    """
    if thetype == six.string_types:
        formatted_thetype = 'type string'
    else:
        formatted_thetype = six.text_type(thetype)

    def validator(thedict):
        if not isinstance(thedict, dict):
            raise Invalid('expected a dictionary with keys of {}'.format(formatted_thetype))
        for key in thedict:
            if not isinstance(key, thetype):
                raise Invalid("{key} is not a valid key, must be of {thetype}"
                              .format(key=key, thetype=formatted_thetype))

        return thedict
    return validator

@truth
def is_callable(obj):
    """Returns true if obj is callable"""
    return callable(obj)

def is_callable_with_args(num_args):
    """
    Validates that a function is callable and takes num_args arguments

    Examples:
    >>> def func(x, y): return x + y
    >>> is_callable_with_args(2)(func) == func
    True
    >>> try:                                                # doctest: +ELLIPSIS
    ...     is_callable_with_args(3)(func) == func
    ... except Invalid as error:
    ...     print(error)
    Expected function ... to have 3 arguments, instead it has 2

    Callable objects work, too:
    >>> class Foo:
    ...     def __call__(self, x):
    ...         return x
    >>> foo = Foo()
    >>> is_callable_with_args(1)(foo) == foo
    True
    >>> try:                                                # doctest: +ELLIPSIS
    ...     is_callable_with_args(2)(foo)
    ... except Invalid as error:
    ...     print(error)
    Expected function ... to have 2 arguments, instead it has 1
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
    >>> valid_examples = [3, (3,), [3], (4, 2), [4, 2] ]
    >>> [vec_or_mat(item) for item in valid_examples]
    [(3,), (3,), (3,), (4, 2), (4, 2)]

    Invalid inputs raise a useful error:
    >>> try:                                                # doctest: +ELLIPSIS
    ...     vec_or_mat(0)
    ... except Invalid as error:
    ...     print(error)
    expected shape specification to be a positive integer,...
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

def Nullable(schema):
    """
    Indicates that a value could be None or satisfy schema.
    """
    return Any(None, schema)

def text_string(obj):
    """
    Voluptuous validator that expects text strings and coerces Python 2 string
    literals to unicode.
    """
    if isinstance(obj, six.string_types):
        return ensure_text(obj)

    raise Invalid('expected str (or unicode)')
