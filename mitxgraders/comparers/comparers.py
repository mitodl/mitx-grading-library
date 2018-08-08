"""
Defines comparer functions used by FormulaGrader and its subclasses.
"""
from numbers import Number
import numpy as np

def equality_comparer(comparer_params_evals, student_eval, utils):
    """
    Default comparer function used by FormulaGrader, NumericalGrader,
    and MatrixGrader.

    comparer_params: ['expected_input']
    """
    expected_input = comparer_params_evals[0]

    if hasattr(utils, 'validate_shape'):
        # in numpy, scalars have empty tuples as their shapes
        shape = tuple() if isinstance(expected_input, Number) else expected_input.shape
        utils.validate_shape(student_eval, shape)

    return utils.within_tolerance(expected_input, student_eval)

def within_range_comparer(comparer_params_evals, student_eval, utils):
    """
    comparer_params: ['start', 'stop']

    Example:
    >>> from mitxgraders import NumericalGrader
    >>> grader = NumericalGrader(
    ...     answers={
    ...         'comparer': within_range_comparer,
    ...         'comparer_params': ['1e6', '1e9']
    ...     }
    ... )
    >>> grader(None, '2.5e8')['ok']
    True
    >>> grader(None, '0.001e8')['ok']
    False
    >>> grader(None, '5e7')['ok']
    True
    """
    start, stop = comparer_params_evals

    return start <= student_eval <= stop

def congruence_comparer(comparer_params_evals, student_eval, utils):
    """
    comparer_params: [target, modulus]

    Example usage:
    >>> from mitxgraders import FormulaGrader
    >>> grader = FormulaGrader(
    ...     answers={
    ...         'comparer': congruence_comparer,
    ...         'comparer_params': [
    ...             'b^2/a', # target
    ...             'c'      # modulus
    ...         ]
    ...     },
    ...     variables=['a', 'b', 'c']
    ... )
    >>> grader(None, 'b^2/a')['ok']
    True
    >>> grader(None, 'b^2/a + 1.5*c')['ok']
    False
    >>> grader(None, 'b^2/a + 2*c  ')['ok']
    True
    """
    expected, modulus = comparer_params_evals

    expected_reduced = expected % modulus
    input_reduced = student_eval % modulus
    return utils.within_tolerance(expected_reduced, input_reduced)

def eigenvector_comparer(comparer_params_evals, student_eval, utils):
    """
    comparer_params: [matrix, eigenvalue]

    Example Usage:
    >>> from mitxgraders import MatrixGrader
    >>> grader = MatrixGrader(
    ...     answers={
    ...         'comparer_params': [
    ...             '[[1, x], [x, -1]]',    # matrix
    ...             'sqrt(1+x^2)'           # eigenvalue
    ...         ],
    ...         'comparer': eigenvector_comparer
    ...     },
    ...     variables=['x']
    ... )
    >>> grader(None, '[1+sqrt(1+x^2), x]')['ok']
    True
    >>> grader(None, '2*[1+sqrt(1+x^2), x]')['ok']
    True
    >>> grader(None, '[1+sqrt(1+x^2), 1]')['ok']
    False
    >>> grader(None, '[0, 0]') == {
    ...     'ok': False,
    ...     'msg': 'Eigenvectors must be nonzero.',
    ...     'grade_decimal': 0
    ... }
    True

    """

    matrix, eigenvalue = comparer_params_evals

    # matrix is square with shape (n, n); student input should have shape (n, )
    expected_input_shape = (matrix.shape[0], )
    utils.validate_shape(student_eval, expected_input_shape)

    expected = eigenvalue * student_eval
    actual = matrix * student_eval

    if utils.within_tolerance(0, np.linalg.norm(student_eval)):
        return {
            'ok': False,
            'grade_decimal': 0,
            'msg': 'Eigenvectors must be nonzero.'
        }

    return utils.within_tolerance(actual, expected)
