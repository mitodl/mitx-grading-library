"""
Defines comparer functions used by FormulaGrader and its subclasses.

Comparer Functions
==================

A comparer function must have signature
`comparer_func(comparer_params_evals, student_eval, utils)` and should return
True, False, 'partial', or a dictionary with required key 'grade_decimal' and
optional key 'msg'. When `FormulaGrader` (or its subclasses) call your custom
comparer function, `comparer_func`'s argument values are:

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
from mitxgraders.exceptions import InputTypeError, StudentFacingError
from mitxgraders.helpers.calc.mathfuncs import is_nearly_zero
from mitxgraders.helpers.calc.math_array import are_same_length_vectors, is_vector

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

def vector_span_comparer(comparer_params_evals, student_eval, utils):
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
    >>> result['ok']
    False
    >>> result['msg']
    'Input should be a nonzero vector.'

    Input shape is validated:
    >>> grader(None, '5')
    Traceback (most recent call last):
    InputTypeError: Expected answer to be a vector, but input is a scalar

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
    >>> grader(None, '[1, 2, 3]')               # doctest: +ELLIPSIS
    Traceback (most recent call last):
    StudentFacingError: Problem Configuration Error: ...to equal-length vectors
    """

    # Validate the comparer params
    if not are_same_length_vectors(comparer_params_evals):
        raise StudentFacingError('Problem Configuration Error: comparer_params '
            'should be a list of strings that evaluate to equal-length vectors')

    # Validate student input shape
    utils.validate_shape(student_eval, comparer_params_evals[0].shape)

    if utils.within_tolerance(0, np.linalg.norm(student_eval)):
        return {
            'ok': False,
            'grade_decimal': 0,
            'msg': 'Input should be a nonzero vector.'
        }

    # Use ordinary least squares to find an approximation to student_eval
    # that lies within the span of given vectors, then check that the
    # residual-sum is small in comparison to student input.
    column_vectors = np.array(comparer_params_evals).transpose()
    # rcond=-1 uses machine precision for testing singular values
    # In numpy 1.14+, use rcond=None fo this behavior. (we use 1.6)
    ols = np.linalg.lstsq(column_vectors, student_eval, rcond=-1)
    error = np.sqrt(ols[1])

    # Check that error is nearly zero, using student_eval as a reference
    # when tolerance is specified as a percentage
    return is_nearly_zero(error, utils.tolerance, reference=student_eval)

def vector_phase_comparer(comparer_params_evals, student_eval, utils):
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
    >>> grader(None, '[1, 2, 3]')               # doctest: +ELLIPSIS
    Traceback (most recent call last):
    StudentFacingError: Problem Configuration Error: ...to a single vector.
    """
    # Validate that author comparer_params evaluate to a single vector
    if not len(comparer_params_evals) == 1 and is_vector(comparer_params_evals[0]):
        raise StudentFacingError('Problem Configuration Error: comparer_params '
            'should be a list of strings that evaluate to a single vector.')

    # We'll check that student input is in the span as target vector and that
    # it has the same magnitude

    in_span = vector_span_comparer(comparer_params_evals, student_eval, utils)

    expected_mag = np.linalg.norm(comparer_params_evals[0])
    student_mag = np.linalg.norm(student_eval)
    same_magnitude = utils.within_tolerance(expected_mag, student_mag)

    return in_span and same_magnitude

class CorrelatedComparer(object):
    """
    CorrelatedComparer instances are callable objects used as comparer functions
    in FormulaGrader problems. Unlike standard comparer functions, CorrelatedComparer
    instances are given access to all parameter evaluations at once.

    For example, a comparer function that decides whether the student input is a
    nonzero constant multiple of the expected input would need to be a correlated
    comparer so that it can determine if there is a linear relationship between
    the student and expected samples.
    """

    def __init__(self, func):
        self._comparer = func

    def __call__(self, comparer_params_evals, student_evals, utils):
        return self._comparer(comparer_params_evals, student_evals, utils)

def make_constant_multiple_comparer(grade_decimal=0.5, msg='The submitted answer differs from the expected answer by a constant multiple'):
    """
    Makes a comparer function that tests whether student input is a constant multiple
    of expected input, and if so, gives partial credit and displays a message.

    Usage
    =====

    >>> from mitxgraders import FormulaGrader
    >>> grader = FormulaGrader(
    ...     answers={
    ...         'comparer_params': ['m*c^2'],
    ...         'comparer': make_constant_multiple_comparer(grade_decimal=0.75)
    ...     },
    ...     variables=['m', 'c']
    ... )
    >>> result = grader(None, '2*m*c^2')
    >>> result == {
    ...     'ok': 'partial',
    ...     'msg': 'The submitted answer differs from the expected answer by a constant multiple',
    ...     'grade_decimal': 0.75
    ... }
    True


    Gives full credit / no credit appropriately:
    >>> grader(None, 'm*c^3')['ok']
    False
    >>> grader(None, 'm*c^2')['ok']
    True

    Zero input is always marked wrong:
    >>> grader(None, '0')['ok']
    False
    """


    @CorrelatedComparer
    def _comparer(comparer_params_evals, student_evals, utils):
        student_eval_norm = np.linalg.norm(student_evals)/len(student_evals)

        # Validate student input shape...only needed for MatrixGrader
        try:
            utils.validate_shape(student_evals[0], comparer_params_evals[0][0].shape)
        except AttributeError:
            pass # not called by MatrixGrader

        if is_nearly_zero(student_eval_norm, utils.tolerance, reference=student_evals):
            return False

        A = np.vstack(np.array(student_evals).flatten())
        y = np.array(comparer_params_evals).flatten()

        sol, residuals, _, _ = np.linalg.lstsq(A, y, rcond=-1)
        coeff = sol[0]
        error = np.sqrt(residuals)

        if is_nearly_zero(error, utils.tolerance, reference=student_eval_norm):
            if is_nearly_zero(coeff - 1, utils.tolerance, reference=student_eval_norm):
                return True
            return { 'grade_decimal': grade_decimal, 'msg': msg }

        return False

    return _comparer

constant_multiple_comparer = make_constant_multiple_comparer()
