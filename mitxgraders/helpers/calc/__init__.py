"""
calc module

Exports frequently used objects for convenience
"""
from __future__ import print_function, division, absolute_import

from mitxgraders.helpers.calc.expressions import evaluator, parse
from mitxgraders.helpers.calc.mathfuncs import (
    DEFAULT_VARIABLES,
    DEFAULT_FUNCTIONS,
    DEFAULT_SUFFIXES,
    METRIC_SUFFIXES,
    pauli,
    cartesian_xyz,
    cartesian_ijk,
    within_tolerance
)
from mitxgraders.helpers.calc.math_array import MathArray, identity
from mitxgraders.helpers.calc.specify_domain import specify_domain
from mitxgraders.helpers.calc.exceptions import CalcError

__all__ = [
    "parse",
    "evaluator",
    "DEFAULT_VARIABLES",
    "DEFAULT_FUNCTIONS",
    "DEFAULT_SUFFIXES",
    "METRIC_SUFFIXES",
    "pauli",
    "cartesian_xyz",
    "cartesian_ijk",
    "within_tolerance",
    "MathArray",
    "identity",
    "specify_domain",
    "CalcError"
]
