"""
stringgrader.py

Class for grading inputs that correspond to a text string
* StringGrader
"""
from graders.baseclasses import ItemGrader
from graders.voluptuous import Required

# Set the objects to be imported from this grader
__all__ = ["StringGrader"]

class StringGrader(ItemGrader):
    """
    Grader based on exact comparison of strings

    Configuration options:

    grader = StringGrader(
        answers='cat',
        strip=True,
        case_sensitive=True
    )

    answers: List of answers in the typical form
    strip: Whether or not to strip leading and trailing whitespace
           from answers/student responses before comparing to answers (default True)
    case_sensitive: Whether to be case sensitive in comparisons (default True)
    """

    @property
    def schema_config(self):
        """Define the configuration options for StringGrader"""
        # Construct the default ItemGrader schema
        schema = super(StringGrader, self).schema_config
        # Append options
        return schema.extend({
            Required('strip', default=True): bool,
            Required('case_sensitive', default=True): bool
        })

    def check_response(self, answer, student_input):
        """
        Grades a student response against a given answer

        Arguments:
            answer (str): The answer to compare to
            student_input (str): The student's input passed by edX
        """
        expect = answer['expect']
        student = student_input

        # Apply options
        if self.config['strip']:
            expect = expect.strip()
            student = student.strip()
        if not self.config['case_sensitive']:
            expect = expect.lower()
            student = student.lower()

        # Perform comparison
        if expect == student:
            return {
                'ok': answer['ok'],
                'grade_decimal': answer['grade_decimal'],
                'msg': answer['msg']
            }

        return {'ok': False, 'grade_decimal': 0, 'msg': ''}
