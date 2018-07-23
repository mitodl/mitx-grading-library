from numbers import Number
from mitxgraders.helpers.calc.math_array import MathArray

def get_description(obj, detailed=True):
    """
    Gets a student-facing description of obj.

    Arguments:
        obj: the object to describe
        detailed (bool): for MathArray instances, whether to provide the shape
            or only the shape name (scalar, vector, matrix, tensor)

    Numbers return scalar:
    >>> get_description(5)
    'scalar'

    MathArrays return their own description:
    >>> get_description(MathArray([1, 2, 3]))
    'vector of length 3'

    Unless detailed=False, then only type is provided:
    >>> get_description(MathArray([1, 2, 3]), detailed=False)
    'vector'

    Other objects return their class name:
    >>> get_description("puppy")
    'str'
    """
    if isinstance(obj, Number):
        return 'scalar'
    elif isinstance(obj, MathArray):
        return obj.description if detailed else obj.shape_name
    else:
        return obj.__class__.__name__
