"""
exceptions.py

Contains generic grader-related exceptions
"""

class ConfigError(Exception):
    """Raised whenever a configuration error occurs"""
    pass

class StudentFacingError(Exception):
    """Base class for errors whose messages are intended for students to view."""
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
