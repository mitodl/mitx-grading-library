"""
exceptions.py

Contains generic grader-related exceptions
"""

class MITxError(Exception):
    """Base class for all exceptions in mitxgraders"""
    pass

class ConfigError(MITxError):
    """
    Raised whenever a configuration error occurs; author-facing, not intended
    for students.
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

class MissingInput(StudentFacingError):
    """
    Raised when a required input has been left blank.
    """
    pass
