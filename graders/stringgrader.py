from baseclasses import ItemGrader
from voluptuous import Schema, Required

class StringGrader(ItemGrader):

    @property
    def schema_config(self):
        schema = super(StringGrader, self).schema_config
        return schema.extend({
            Required('strip', default=True): bool,
            Required('case_sensitive', default=True) : bool
        })

    def check_response(self, answer, student_input):
        if self.config['strip']:
            answer['expect'] = answer['expect'].strip()
            student_input = student_input.strip()

        if student_input.strip() == answer['expect'].strip():
            return {'ok':answer['ok'], 'grade_decimal':answer['grade_decimal'], 'msg':answer['msg']}
        else:
            return {'ok':False, 'grade_decimal':0, 'msg':''}

# Set the objects to be imported from this grader
__all__ = ["StringGrader"]
