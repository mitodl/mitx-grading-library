"""
exceptions.py

Contains exceptions that are used in more than one module.
"""

class ConfigError(Exception):
    """Raised whenever a configuration error occurs"""
    pass

class InvalidInput(Exception):
    """Raised whenever user input is invalid"""
    pass

class StudentFacingError(Exception):
    """Base class for errors whose messages are intended for students to view."""
    pass

class MissingInput(StudentFacingError):
    """
    Raised when a required input has been left blank.
    """
