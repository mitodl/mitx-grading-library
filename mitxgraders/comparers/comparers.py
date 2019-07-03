"""
Defines comparer functions used by FormulaGrader and its subclasses.

Simple Comparer Functions
=========================

A comparer function must have signature
`comparer_func(comparer_params_eval, student_eval, utils)` and should return
True, False, 'partial', or a dictionary with required key 'grade_decimal' and
optional key 'msg'. When `FormulaGrader` (or its subclasses) call your custom
comparer function, `comparer_func`'s argument values are:

- `comparer_params_eval`: The `comparer_params` list, numerically evaluated
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

Correlated Comparers
====================
See ./baseclasses.py and ./linear_comparer.py for examples.
"""
from __future__ import print_function, division, absolute_import, unicode_literals

from numbers import Number
import numpy as np

from voluptuous import Schema, Required

from mitxgraders.exceptions import InputTypeError, StudentFacingError
from mitxgraders.helpers.validatorfuncs import is_callable, Nullable
from mitxgraders.helpers.calc.mathfuncs import is_nearly_zero
from mitxgraders.helpers.calc.math_array import are_same_length_vectors, is_vector
from mitxgraders.comparers.baseclasses import Comparer

class EqualityComparer(Comparer):
    """
    This comparer checks for equality between the student and instructor results,
    up to a desired tolerance. If desired, a transforming function can be applied
    before the comparison is carried out.

    comparer_params: ['expect']

    By default, equality_comparer is used in FormulaGrader, NumericalGrader and MatrixGrader.
    >>> from mitxgraders import *
    >>> equality_comparer == EqualityComparer()
    True
    >>> grader = FormulaGrader(
    ...     answers='2*x',
    ...     variables=['x']
    ... )
    >>> grader(None, 'x')['ok']
    False
    >>> grader(None, 'x*2')['ok']
    True

    The following example applies cosine to the expected answer and student input
    before comparison:
    >>> import numpy as np
    >>> grader = FormulaGrader(
    ...     answers={
    ...         'comparer': EqualityComparer(transform=np.cos),
    ...         'comparer_params': ['x']
    ...     },
    ...     variables=['x']
    ... )
    >>> grader(None, 'x')['ok']
    True
    >>> grader(None, '-x')['ok']
    True
    >>> grader(None, 'x + 2*pi')['ok']
    True
    >>> grader(None, 'x + pi')['ok']
    False

    The following example takes the norm of the expected answer and student input
    before comparison. Note the different method of changing the comparer.
    >>> FormulaGrader.set_default_comparer(EqualityComparer(transform=np.linalg.norm))
    >>> grader = MatrixGrader(
    ...     answers='[1, 0, 0]'
    ... )
    >>> grader(None, '[1, 0, 0]')['ok']
    True
    >>> grader(None, '[0, 1, 0]')['ok']
    True
    >>> grader(None, '[1/sqrt(2), 0, 1/sqrt(2)]')['ok']
    True
    >>> FormulaGrader.reset_default_comparer()

    """
    schema_config = Schema({
        Required('transform', default=None): Nullable(is_callable)
    })

    def __call__(self, comparer_params_eval, student_eval, utils):
        expected_input = comparer_params_eval[0]

        if hasattr(utils, 'validate_shape'):
            # in numpy, scalars have empty tuples as their shapes
            shape = tuple() if isinstance(expected_input, Number) else expected_input.shape
            utils.validate_shape(student_eval, shape)

        # If provided, apply the transform function
        if self.config['transform'] is not None:
            expected_input = self.config['transform'](expected_input)
            student_eval = self.config['transform'](student_eval)

        return utils.within_tolerance(expected_input, student_eval)

equality_comparer = EqualityComparer()

