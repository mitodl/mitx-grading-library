import numpy as np

# TODO: document comparer structure here. Might be written in FormulaGrader already.

def eigenvector_comparer(comparer_params, student_input, utils):
    """
    A comparer function for MatrixGrader.

    Example Usage:
    >>> from mitxgraders import MatrixGrader
    >>> grader = MatrixGrader(
    ...     answers={
    ...         'comparer_params': [
    ...             '[[1, x], [x, -1]]',
    ...             'sqrt(1+x^2)'
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

    matrix, eigenvalue = comparer_params

    # matrix is square with shape (n, n); student input should have shape (n, )
    expected_input_shape = (matrix.shape[0], )
    utils.validate_shape(student_input, expected_input_shape)

    expected = eigenvalue * student_input
    actual = matrix * student_input

    if utils.within_tolerance(0, np.linalg.norm(student_input)):
        return {
            'ok': False,
            'grade_decimal': 0,
            'msg': 'Eigenvectors must be nonzero.'
        }

    return utils.within_tolerance(actual, expected)
