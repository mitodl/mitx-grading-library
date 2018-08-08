"""
exceptions.py
Contains generic grader-related exceptions
"""

class MITxError(Exception):
    """
    Base class for all exceptions in mitxgraders, has a privileged role
    in grading.

    if an MITxError is raised when a grader tries to check a student's input,
    its message will be displayed directly to the student. If any other error
    occurs, it will be caught and a a generic error message is shown.

    (Except when debug=True, in which case all errors are simply
    re-raised.)
    """
    pass

class ConfigError(MITxError):
    """
    Raised whenever a configuration error occurs. This is intended for
    author-facing messages.
    """
    pass

class StudentFacingError(MITxError):
    """
    Base class for errors whose messages are intended for students to view.
    """
    pass

class InvalidInput(StudentFacingError):
    """
    Raised when an input has failed some validation.

    Usually we use this when the input can be graded, but is invalid in some
    other sense. For example, an input contains a forbidden string or function.
    """
    pass

class InputTypeError(InvalidInput):
    """
    Indicates that student's input has evaluated to an object of the wrong
    type (or shape).
    """

class MissingInput(StudentFacingError):
    """
    Raised when a required input has been left blank.
    """
    pass
