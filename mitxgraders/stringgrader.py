"""
stringgrader.py

Class for grading inputs that correspond to a text string
* StringGrader
"""
from __future__ import print_function, division, absolute_import, unicode_literals
import re
from voluptuous import Required, Any
from mitxgraders.baseclasses import ItemGrader
from mitxgraders.helpers.validatorfuncs import NonNegative, text_string
from mitxgraders.exceptions import InvalidInput, ConfigError

# Set the objects to be imported from this grader
__all__ = ["StringGrader"]

class StringGrader(ItemGrader):
    """
    Grader based on exact comparison of strings

    Configuration options:
    * Cleaning input
        case_sensitive (bool): Whether to be case sensitive in comparing responses to
            answers (default True)

        clean_spaces (bool): Whether or not to convert multiple spaces into single spaces
            before comparing (default True)

        strip (bool): Whether or not to strip leading and trailing whitespace
            from answers/student input before comparing (default True)

        strip_all (bool): Whether or not to remove all spaces from student
            input before grading (default False)

    * Accepting any input
        accept_any (bool): Whether to accept any answer as correct (default False)

        accept_nonempty (bool): Whether to accept any nonempty answer as correct.
            Implemented as turning on accept_any and ensuring that min_length > 0.
            (default False)

        min_length (int): When using accept_any or accept_nonempty, sets the minimum
            number of characters required to be entered in order to be graded
            correct (default 0)

        min_words (int): When using accept_any or accept_nonempty, sets the minimum
            number of words required to be entered in order to be graded
            correct (default 0)

        explain_minimums ('err', 'msg', None): If a response is unsatisfactory due to
            min_length or min_words being insufficient, do we raise an error ('err'),
            grade as incorrect but present a message ('msg' or debug=True), or just grade
            as incorrect (None)? (default 'err')

    * Validating input
        validation_pattern (str or None): A regex pattern to validate the cleaned input
            against. If the pattern is not satisfied, the setting in explain_validation
            is followed. Applies even when accept_any/accept_nonempty are True.
            (default None)

        explain_validation ('err', 'msg', None): How to proceed when the student response
            does not satisfy the validation_pattern. Raise an error ('err'), grade as
            incorrect but present a message ('msg' or debug=True), or just grade as
            incorrect (None)? (default 'err')

        invalid_msg (str): Error message presented to students if their input does
            not satisfy the validation pattern
            (default 'Your input is not in the expected format')
    """

    @property
    def schema_config(self):
        """Define the configuration options for StringGrader"""
        # Construct the default ItemGrader schema
        schema = super(StringGrader, self).schema_config
        # Append options
        return schema.extend({
            Required('case_sensitive', default=True): bool,
            Required('strip', default=True): bool,
            Required('strip_all', default=False): bool,
            Required('clean_spaces', default=True): bool,
            Required('accept_any', default=False): bool,
            Required('accept_nonempty', default=False): bool,
            Required('min_length', default=0): NonNegative(int),
            Required('min_words', default=0): NonNegative(int),
            Required('explain_minimums', default='err'): Any('err', 'msg', None),
            Required('validation_pattern', default=None): Any(text_string, None),
            Required('explain_validation', default='err'): Any('err', 'msg', None),
            Required('invalid_msg', default='Your input is not in the expected format'): text_string
            })

    def clean_input(self, input):
        """
        Performs cleaning operations on the given input, according to
        case_sensitive, strip, strip_all and clean_spaces.

        Also converts tabs and newlines spaces for the purpose of grading.
        """
        cleaned = text_string(input)

        # Convert \t and newline characters (\r and \n) to spaces
        # Note: there is no option for this conversion
        cleaned = cleaned.replace('\t', ' ')
        cleaned = cleaned.replace('\r\n', ' ')
        cleaned = cleaned.replace('\n\r', ' ')
        cleaned = cleaned.replace('\r', ' ')
        cleaned = cleaned.replace('\n', ' ')

        # Apply case sensitivity
        if not self.config['case_sensitive']:
            cleaned = cleaned.lower()

        # Apply strip, strip_all and clean_spaces
        if self.config['strip']:
            cleaned = cleaned.strip()
        if self.config['strip_all']:
            cleaned = cleaned.replace(' ', '')
        if self.config['clean_spaces']:
            cleaned = re.sub(r' +', ' ', cleaned)

        return cleaned

    def construct_message(self, msg, msg_type):
        """
        Depending on the configuration, construct the appropriate return dictionary
        for a bad entry or raises an error.

        Arguments:
            msg: Message to return if a message should be returned
            msg_type: Type of message to return ('err', 'msg', or None)
        """
        invalid_response = {'ok': False, 'grade_decimal': 0, 'msg': ''}
        if msg_type == 'err':
            raise InvalidInput(msg)
        elif msg_type == 'msg' or self.config['debug']:
            invalid_response['msg'] = msg
        return invalid_response

    def check_response(self, answer, student_input, **kwargs):
        """
        Grades a student response against a given answer

        Arguments:
            answer (dict): Dictionary describing the expected answer,
                           its point value, and any associated message
            student_input (str): The student's input passed by edX
        """
        expect = self.clean_input(answer['expect'])
        student = self.clean_input(student_input)

        # Figure out if we are accepting any input
        accept_any = self.config['accept_any'] or self.config['accept_nonempty']
        min_length = self.config['min_length']
        if self.config['accept_nonempty'] and min_length == 0:
            min_length = 1

        # Apply the validation pattern
        pattern = self.config['validation_pattern']
        if pattern is not None:
            # Make sure that the pattern matches the entire input
            testpattern = pattern
            if not pattern.endswith("^"):
                testpattern += "$"

            if not accept_any:
                # Make sure that expect matches the pattern
                # If it doesn't, a student can never get this right
                if re.match(testpattern, expect) is None:
                    msg = "The provided answer '{}' does not match the validation pattern '{}'"
                    raise ConfigError(msg.format(answer['expect'], pattern))

            # Check to see if the student input matches the validation pattern
            if re.match(testpattern, student) is None:
                return self.construct_message(self.config['invalid_msg'],
                                              self.config['explain_validation'])

        # Perform the comparison
        if not accept_any:
            # Check for a match to expect
            if student != expect:
                return {'ok': False, 'grade_decimal': 0, 'msg': ''}
        else:
            # Check for the minimum length
            msg = None
            chars = len(student)
            if chars < min_length:
                msg = ('Your response is too short ({chars}/{min} characters)'
                       ).format(chars=chars, min=min_length)

            # Check for minimum word count (more important than character count)
            words = len(student.split())
            if words < self.config['min_words']:
                msg = ('Your response is too short ({words}/{min} words)'
                       ).format(words=words, min=self.config['min_words'])

            # Give student feedback
            if msg:
                return self.construct_message(msg,
                                              self.config['explain_minimums'])

        # If we got here, everything is correct
        return {
            'ok': answer['ok'],
            'grade_decimal': answer['grade_decimal'],
            'msg': answer['msg']
        }

    def __call__(self, expect, student_input, **kwargs):
        """
        The same as ItemGrader.__call__, except that we accept a None
        entry for expect if accept_any or accept_nonempty are set.
        """
        if expect is None and (self.config['accept_any'] or self.config['accept_nonempty']):
            expect = ""

        return super(StringGrader, self).__call__(expect, student_input, **kwargs)
