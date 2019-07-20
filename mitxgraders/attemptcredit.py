"""
attemptcredit.py

This file contains various routines for assigning attempt-based partial credit.
"""
from __future__ import print_function, division, absolute_import, unicode_literals
from voluptuous import Schema, Required, Any, Range, All
from mitxgraders.baseclasses import ObjectWithSchema
from mitxgraders.helpers.validatorfuncs import Positive

__all__ = ['LinearCredit', 'GeometricCredit', 'ReciprocalCredit']

class LinearCredit(ObjectWithSchema):
    """
    This class assigns credit based on a piecewise linear progression:
    Constant - Linear Decrease - Constant

    Credit
    ^
    |--
    |  \
    |   \
    |    -----
    |
    +---------> Attempt number

    Configuration:
    ==============
        decrease_credit_after (positive int): The last attempt number to award maximum
            credit to (default 1)

        minimum_credit (float between 0 and 1): The minimum amount of credit to be awarded
            after using too many attempts (default 0.2)

        decrease_credit_steps (positive int): How many attempts it takes to get to minimum
            credit. So, if set to 1, after decrease_credit_after attempts, the next attempt
            will receive minimum_credit. If set to 2, the next attempt will be halfway
            between 1 and minimum_credit, and the attempt after that will be awarded
            minimum_credit. (default 4)

    Usage:
    ======

    >>> creditor = LinearCredit(decrease_credit_after=1, minimum_credit=0.2, decrease_credit_steps=4)
    >>> creditor(1)
    1
    >>> creditor(2)
    0.8
    >>> creditor(3)
    0.6
    >>> creditor(4)
    0.4
    >>> creditor(5)
    0.2
    >>> creditor(6)
    0.2

    """
    @property
    def schema_config(self):
        return Schema({
            Required('decrease_credit_after', default=1): Positive(int),
            Required('decrease_credit_steps', default=4): Positive(int),
            Required('minimum_credit', default=0.2): Any(All(float, Range(0, 1)), 0, 1)
        })

    def __call__(self, attempt):
        """
        Return the credit associated with a given attempt number
        """
        if attempt == 1:
            return 1

        # How far past the point of decreasing credit are we?
        steps = attempt - self.config['decrease_credit_after']
        if steps <= 0:
            return 1

        # Compute the credit to be awarded
        min_cred = self.config['minimum_credit']
        decrease_steps = self.config['decrease_credit_steps']
        if steps >= decrease_steps:
            credit = min_cred
        else:
            # Linear interpolation
            credit = 1 + (min_cred - 1) * steps / decrease_steps

        return round(credit, 4)

class GeometricCredit(ObjectWithSchema):
    """
    This class assigns credit based on a geometric progression:
    1, x, x^2, etc.
    x = 3/4 by default.

    Configuration:
    ==============
        factor (float): Number between 0 and 1 inclusive that is the decreasing
            factor for each attempt (default 0.75).

    Usage:
    ======

    >>> creditor = GeometricCredit(factor=0.5)
    >>> creditor(1)
    1
    >>> creditor(2)
    0.5
    >>> creditor(3)
    0.25

    """
    @property
    def schema_config(self):
        return Schema({
            Required('factor', default=0.75): Any(All(float, Range(0, 1)), 0, 1)
        })

    def __call__(self, attempt):
        """
        Return the credit associated with a given attempt number
        """
        if attempt == 1:
            return 1
        credit = self.config['factor'] ** (attempt - 1)
        return round(credit, 4)

class ReciprocalCredit(ObjectWithSchema):
    """
    This class assigns credit based on the reciprocal of attempt number.
    1, 1/2, 1/3, etc.

    Configuration:
    ==============
        None

    Usage:
    ======

    >>> creditor = ReciprocalCredit()
    >>> creditor(1)
    1
    >>> creditor(2)
    0.5
    >>> creditor(3)   # doctest: +ELLIPSIS
    0.333...
    >>> creditor(4)
    0.25

    """
    @property
    def schema_config(self):
        # No configuration for this one!
        return Schema({})

    def __call__(self, attempt):
        """
        Return the credit associated with a given attempt number
        """
        if attempt == 1:
            return 1
        credit = 1.0 / attempt
        return round(credit, 4)
