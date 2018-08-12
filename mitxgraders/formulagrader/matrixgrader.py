"""
matrixgrader.py

Defines a FormulaGrader subtype that handles matrices, too.
"""
from numbers import Number
from collections import namedtuple
from voluptuous import Required, Any
from mitxgraders.exceptions import InputTypeError
from mitxgraders.formulagrader.formulagrader import FormulaGrader
from mitxgraders.helpers.validatorfuncs import NonNegative
from mitxgraders.helpers.calc import MathArray, within_tolerance, identity
from mitxgraders.helpers.calc.exceptions import (
    CalcError, MathArrayShapeError as ShapeError)
from mitxgraders.helpers.calc.mathfuncs import (
    merge_dicts, ARRAY_ONLY_FUNCTIONS)

class MatrixGrader(FormulaGrader):
    """
    An extension of FormulaGrader with better support for grading expressions
    with vectors and matrices. Includes an extra default constant ('I', for the
    identity operator) and some extra default functions (trans, det, ...)

    Configuration options as per FormulaGrader, except:
        identity_dim (?int): If specified as an integer n, 'I' is automatically
            added as a variable whose value is the n by n MathArray identity
            matrix. Defaults to None.

        max_array_dim (int): Specify the maximum array dimension that the
            expression parser will accept, defaults to 1 (allows vectors).
            NOTE: Variables can still contain higher dimensional arrays.

        shape_errors (bool): If True (the default), then array shape mismatch
            errors will raise an error rather. If false, shape mismatch will
            result in input being graded incorrect.

        negative_powers (bool): If True (the default), then for a square matrix
            A and positive integer k, A^-k is interpreted as (inverse(A))^k.
            If False, negative powers raise an error instead.

        answer_shape_mismatch (dict): Describes how the default comparer_function
            handles grading when student_input and stored answer have different
            incompatible shapes. (For example, student_input is a vector, but
            stored answer is a matrix.) Has keys:

            is_raised (bool): If true, a ShapeError will be raised, otherwise
                the student's input will be marked incorrect. In either case,
                feedback is provided according to the `msg_detail` key.
                Defaults to True.
            msg_detail (None|'type'|'shape'): How detailed the feedback message
                should be.
                    None: No feedback is provided.
                    'type': Type information about the expected/received objects
                        is revealed (e.g., matrix vs vector)
                    'shape': Type and shape information about the expected and
                        received objects is revealed.

    """

    # merge_dicts does not mutate the originals
    default_functions = merge_dicts(FormulaGrader.default_functions,
                                    ARRAY_ONLY_FUNCTIONS)

    @property
    def schema_config(self):
        schema = super(MatrixGrader, self).schema_config
        return schema.extend({
            Required('identity_dim', default=None): NonNegative(int),
            Required('max_array_dim', default=1): NonNegative(int),
            Required('negative_powers', default=True): bool,
            Required('shape_errors', default=True): bool,
            Required('answer_shape_mismatch', default={
                'is_raised': True,
                'msg_detail': 'type'
            }): {
                Required('is_raised', default=True): bool,
                Required('msg_detail', default='type'): Any(None, 'type', 'shape')
            }
        })

    def __init__(self, config=None, **kwargs):
        super(MatrixGrader, self).__init__(config, **kwargs)
        if self.config['identity_dim'] and not self.constants.get('I', None):
            self.constants['I'] = identity(self.config['identity_dim'])

    def check_response(self, answer, student_input, **kwargs):
        try:
            with MathArray.enable_negative_powers(self.config['negative_powers']):
                result = super(MatrixGrader, self).check_response(answer, student_input, **kwargs)
        except ShapeError as err:
            if self.config['shape_errors']:
                raise
            else:
                return {'ok': False, 'msg': err.message, 'grade_decimal': 0}
        except InputTypeError as err:
            if self.config['answer_shape_mismatch']['is_raised']:
                raise
            else:
                return {'ok': False, 'grade_decimal': 0, 'msg': err.message}
        return result

    @staticmethod
    def validate_student_input_shape(student_input, expected_shape, detail):
        """
        Checks that student_input has expected_shape and raises a ShapeError
        if it does not.

        Arguments:
            student_input (number | MathArray): The numerically-sampled student
                input
            expected_shape (tuple): A numpy shape tuple
            detail (None|'shape'|'type') detail-level of ShapeError message
        """
        try:
            input_shape = student_input.shape
        except AttributeError:
            if isinstance(student_input, Number):
                input_shape = tuple()
            else:
                raise

        if expected_shape == input_shape:
            return True

        if detail is None:
            raise InputTypeError('')

        if detail == 'shape':
            expected = MathArray.get_description(expected_shape)
            received = MathArray.get_description(input_shape)
        else:
            expected = MathArray.get_shape_name(len(expected_shape))
            received = MathArray.get_shape_name(len(input_shape))

        if detail != 'shape' and expected == received:
            msg = ("Expected answer to be a {0}, but input is a {1} "
                   "of incorrect shape".format(expected, received))
        else:
            msg = ("Expected answer to be a {0}, but input is a {1}"
                .format(expected, received))

        raise InputTypeError(msg)

    Utils = namedtuple('Utils', ['tolerance', 'within_tolerance', 'validate_shape'])

    def get_comparer_utils(self):
        """Get the utils for comparer function."""
        def _within_tolerance(x, y):
            return within_tolerance(x, y, self.config['tolerance'])
        def _validate_shape(student_input, shape):
            detail = self.config['answer_shape_mismatch']['msg_detail']
            return self.validate_student_input_shape(student_input, shape, detail)

        return self.Utils(tolerance=self.config['tolerance'],
                          within_tolerance=_within_tolerance,
                          validate_shape=_validate_shape)
