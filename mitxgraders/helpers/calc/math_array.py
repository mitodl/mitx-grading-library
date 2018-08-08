"""
math_array.py

Contains a subclass of numpy.ndarray with matrix-like operations.
"""

from __future__ import division  # necessary for one of the doctests
from contextlib import contextmanager
from numbers import Number
import numpy as np
from mitxgraders.helpers.calc.exceptions import (
    MathArrayError, MathArrayShapeError as ShapeError)
from mitxgraders.helpers.calc.robust_pow import robust_pow

def is_number_zero(value):
    """
    Tests whether a value is the scalar number 0.

    >>> map(is_number_zero, [0, 0.0, 0j])
    [True, True, True]
    >>> is_number_zero(np.matrix([0, 0, 0]))
    False
    """
    return isinstance(value, Number) and value == 0

def is_numberlike_array(obj):
    """
    Test than obj is a MathArray with 1 item

    >>> is_numberlike_array(MathArray(5))
    True
    >>> is_numberlike_array(MathArray([5]))
    True
    >>> is_numberlike_array(MathArray([[5]]))
    True
    >>> is_numberlike_array(MathArray([5, 5]))
    False


    The unique item of a numberlike array is a number:
    >>> numberlike = MathArray([[[[5]]]])
    >>> is_numberlike_array(numberlike)
    True
    >>> isinstance(numberlike.item(), Number)
    True
    """
    return isinstance(obj, MathArray) and obj.size == 1

def is_numberlike_zero_array(obj):
    """
    Tests if value is a scalar MathArray with value 0.

    >>> zero = MathArray(0)
    >>> is_numberlike_zero_array(zero)
    True
    >>> is_numberlike_zero_array(MathArray([[[0]]]))
    True
    >>> five = MathArray(5) # scalar MathArray, but not zero
    >>> is_numberlike_zero_array(MathArray(5))
    False
    >>> is_numberlike_zero_array(MathArray([0, 0, 0])) # vector zero, not scalar
    False
    >>> is_numberlike_zero_array(0) # number zero, not MathArray
    False
    """
    return is_numberlike_array(obj) and obj.item() == 0

def is_square(array):
    return array.ndim == 2 and array.shape[0] == array.shape[1]

def is_vector(obj):
    """Tests if obj is a vector MathArray"""
    return isinstance(obj, MathArray) and obj.ndim == 1

