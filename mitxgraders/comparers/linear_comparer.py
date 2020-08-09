from __future__ import print_function, division, absolute_import, unicode_literals
from numbers import Number
import numpy as np
from voluptuous import Schema, Required, Any, Range
from mitxgraders.comparers.baseclasses import CorrelatedComparer
from mitxgraders.helpers.calc.mathfuncs import is_nearly_zero
from mitxgraders.helpers.validatorfuncs import text_string
from mitxgraders.exceptions import ConfigError

def get_linear_fit_error(x, y):
    """
    Get total error in a linear regression y = ax + b between samples x and y.
    
    If x is constant, returns the result of get_offset_fit_error(x, y).

    Arguments:
        x, y: flat numpy array

    Usage
    =====
    Zero error in a linear relationship:
    >>> x = np.array([2, 5, 8])
    >>> result = get_linear_fit_error(x, 2*x + 1)
    >>> round(result, 6)
    0.0

    If x is constant and y is constant, they are considered linearly related
    >>> x = np.array([1, 1, 1])
    >>> result = get_linear_fit_error(x, 2*x + 1)
    >>> round(result, 6)
    0.0

    If x is constant but y is not, the error associated with the best fit of a constant is computed
    >>> x = np.array([1, 1, 1])
    >>> y = np.array([0, 1, 2])
    >>> result = get_linear_fit_error(x, y)
    >>> round(result, 6) == np.sqrt(2)
    True
    """
    A = np.vstack([x, np.ones(len(x))]).T
    coeffs, residuals, rank, singular_vals = np.linalg.lstsq(A, y, rcond=-1)
    if rank == 1:
        # The input values x are constant. Return the linear offset error.
        return get_offset_fit_error(x, y)
    return np.sqrt(residuals.item())

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
    >>> result                                 # doctest: +ELLIPSIS
    0.76200...

    Zero error in a proportional relationship:
    >>> result = get_proportional_fit_error(x, 2*x)
    >>> round(result, 6)
    0.0

    If x is constant and y is constant, they are considered proportional
    >>> x = np.array([1, 1, 1])
    >>> result = get_proportional_fit_error(x, 2*x)
    >>> round(result, 6)
    0.0

    If x is constant but y is not, the error associated with the best fit of a constant is computed
    >>> x = np.array([1, 1, 1])
    >>> y = np.array([0, 1, 2])
    >>> result = get_proportional_fit_error(x, y)
    >>> round(result, 6) == np.sqrt(2)
    True
    """
    A = np.vstack(x)
    coeffs, residuals, rank, singular_vals = np.linalg.lstsq(A, y, rcond=-1)
    return np.sqrt(residuals.item())

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
    >>> result                                              # doctest: +ELLIPSIS
    4.242640...

    Zero error in a constant-offset relationship:
    >>> result = get_offset_fit_error(x, x + 5)
    >>> round(result, 6)
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
    return np.sqrt(sum(np.square(x - y)))

class LinearComparer(CorrelatedComparer):
    """
    Used to check that there is an linear relationship between student's input
    and the expected answer.

    The general linear relationship is expected = a * student + b. The comparer
    can check for four subtypes:
        equals: (a, b) = (1, 0)
        proportional: b = 0
        offset: a = 1
        linear: neither a nor b fixed

    Configuration
    =============
    The first four configuration keys determine the amount of partial credit
    given for a specific type of linear relationship. If set to None, the
    relationship is not checked.
        equals (None | number): defaults to 1.0
        proportional (None | number): defaults to 0.5
        offset (None | number): defaults to None
        linear (None | number): defaults to None

    The remaining configuration keys specify a feedback message to be given
    in each case:
        equals_msg (str): defaults to ''
        proportional_msg (str): defaults to 'The submitted answer differs from
            an expected answer by a constant factor.'
        offset_msg (str): defaults to ''
        linear_msg (str): defaults to ''

    NOTE:
        LinearComparer can be used with MatrixGrader, but the linear
        relationship must be the same for all entries. Essentially, this means
        we test for
            expected_array = sclar_a * expected_array + scalar_b * ONES
        where ONES is a matrix of all ones.
        The ONES offset works as expected for vectors, but is probably not what
        you want for matrices.

    """

    schema_config = Schema({
        Required('equals', default=1.0): Any(None, Range(0, 1)),
        Required('proportional', default=0.5): Any(None, Range(0, 1)),
        Required('offset', default=None): Any(None, Range(0, 1)),
        Required('linear', default=None): Any(None, Range(0, 1)),
        Required('equals_msg', default=''): text_string,
        Required('proportional_msg', default=(
            'The submitted answer differs from an expected answer by a '
            'constant factor.'
        )): text_string,
        Required('offset_msg', default=''): text_string,
        Required('linear_msg', default=''): text_string,
    })

    all_modes = ('equals', 'proportional', 'offset', 'linear')
    zero_compatible_modes = ('equals', 'offset')

    def __init__(self, config=None, **kwargs):
        super(LinearComparer, self).__init__(config, **kwargs)
        self.modes = tuple(mode for mode in self.all_modes if self.config[mode] is not None)

    error_calculators = {
        'equals': get_equals_fit_error,
        'proportional': get_proportional_fit_error,
        'offset': get_offset_fit_error,
        'linear': get_linear_fit_error,
    }

    @staticmethod
    def check_comparing_zero(comparer_params_evals, student_evals, tolerance):
        """
        Check whether student input is nearly zero, or author input is exactly zero
        """
        student_zero = all([
            is_nearly_zero(x, tolerance, reference=y)
            for x, y in zip(student_evals, comparer_params_evals)
        ])
        expected_zero = all(np.all(x == 0.0) for [x] in comparer_params_evals)
        return student_zero or expected_zero

    def get_valid_modes(self, is_comparing_zero):
        """
        Returns a copy of self.modes, first removing 'proportional' and 'linear'
        when is_comparing_zero is truthy.
        """
        if is_comparing_zero:
            return tuple(mode for mode in self.modes
                         if mode in self.zero_compatible_modes)
        return self.modes

    def __call__(self, comparer_params_evals, student_evals, utils):
        student_evals_norm = np.linalg.norm(student_evals)

        # Validate student input shape...only needed for MatrixGrader
        if hasattr(utils, 'validate_shape'):
            # in numpy, scalars have empty tuples as their shapes
            expected_0 = comparer_params_evals[0][0]
            scalar_expected = isinstance(expected_0, Number)
            shape = tuple() if scalar_expected else expected_0.shape
            utils.validate_shape(student_evals[0], shape)

        # Raise an error if there is less than 3 samples
        if len(student_evals) < 3:
            msg = 'Cannot perform linear comparison with less than 3 samples'
            raise ConfigError(msg)

        is_comparing_zero = self.check_comparing_zero(comparer_params_evals,
                                                      student_evals, utils.tolerance)
        filtered_modes = self.get_valid_modes(is_comparing_zero)

        # Get the result for each mode
        # flatten in case individual evals are arrays (as in MatrixGrader)
        student = np.array(student_evals).flatten()
        expected = np.array(comparer_params_evals).flatten()
        errors = [self.error_calculators[mode](student, expected) for mode in filtered_modes]

        results = [
            {'grade_decimal': self.config[mode], 'msg': self.config[mode+'_msg']}
            if is_nearly_zero(error, utils.tolerance, reference=student_evals_norm)
            else
            {'grade_decimal': 0, 'msg': ''}
            for mode, error in zip(filtered_modes, errors)
        ]

        # Get the best result using max.
        # For a list of pairs, max compares by 1st index and uses 2nd to break ties
        key = lambda result: (result['grade_decimal'], result['msg'])
        return max(results, key=key)
