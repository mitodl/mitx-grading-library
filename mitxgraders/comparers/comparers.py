"""
Defines comparer functions used by FormulaGrader and its subclasses.

Comparer Functions
==================

A comparer function must have signature
`comparer_func(comparer_params_evals, student_eval, utils)`.
When `FormulaGrader` (or its subclasses) call your custom comparer function,
`comparer_func`'s argument values are:

- `comparer_params_evals`: The `comparer_params` list, numerically evaluated
  according to variable and function sampling.
- `student_eval`: The student's input, numerically evaluated according to
  variable and function sampling.
- `utils`: A convenience object that may be helpful when writing custom
  comparer functions. It has attributes:

    - `utils.tolerance`: The tolerance specified in grader configuration,
      `0.01%` by default
    - `utils.within_tolerance(x, y)`: checks that `y` is within specified
      tolerance of `x`. Can handle scalars, vectors, and matrices.
      If tolerance was specified as a percentage, then checks that
      `|x-y| < tolerance * x`.

    Comparer functions used inside `MatrixGrader` have the following additional
    `utils` method:

    - `utils.validate_shape(student_eval, shape)`: Checks that `student_eval`
      has specified `shape`, where `shape` is a Numpy shape tuple.

A comparer function must return either:

  - a boolean, or
  - a dictionary with keys:
      - `'grade_decimal'`: number between 0 and 1 (required)
      - `'ok'`: `True` or `False` or `'partial'` (optional, inferred from
        grade_decimal by default)
      - `'msg'`: a feedback message (optional, defaults to `''`)


NOTE: doctests in this module show how the comparer function would be used
      inside a grader
"""
from numbers import Number
import numpy as np
from mitxgraders.exceptions import InputTypeError

def equality_comparer(comparer_params_evals, student_eval, utils):
    """
    Default comparer function used by FormulaGrader, NumericalGrader,
    and MatrixGrader. Checks for equality.

    comparer_params: ['expected_input']
    """
    expected_input = comparer_params_evals[0]

    if hasattr(utils, 'validate_shape'):
        # in numpy, scalars have empty tuples as their shapes
        shape = tuple() if isinstance(expected_input, Number) else expected_input.shape
        utils.validate_shape(student_eval, shape)

    return utils.within_tolerance(expected_input, student_eval)

def between_comparer(comparer_params_evals, student_eval, utils):
    """
    Used to check that input is real and between two parameters.

    comparer_params: ['start', 'stop']

    Example:
    >>> from mitxgraders import NumericalGrader
    >>> grader = NumericalGrader(
    ...     answers={
    ...         'comparer': between_comparer,
    ...         'comparer_params': ['1e6', '1e9']
    ...     }
    ... )
    >>> grader(None, '2.5e8')['ok']
    True
    >>> grader(None, '0.001e8')['ok']
    False
    >>> grader(None, '5e7')['ok']
    True

    Input must be real:
    >>> grader(None, '5e8+2e6*i')['ok']
    Traceback (most recent call last):
    InputTypeError: Input must be real.
    """
    start, stop = comparer_params_evals

    if not np.isreal(student_eval):
        raise InputTypeError("Input must be real.")

    return start <= student_eval <= stop

def congruence_comparer(comparer_params_evals, student_eval, utils):
    """
    Compares the student input to a target, moduli a given modulus.
    Will often set modulus to 2*pi in order to compare angles.

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
    Used to check that a student's answer is an eigenvector of a matrix
    with a given eigenvalue. Ignores scaling of the eigenvector.

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