class MathArray(np.ndarray):
    """
    A modification of numpy's ndarray class that behaves more like a mathematician would expect.

    Terminology:
    ============
        - vector, 1 dimensional, e.g., MathArray([1, 2, 3])
        - matrix, 2 dimensional, e.g., MathArray([[1, 2], [3, 4]])
        - tensor, 3+ dimensional, e.g., MathArray([ [[1]], [[2]] ])

    Zero-dimensional arrays, e.g., MathArray(5) are also supported but should
    not occur in practice.

        - scalar: Python number OR zero-dimensional array

    Differences from numpy.ndarray:
    ==============================
        - Multiplication:
            - scalar * array = scales elements of array;
            - array * scalar = scales elements of array;
            If shapes are correct:
            - vector * vector = number
            - matrix * vector = vector
            - vector * matrix = vector
            - matrix * matrix = matrix
            Any multiplication involving tensors and arrays of dimension >1 is not supported.
        - powers are only allowed for square matrices and integer-like exponents.
        - supports multiplication with a universal identity irrespective of own shape
        - supports addition/subtraction with a universal identity if MathArray is square matrix.
        - throws ShapeError instances when anticipated errors are made.
        Raised with student-friendly error messages.
    """

    def __new__(cls, input_array):
        """
        Creates a new MathArray Instance.

        Note: The ndarray constructor is very low-level and apparently not meant
        to be used, hence we need our own. This is a quirk of subclassing
        ndarray. See https://docs.scipy.org/doc/numpy/user/basics.subclassing.html
        for more info.

        No need for __array_finalize__ since we do not add any any properties
        (except computed properties like shape_name).
        """

        return np.asarray(input_array).view(cls)

    @staticmethod
    def get_shape_name(ndim):
        names = {
            0: 'scalar',
            1: 'vector',
            2: 'matrix',
        }
        return names.get(ndim, 'tensor')

    @property
    def shape_name(self):
        return self.get_shape_name(self.ndim)

    @staticmethod
    def get_description(shape):
        ndim = len(shape)
        shape_name = MathArray.get_shape_name(ndim)
        if ndim == 0:
            return shape_name
        elif ndim == 1:
            return '{shape_name} of length {shape[0]}'.format(shape_name=shape_name, shape=shape)
        elif ndim == 2:
            return ('{shape_name} of shape (rows: {shape[0]}, cols: '
                    '{shape[1]})').format(shape_name=shape_name, shape=shape)
        else:
            return '{shape_name} of shape {shape}'.format(shape_name=shape_name, shape=shape)

    @property
    def description(self):
        return self.get_description(self.shape)

    def __add__(self, other):
        super_ADD = super(MathArray, self).__add__

        if is_number_zero(other):
            return super_ADD(other)

        elif is_numberlike_zero_array(other):
            return super_ADD(other.item())

        elif isinstance(other, Number):
            if is_numberlike_array(self):
                return self.item() + (other)
            raise ShapeError("Cannot add/subtract scalars to a {self.shape_name}."
                                 .format(self=self))

        elif isinstance(other, MathArray):
            if self.shape == other.shape:
                return super_ADD(other)
            elif is_numberlike_zero_array(self):
                return self.item() + other

            msg = ("Cannot add/subtract a {self.description} with a {other.description}.").format(
                self=self, other=other)
            raise ShapeError(msg)

        raise TypeError("Cannot add/subtract a {self.shape_name} with object of {type}."
                        .format(type=type(other), self=self))

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        return self.__add__(-1*other)

    def __rsub__(self, other):
        return (-self).__add__(other) # pylint: disable=invalid-unary-operand-type

    def __mul__(self, other):
        super_MUL = super(MathArray, self).__mul__
        if isinstance(other, Number):
            return super_MUL(other)

        elif isinstance(other, MathArray):
            if is_numberlike_array(self):
                return self.item() * (other)
            elif is_numberlike_array(other):
                return super_MUL(other.item())
            elif self.ndim > 2 or other.ndim > 2:
                raise MathArrayError("Multiplication of tensor arrays is not currently supported.")
            try:
                # can't mutate self during the multiplication
                result = np.dot(self, other)
                # If A has shape (1, n) and B has shape (n, 1), return a
                # number instead of a (1, 1) array
                if isinstance(result, MathArray) and is_numberlike_array(result):
                    return result.item()
                else:
                    return result

            except ValueError:
                # vector-specific message mentions dot product
                if self.ndim == 1 and other.ndim == 1:
                    msg = ("Cannot calculate the dot product of a {self.description} "
                           "with a {other.description}".format(self=self, other=other))
                    raise ShapeError(msg)
                # general message:
                msg = ("Cannot multiply a {self.description} with a {other.description}.").format(
                    self=self, other=other)
                raise ShapeError(msg)

        raise TypeError("Cannot multiply a {self.shape_name} with object of {type}."
                        .format(type=type(other), self=self))

    def __rmul__(self, other):
        if isinstance(other, Number):
            return super(MathArray, self).__rmul__(other)

        raise TypeError("Cannot multiply object of type {type} with a {self.shape_name}."
                        .format(type=type(other), self=self))


    def __truediv__(self, other):
        super_DIV = super(MathArray, self).__truediv__
        if isinstance(other, Number):
            return super_DIV(other)
        elif isinstance(other, MathArray):
            if is_numberlike_array(other):
                return super_DIV(other.item())
            else:
                raise ShapeError('Cannot divide a {self.shape_name} by a {other.shape_name}'
                                     .format(self=self, other=other))

        raise TypeError("Cannot divide {self.shape_name} by object of {type}.".format(
            type=type(other), self=self))

    def __rtruediv__(self, other):
        if self.ndim > 0:
            raise ShapeError("Cannot divide by a {self.shape_name}".format(self=self))
        return super(MathArray, self).__rtruediv__(other)

    def __pow__(self, other):
        """
        Matrix powers for MathArrays of dimension 0 and 2.
        """
        if is_numberlike_array(self):
            if isinstance(other, Number):
                return robust_pow(self.item(), other)
            elif isinstance(other, MathArray):
                return other.__rpow__(self.item())
            else:
                raise TypeError("Cannot raise a scalar to a {type} power".format(type=type(other)))

        elif not self.ndim == 2:
            raise ShapeError("Cannot raise a {self.shape_name} to powers.".format(
                self=self))

        elif not is_square(self):
            raise ShapeError("Cannot raise a non-square matrix to powers.")

        # Henceforth, self is a square matrix.
        if isinstance(other, Number):
            exponent = other
        elif isinstance(other, MathArray):
            if is_numberlike_array(other):
                exponent = other.item()
            else:
                raise ShapeError("Cannot raise a matrix to {other.shape_name} powers.".format(
                    other=other))
        else:
            raise TypeError("Cannot raise matrix to power of type {type}.".format(
                type=type(other)))

        # Henceforth:
        # - self is a square matrix, AND
        # - exponent is a number
        integer_like = (isinstance(exponent, int) or
                        isinstance(exponent, float) and exponent.is_integer())
        if not integer_like:
            raise MathArrayError("Cannot raise a matrix to non-integer powers.")
        elif exponent < 0 and not MathArray._negative_powers:
            raise MathArrayError('Negative matrix powers have been disabled.')
        else:
            # just in case it had been an integer-like float
            exponent = int(exponent)
            return np.linalg.matrix_power(self, exponent)

    _default_negative_powers = True
    _negative_powers = True
    @classmethod
    @contextmanager
    def enable_negative_powers(cls, value):
        """
        A context-manager manager that can be used to temporarily disable
        negative matrix powers.

        Usage
        =====

        By default, negative integer matrix powers are interpreted as inverses.
        Use MathArray.enable_negative_powers(False) to temporarily throw errors
        instead:
        >>> A = MathArray([[2, 1], [-1, 3]])
        >>> with MathArray.enable_negative_powers(False):
        ...     try:
        ...         A**-1
        ...     except MathArrayError as err:
        ...         print(err.message)
        Negative matrix powers have been disabled.

        It's only temporary!
        >>> approx_equal_as_arrays(
        ...     A * A**-1,
        ...     MathArray([[1, 0], [0, 1]])
        ... )
        True
        """
        # setup
        cls._negative_powers = value
        try:
            # try with block
            yield
        finally:
            # teardown
            cls._negative_powers = cls._default_negative_powers

    def __rpow__(self, other):
        if is_numberlike_array(self) and isinstance(other, Number):
            return robust_pow(other, self.item())

        if isinstance(other, Number):
            raise ShapeError("Cannot raise a scalar to power of a {self.shape_name}."
                                 .format(self=self))
        raise TypeError("Cannot raise {type} to power of {self.shape_name}."
                        .format(type=type(other), self=self))

    # in-place operations

    def __iadd__(self, other):
        return self.__add__(other)

    def __isub__(self, other):
        return self.__sub__(other)

    def __imul__(self, other):
        return self.__mul__(other)

    def __itruediv__(self, other):
        return self.__truediv__(other)

    def __ipow__(self, other):
        return self.__pow__(other)


