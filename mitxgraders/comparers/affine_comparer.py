from collections import namedtuple
import numpy as np
from voluptuous import Schema, Required, Any, All, Optional, Range
from mitxgraders.comparers.baseclasses import CorrelatedComparer
from mitxgraders.helpers.calc.mathfuncs import is_nearly_zero

def get_affine_fit_error(x, y):
    """
    Get total error in a linear regression y = ax + b between samples x and y.

    Arguments:
        x, y: flat numpy array

    Usage
    =====
    Zero error in a linear relationship:
    >>> x = np.array([2, 5, 8])
    >>> result = get_affine_fit_error(x, 2*x + 1)
    >>> round(result, 8)
    0.0
    """
    A = np.vstack([x, np.ones(len(x))]).T
    _, residuals, _, _ = np.linalg.lstsq(A, y, rcond=-1)
    return np.sqrt(residuals)

def get_proportional_fit_error(x, y):
    """
    Get total error in a linear regression y = ax between samples x and y, with
    zero constant term.

    Arguments:
        x, y: flat numpy array

    Usage
    =====
    Reveals error if relationship is not proportional:
    >>> x = np.array([2, 5, 8])
    >>> result = get_proportional_fit_error(x, 2*x + 1)
    >>> round(result, 8)
    0.76200076

    Zero error in a proportional relationship:
    >>> result = get_proportional_fit_error(x, 2*x)
    >>> round(result, 8)
    0.0
    """
    A = np.vstack(x)
    _, residuals, _, _ = np.linalg.lstsq(A, y, rcond=-1)
    return np.sqrt(residuals)

def get_offset_fit_error(x, y):
    """
    Get total error in a linear regression y = x + b between samples x and y,
    with slope term equal to 1.

    Arguments:
        x, y: flat numpy array

    Usage
    =====
    Reveals error if relationship is not constant-offset:
    >>> x = np.array([2, 5, 8])
    >>> result = get_offset_fit_error(x, 2*x + 1)
    >>> round(result, 8)
    4.24264069

    Zero error in a constant-offset relationship:
    >>> result = get_offset_fit_error(x, x + 5)
    >>> round(result, 8)
    0.0
    """
    mean = np.mean(y - x)
    return np.sqrt(sum(np.square(x + mean - y)))

def get_equals_fit_error(x, y):
    """
    Get total error in the difference between two samples.
    Arguments:
        x, y: compatible numpy arrays
    """
    return sum(np.abs(x-y))

class AffineComparer(CorrelatedComparer):
    """
    Used to check that there is an affine relationship between student's input
    and the expected answer.

    The general affine relationship is expected = a * student + b. The comparer
    can check for four subtypes:
        equals: (a, b) = (1, 0)
        proportional: b = 0
        offset: a = 1
        affine: neither a nor b fixed

    Configuration
    =============
    The first four configuration keys determine the amount of partial credit
    given for a specific type of affine relationship. If set to None, the
    relationship is not checked.
        equals (None | number): defaults to 1.0
        proportional (None | number): defaults to 0.5
        offset (None | number): defaults to None
        affine (None | number): defaults to None

    The remaining configuration keys specify a feedback message to be given
    in each case:
        equals_msg (str): defaults to ''
        proportional_msg (str): defaults to 'The submitted answer differs from
            an expected answer by a constant factor.'
        offset_msg (str): defaults to ''
        affine_msg (str): defaults to ''
    """

    schema_config = Schema({
        Required('equals', default=1.0): Any(None, Range(0, 1)),
        Required('proportional', default=0.5): Any(None, Range(0, 1)),
        Required('offset', default=None): Any(None, Range(0, 1)),
        Required('affine', default=None): Any(None, Range(0, 1)),
        Required('equals_msg', default=''): str,
        Required('proportional_msg', default=(
            'The submitted answer differs from an expected answer by a '
            'constant factor.'
        )): str,
        Required('offset_msg', default=''): str,
        Required('affine_msg', default=''): str,
    })

    def __init__(self, config=None, **kwargs):
        super(AffineComparer, self).__init__(config, **kwargs)
        all_modes = ('equals', 'proportional', 'offset', 'affine')
        self.modes = tuple(mode for mode in all_modes if self.config[mode] is not None)

    error_calculators = {
        'equals': get_equals_fit_error,
        'proportional': get_proportional_fit_error,
        'offset': get_offset_fit_error,
        'affine': get_affine_fit_error,
    }

    def __call__(self, comparer_params_evals, student_evals, utils):
        student_eval_norm = np.linalg.norm(student_evals)

        # Validate student input shape...only needed for MatrixGrader
        try:
            utils.validate_shape(student_evals[0], comparer_params_evals[0][0].shape)
        except AttributeError:
            pass # not called by MatrixGrader

        if is_nearly_zero(student_eval_norm, utils.tolerance, reference=comparer_params_evals):
            return False

        # Get the result for each mode
        student = np.array(student_evals).flatten()
        expected = np.array(comparer_params_evals).flatten()
        errors = [self.error_calculators[mode](student, expected) for mode in self.modes]
        results = [
            {'grade_decimal': self.config[mode], 'msg': self.config[mode+'_msg']}
            if is_nearly_zero(error, utils.tolerance, reference=student_eval_norm)
            else
            {'grade_decimal': 0, 'msg': ''}
            for mode, error in zip(self.modes, errors)
        ]

        # Get the best result using max.
        # For a list of pairs, max compares by 1st index and uses 2nd to break ties
        key = lambda result: (result['grade_decimal'], result['msg'])
        return max(results, key=key)
