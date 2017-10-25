"""
validatorfuncs.py

Stand-alone validator functions for use in voluptuous Schema
"""
from numbers import Number
from graders.voluptuous import All, Range, NotIn, Invalid, Schema, Any, Required, Length, truth

def Positive(thetype):
    if thetype == int:
        return All(thetype, Range(1, float('inf')))
    else:
        return All(thetype, Range(0, float('inf')), NotIn([0]))

def NonNegative(thetype):
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

@truth
def is_callable(obj):
    """Returns true if obj is callable"""
    return callable(obj)

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
            schema = Schema(All((given_type,), Length(min=1), [validator]))
        else:
            schema = Schema(All((given_type,), Length(min=1)))
        return schema(config_input)
    return func