def equal_as_arrays(A, B):
    """
    Test that A and B are both MathArrays and have equal entries.

    >>> equal_as_arrays(MathArray([1, 2, 3]), MathArray([1, 2, 3]))
    True
    >>> equal_as_arrays(MathArray([1, 2, 3]), np.array([1, 2, 3]))
    False
    >>> equal_as_arrays(MathArray([0, 0, 0]), MathArray(0))
    False
    """
    math_arrays = isinstance(A, MathArray) and isinstance(B, MathArray)
    values_equal = np.array_equal(A, B)
    return math_arrays and values_equal

def approx_equal_as_arrays(A, B, tol=1e-12):
    math_arrays = isinstance(A, MathArray) and isinstance(B, MathArray)
    diff_norm = np.linalg.norm(A - B)
    return math_arrays and (diff_norm < tol)

def random_math_array(shape):
    a, b = -10, 10
    elements = a + (b-a)*np.random.random_sample(shape)
    return MathArray(elements)

def identity(n):
    """
    Returns the n by n MathArray identity matrix.

    Usage:

    >>> identity(2)
    MathArray([[ 1.,  0.],
           [ 0.,  1.]])
    >>> identity(3)
    MathArray([[ 1.,  0.,  0.],
           [ 0.,  1.,  0.],
           [ 0.,  0.,  1.]])
    """

    return MathArray(np.identity(n))
