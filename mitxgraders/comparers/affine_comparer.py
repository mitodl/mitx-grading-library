import numpy as np
from voluptuous import Schema, Required, Any, All, Optional, Range
from mitxgraders.comparers.baseclasses import CorrelatedComparer

from mitxgraders.helpers.validatorfuncs import equals
from mitxgraders.helpers.calc.mathfuncs import is_nearly_zero



class AffineComparer(CorrelatedComparer):
    """docstring for AffineComparer.""" #TODO

    schema_config = Schema({
        Required('mode', default='proportional'): Any('proportional', 'offset', 'affine'),
        Required('grade_decimal', default=0.5): Range(0, 1),
        Optional('msg'): str
    })

    default_messages = {
        'proportional': 'The submitted answer differs from the expected answer by a constant factor.',
        'offset': '',
        'affine': ''
    }

    def get_message(self):
        config_msg = self.config.get('msg', None)
        mode = self.config['mode']

        if config_msg is None:
            return self.default_messages[mode]
        return config_msg


    def get_fit_error(self, comparer_params_evals, student_evals):
        """

        """

        student = np.array(student_evals).flatten()
        expected = np.array(comparer_params_evals).flatten()

        if self.config['mode'] == 'proportional':
            a = np.vstack(student)
            b = expected
            x, residuals, _, _ = np.linalg.lstsq(a, b, rcond=-1)
        elif self.config['mode'] == 'affine':
            a = np.vstack([student, np.ones(len(student))]).T
            b = expected
            x, residuals, _, _ = np.linalg.lstsq(a, b, rcond=-1)
        elif self.config['mode'] == 'offset':
            a = student
            b = expected
            mean = np.mean(a - b)
            residuals = np.var(a + mean - b)


        error = np.sqrt(residuals)

        return error

    def __call__(self, comparer_params_evals, student_evals, utils):
        student_eval_norm = np.linalg.norm(student_evals)/len(student_evals)

        # Validate student input shape...only needed for MatrixGrader
        try:
            utils.validate_shape(student_evals[0], comparer_params_evals[0][0].shape)
        except AttributeError:
            pass # not called by MatrixGrader

        if is_nearly_zero(student_eval_norm, utils.tolerance, reference=student_evals):
            return False

        error = self.get_fit_error(comparer_params_evals, student_evals)

        if is_nearly_zero(error, utils.tolerance, reference=student_eval_norm):
            return {
                'grade_decimal': self.config['grade_decimal'],
                'msg': self.get_message()
            }

        return False

# Used by FormulaGrader's Schema
def affine_mode_schema(mode):
    """
    """ # TODO
    return Any(
        Schema({
            Required('grade_decimal', default=0.5): Range(0, 1),
            Optional('msg'): str,
            Required('mode', default=mode): equals(mode)
        }),
        All(
             Range(0, 1),
            lambda x: {'grade_decimal': x, 'mode': mode}
        )
    )
