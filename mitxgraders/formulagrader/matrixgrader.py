"""
matrixgrader.py

Defines a FormulaGrader subtype that handles matrices, too.
"""
from mitxgraders.formulagrader.formulagrader import FormulaGrader
from voluptuous import Required, Any
from mitxgraders.helpers.validatorfuncs import NonNegative
from mitxgraders.helpers.calc import IdentityMultiple, MathArray
from mitxgraders.helpers.calc.exceptions import (
    MathArrayShapeError as ShapeError)
from mitxgraders.helpers.calc.mathfuncs import (
    merge_dicts, ARRAY_ONLY_FUNCTIONS)
from mitxgraders.helpers.calc.formatters import get_description

class MatrixGrader(FormulaGrader):
    """
    An extension of FormulaGrader with better support for grading expressions
    with vectors and matrices. Includes an extra default constant ('I', for the
    identity operator) and some extra default functions (trans, det, ...)

    Configuration options as per FormulaGrader, except:
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
    default_variables = merge_dicts(FormulaGrader.default_functions,
                                    {'I': IdentityMultiple(1)})

    @property
    def schema_config(self):
        schema = super(MatrixGrader, self).schema_config
        return schema.extend({
            Required('max_array_dim', default=1): NonNegative(int),
            Required('negative_powers', default=True): bool,
            Required('shape_errors', default=True): bool,
            Required('answer_shape_mismatch', default={}): {
                Required('is_raised', default=True): bool,
                Required('msg_detail', default='type'): Any(None, 'type', 'shape')
            }
        })

    def check_response(self, answer, student_input, **kwargs):
        try:
            with MathArray.enable_negative_powers(self.config['negative_powers']):
                result = super(MatrixGrader, self).check_response(answer, student_input, **kwargs)
        except ShapeError as err:
            if self.config['shape_errors']:
                raise
            else:
                return {'ok': False, 'msg': err.message, 'grade_decimal': 0}
        return result

    def default_equality_comparer(self, comparer_params, student_input, utils):
        """
        Default comparer function.

        Assumes comparer_params is just the single expected answer wrapped in a list.
        """
        try:
            return utils.within_tolerance(comparer_params[0], student_input)
        except ShapeError as err:
            is_raised = self.config['answer_shape_mismatch']['is_raised']
            msg_detail = self.config['answer_shape_mismatch']['msg_detail']

            if msg_detail is None:
                msg = ''
            else:
                detailed = msg_detail == 'shape'
                expected_shape = get_description(comparer_params[0], detailed=detailed)
                received_shape = get_description(student_input, detailed=detailed)
                if not detailed and expected_shape == received_shape:
                    msg = ("Expected answer to be a {0}, but input is a {1} "
                           "of incorrect shape".format(expected_shape, received_shape))
                else:
                    msg = ("Expected answer to be a {0}, but input is a {1}"
                        .format(expected_shape, received_shape))

            if is_raised:
                raise ShapeError(msg)
            else:
                return {'ok': False, 'grade_decimal': 0, 'msg': msg}
