from __future__ import print_function, division, absolute_import, unicode_literals

from mitxgraders.exceptions import StudentFacingError

class CalcError(StudentFacingError):
    """Base class for errors originating in calc module"""

class UndefinedVariable(CalcError):
    """
    Indicate when a student inputs a variable which was not expected.
    """

class UndefinedFunction(CalcError):
    """
    Indicate when a student inputs a function which was not expected.
    """

class UnbalancedBrackets(CalcError):
    """
    Indicate when a student's input has unbalanced brackets.
    """

class CalcZeroDivisionError(CalcError):
    """
    Indicates division by zero
    """

class CalcOverflowError(CalcError):
    """
    Indicates numerical overflow
    """

class FunctionEvalError(CalcError):
    """
    Indicates that something has gone wrong during function evaluation.
    """

class UnableToParse(CalcError):
    """
    Indicate when an expression cannot be parsed
    """

class DomainError(CalcError):
    """
    Raised when a function has domain error.
    """

class ArgumentError(DomainError):
    """
    Raised when the wrong number of arguments is passed to a function
    """

class ArgumentShapeError(DomainError):
    """
    Raised when the wrong type of argument is passed to a function
    """

class MathArrayError(CalcError):
    """
    Thrown by MathArray when anticipated errors are made.
    """

class MathArrayShapeError(MathArrayError):
    """Raised when a MathArray operation cannot be performed because of shape
    mismatch."""
