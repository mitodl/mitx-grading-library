"""
mitmath module

Exports frequently used objects for convenience
"""
from mitxgraders.helpers.mitmath.calc import evaluator
from mitxgraders.helpers.mitmath.mathfuncs import (
    DEFAULT_VARIABLES,
    DEFAULT_FUNCTIONS,
    DEFAULT_SUFFIXES,
    METRIC_SUFFIXES,
    pauli,
    within_tolerance
)
from mitxgraders.helpers.mitmath.math_array import MathArray, IdentityMultiple
from mitxgraders.helpers.mitmath.specify_domain import specify_domain
from mitxgraders.helpers.mitmath.exceptions import CalcError