def between_comparer(comparer_params_eval, student_eval, utils):
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
    >>> try:
    ...     grader(None, '5e8+2e6*i')['ok']
    ... except InputTypeError as error:
    ...     print(error)
    Input must be real.
    """
    start, stop = comparer_params_eval

    if not np.isreal(student_eval):
        raise InputTypeError("Input must be real.")

    return start <= student_eval <= stop

def congruence_comparer(comparer_params_eval, student_eval, utils):
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
    expected, modulus = comparer_params_eval

    expected_reduced = expected % modulus
    input_reduced = student_eval % modulus
    return utils.within_tolerance(expected_reduced, input_reduced)

def eigenvector_comparer(comparer_params_eval, student_eval, utils):
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

    matrix, eigenvalue = comparer_params_eval

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

def vector_span_comparer(comparer_params_eval, student_eval, utils):
    """
    Check whether student's answer is nonzero and in the span of some given
    vectors.

    comparer_params: A list of vectors

    Usage
    =====

    Use a single vector as comparer_params to test whether student input is
    parallel to a particular vector:
    >>> from mitxgraders import MatrixGrader
    >>> grader = MatrixGrader(
    ...     answers={
    ...         'comparer_params': [
    ...             '[3, x, 1 + i]',
    ...         ],
    ...         'comparer': vector_span_comparer
    ...     },
    ...     variables=['x'],
    ... )
    >>> grader(None, '[3, x, 1 + i]')['ok']
    True
    >>> grader(None, '[9, 3*x, 3 + 3*i]')['ok']
    True
    >>> grader(None, '[9, 3*x, 3 - 3*i]')['ok']
    False

    Complex scale factors work, too:
    >>> grader(None, '(4 + 2*i)*[3, x, 1 + i]')['ok']
    True

    Student input should be nonzero:
    >>> result = grader(None, '[0, 0, 0]')
    >>> expected = {
    ...     'ok': False,
    ...     'grade_decimal': 0.0,
    ...     'msg': 'Input should be a nonzero vector.'
    ... }
    >>> result == expected
    True

    Input shape is validated:
    >>> try:
    ...     grader(None, '5')
    ... except InputTypeError as error:
    ...     print(error)
    Expected answer to be a vector, but input is a scalar

    Multiple vectors can be provided:
    >>> grader = MatrixGrader(
    ...     answers={
    ...         'comparer_params': [
    ...             '[1, 1, 0]',    # v0
    ...             '[0, 1, 2]'     # v1
    ...         ],
    ...         'comparer': vector_span_comparer
    ...     },
    ... )

    The vector 2*v0 + 3i*v1 = [2, 2+3i, 6i] is in the span of v0 and v1:
    >>> grader(None, '[2, 2 + 3*i, 6*i]')['ok']
    True

    The comparer_params should be list of equal-length vectors:
    >>> grader = MatrixGrader(
    ...     answers={
    ...         'comparer_params': [
    ...             '[1, 1, 0]',
    ...             '5'
    ...         ],
    ...         'comparer': vector_span_comparer
    ...     },
    ... )
    >>> try:
    ...     grader(None, '[1, 2, 3]')               # doctest: +ELLIPSIS
    ... except StudentFacingError as error:
    ...     print(error)
    Problem Configuration Error: ...to equal-length vectors
    """

    # Validate the comparer params
    if not are_same_length_vectors(comparer_params_eval):
        raise StudentFacingError('Problem Configuration Error: comparer_params '
            'should be a list of strings that evaluate to equal-length vectors')

    # Validate student input shape
    utils.validate_shape(student_eval, comparer_params_eval[0].shape)

    if utils.within_tolerance(0, np.linalg.norm(student_eval)):
        return {
            'ok': False,
            'grade_decimal': 0,
            'msg': 'Input should be a nonzero vector.'
        }

    # Use ordinary least squares to find an approximation to student_eval
    # that lies within the span of given vectors, then check that the
    # residual-sum is small in comparison to student input.
    column_vectors = np.array(comparer_params_eval).transpose()
    # rcond=-1 uses machine precision for testing singular values
    # In numpy 1.14+, use rcond=None fo this behavior. (we use 1.6)
    ols = np.linalg.lstsq(column_vectors, student_eval, rcond=-1)
    error = np.sqrt(ols[1])

    # Check that error is nearly zero, using student_eval as a reference
    # when tolerance is specified as a percentage
    return is_nearly_zero(error, utils.tolerance, reference=student_eval)

def vector_phase_comparer(comparer_params_eval, student_eval, utils):
    """
    Check that student input equals a given input (to within tolerance), up to
    an overall phase factor.

    comparer_params: [target_vector]

    Usage
    =====

    >>> from mitxgraders import MatrixGrader
    >>> grader = MatrixGrader(
    ...     answers={
    ...         'comparer_params': [
    ...             '[1, exp(-i*phi)]',
    ...         ],
    ...         'comparer': vector_phase_comparer
    ...     },
    ...     variables=['phi'],
    ... )

    >>> grader(None, '[1, exp(-i*phi)]')['ok']
    True
    >>> grader(None, '[exp(i*phi/2), exp(-i*phi/2)]')['ok']
    True
    >>> grader(None, '[i, exp(i*(pi/2 - phi))]')['ok']
    True

    >>> grader(None, '[1, exp(+i*phi)]')['ok']
    False
    >>> grader(None, '[2, 2*exp(-i*phi)]')['ok']
    False

    The comparer_params should be list with a single vector:
    >>> grader = MatrixGrader(
    ...     answers={
    ...         'comparer_params': [
    ...             '[1, 1, 0]',
    ...             '[0, 1, 1]'
    ...         ],
    ...         'comparer': vector_phase_comparer
    ...     },
    ... )
    >>> try:
    ...     grader(None, '[1, 2, 3]')               # doctest: +ELLIPSIS
    ... except StudentFacingError as error:
    ...     print(error)
    Problem Configuration Error: ...to a single vector.
    """
    # Validate that author comparer_params evaluate to a single vector
    if not len(comparer_params_eval) == 1 and is_vector(comparer_params_eval[0]):
        raise StudentFacingError('Problem Configuration Error: comparer_params '
            'should be a list of strings that evaluate to a single vector.')

    # We'll check that student input is in the span as target vector and that
    # it has the same magnitude

    in_span = vector_span_comparer(comparer_params_eval, student_eval, utils)

    expected_mag = np.linalg.norm(comparer_params_eval[0])
    student_mag = np.linalg.norm(student_eval)
    same_magnitude = utils.within_tolerance(expected_mag, student_mag)

    return in_span and same_magnitude
