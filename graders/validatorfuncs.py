"""Standalone validator functions for use in voluptuous Schema."""

from voluptuous import All, Range, NotIn

def Positive(thetype):
    if thetype==int:
        return All(thetype, Range(1, float('inf')))
    else:
        return All(thetype, Range(0, float('inf')), NotIn([0]))

def NonNegative(thetype):
    return All(thetype, Range(0, float('inf')))

def PercentageString(value):
    """Validate that a string can be interpretted as a percentage."""
    if isinstance(value, str) and value.endswith("%"):
        try:
            percent = float(value[:-1])
            return "{percent}%".format(percent=percent)
        except:
            pass

    raise ValueError("Not a percentage string.")