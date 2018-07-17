"""
matrixgrader.py

Defines a FormulaGrader subtype that handles matrices, too.
"""
from mitxgraders.formulagrader.formulagrader import FormulaGrader
from voluptuous import Required
from mitxgraders.helpers.validatorfuncs import NonNegative
from mitxgraders.helpers.mitmath import IdentityMultiple, MathArray
from mitxgraders.helpers.mitmath.exceptions import (
    MathArrayShapeError as ShapeError)
from mitxgraders.helpers.mitmath.mathfuncs import (
    merge_dicts, ARRAY_ONLY_FUNCTIONS)

class MatrixGrader(FormulaGrader):

    # merge_dicts does not mutate the originals
    default_functions = merge_dicts(FormulaGrader.default_functions,
                                    ARRAY_ONLY_FUNCTIONS)
    default_variables = merge_dicts(FormulaGrader.default_functions,
                                    {'I': IdentityMultiple(1)})

    @property
    def schema_config(self):
        schema = super(MatrixGrader, self).schema_config
        return schema.extend({
            Required('max_array_dim', default=2): NonNegative(int),
            Required('shape_errors', default=True): bool,
            Required('negative_powers', default=True): bool
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
