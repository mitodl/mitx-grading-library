"""
baseclasses.py

Contains base classes for the library:
* ObjectWithSchema
* AbstractGrader
* ItemGrader
"""
from __future__ import division
import numbers
import abc
from graders.voluptuous import Schema, Required, All, Any, Range, MultipleInvalid
from graders.voluptuous.humanize import validate_with_humanized_errors as voluptuous_validate
from graders.version import __version__

class ConfigError(Exception):
    """Raised whenever a configuration error occurs"""
    pass

class ObjectWithSchema(object):
    """Represents an author-facing object whose configuration needs validation."""

    # This is an abstract base class
    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def schema_config(self):
        """
        The schema that defines the configuration of this object.
        The schema MUST be independent of the config itself. If you need to further validate
        parts of the config based on the config, do so in the __init__ method. See ListGrader
        for an example.
        """
        pass

    def validate_config(self, config):
        """
        Validates the supplied config with human-readable error messages.
        Returns a mutated config variable that conforms to the schema.
        """
        return voluptuous_validate(config, self.schema_config)

    def __init__(self, config=None, **kwargs):
        """
        Validate the supplied config for the object, using either a config dict or kwargs,
        but not both.
        """
        if config is None:
            self.config = self.validate_config(kwargs)
        else:
            self.config = self.validate_config(config)

    def __repr__(self):
        """Printable representation of the object"""
        return "{classname}({config})".format(classname=self.__class__.__name__, config=self.config)

class AbstractGrader(ObjectWithSchema):
    """
    Abstract grader class. All graders must build on this class.

    Configuration options:
        debug (bool): Whether to add debug information to the output. Can also affect
            the types of error messages that are generated to be more technical (for
            authors) or more user-friendly (for students) (default True)
    """

    # This is an abstract base class
    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def schema_config(self):
        """
        Defines the default config schema for abstract graders.
        Classes that inherit from AbstractGrader should extend this schema.
        """
        return Schema({
            Required('debug', default=False): bool  # Use to turn on debug output
        })

    @abc.abstractmethod
    def check(self, answers, student_input):
        """
        Check student_input for correctness and provide feedback.

        Arguments:
            answers: The expected result(s) and grading information
            student_input: The student's input passed by edX
        """
        pass

    def __call__(self, expect, student_input):
        """
        Used to ask the grading class to grade student_input.
        Used by edX as the check function (cfn).

        Arguments:
            expect: The value of edX customresponse expect attribute (ignored)
            student_input: The student's input passed by edX

        Notes:
            This function ignores the value of expect.

            This is because edX requires a two-parameter check function cfn
            with the signature above. In the graders module, we NEVER use
            the <customresponse /> tag's expect attribute for grading.

            (Our check functions require an answer dictionary, as described
            in the documentation.)

            But we do want to allow authors to use the edX <customresponse />
            expect attribute because its value is displayed to students as
            the "correct" answer.

            The answer that we pass to check is None, indicating that the
            grader should read the answer from its internal configuration.
        """
        result = self.check(None, student_input)

        if self.config['debug']:
            # Construct the debug output
            debugoutput = "MITx Grading Library Version " + __version__ + "\n"
            if isinstance(student_input, list):
                debugoutput += "Student Responses:\n" + "\n".join(student_input)
            else:
                debugoutput += "Student Response:\n" + student_input
            # Append the message
            if "input_list" in result:
                if result.get('overall_message', ''):
                    result['overall_message'] += "\n\n" + debugoutput
                else:
                    result['overall_message'] = debugoutput
            else:
                if result.get('msg', ''):
                    result['msg'] += "\n\n" + debugoutput
                else:
                    result['msg'] = debugoutput

        return result

class ItemGrader(AbstractGrader):
    """
    Abstract base class that represents a grader that grades a single input.
    Almost all grading classes should inherit from this class. The most notable
    exception is ListGrader.

    This class looks after the basic schema required to describe answers to a problem,
    allowing for multiple ways of providing those answers. It also looks after checking
    student input against all possible answers.

    Inheriting classes must implement check_response. If any extra parameters are added
    to the config, then schema_config should be extended (see StringGrader, for example).
    The only other thing you may want to shadow is schema_expect, to add parsing to
    answers.

    Answers can be provided in one of two forms:
        * An answer string
        * A dictionary:
            {'expect': answer, 'grade_decimal': number, 'ok': value, 'msg'}
            expect: Stores the expected answer as a string (Required)
            grade_decimal: Stores the grade as a decimal that this answer should receive.
                If set, overrides 'ok' entry (default 1)
            ok: Can be set to True, False, 'partial' or 'computed' (default). Ignored if
                'grade_decimal' is not 1.
            msg: Message to return to the student if they provide this answer (default "")
    Internally, an answer string will be coverted into a dictionary with 'ok'=True.

    Configuration options:
        answers (varies): A single answer in one of the above forms, or a tuple of answers
            in the above forms. Not required, as answers can be provided later.

        wrong_msg (str): A generic message to give the students upon submission of an
            answer that received a grade of 0 (default "")
    """

    # This is an abstract base class
    __metaclass__ = abc.ABCMeta

    @property
    def schema_config(self):
        """
        Defines the default config schema for item graders.
        Classes that inherit from ItemGrader should extend this schema.
        """
        schema = super(ItemGrader, self).schema_config
        return schema.extend({
            Required('answers', default=tuple()): self.schema_answers,
            Required('wrong_msg', default=""): str
        })

    def schema_answers(self, answer_tuple):
        """
        Defines the schema to validate an answer tuple against (eg, config['answers']).

        This will transform the input to a tuple as necessary, and then call
        validate_single_answer to validate individual answers.

        Arguments:
            answer_tuple: The input answers to validate and return in a conforming state
        """
        if not isinstance(answer_tuple, tuple):
            answer_tuple = (answer_tuple,)
        schema = Schema((self.validate_single_answer,))
        return schema(answer_tuple)

    def validate_single_answer(self, answer):
        """
        Validates a single answer.
        Transforms the answer to conform with schema_answer and returns it.
        If invalid, raises an error.

        Arguments:
            answer: The answer to validate. Two forms are acceptable:
                1. A schema_answer dictionary (we compute the 'ok' value if needed)
                2. A schema_answer['expect'] value (validated as {'expect': answer})
        """
        try:
            # Try to validate against the answer schema
            validated_answer = self.schema_answer(answer)
        except MultipleInvalid:
            try:
                # Ok, assume that answer is a single 'expect' value
                validated_answer = self.schema_answer({'expect': answer, 'ok': True})
            except MultipleInvalid:
                # Unable to interpret your answer!
                raise

        # If the 'ok' value is 'computed' or the grade decimal is not 1,
        # then compute what it should be
        if validated_answer['ok'] == 'computed' or validated_answer['grade_decimal'] != 1:
            validated_answer['ok'] = self.grade_decimal_to_ok(validated_answer['grade_decimal'])

        return validated_answer

    @staticmethod
    def grade_decimal_to_ok(grade):
        """Converts a grade decimal into an 'ok' value: True, False or 'partial'"""
        return {0: False, 1: True}.get(grade, 'partial')

    @property
    def schema_answer(self):
        """Defines the schema that a fully-specified answer should satisfy."""
        return Schema({
            Required('expect'): self.schema_expect,
            Required('grade_decimal', default=1): All(numbers.Number, Range(0, 1)),
            Required('msg', default=''): str,
            Required('ok', default='computed'): Any('computed', True, False, 'partial')
        })

    # Defines the schema that a supplied answer should satisfy.
    # This is simply a string, because students enter answers as a string.
    # If this is shadowed, it should only be to parse the string.
    schema_expect = Schema(str)

    def check(self, answers, student_input):
        """
        Compares student input to each answer in answers, using check_response.
        Computes the best outcome for the student.

        Arguments:
            answer: A tuple of answers to compare to, or None to use internal config
            student_input (str): The student's input passed by edX
        """
        # If no answers provided, use the internal configuration
        answers = self.config['answers'] if answers is None else answers

        # answers should now be a tuple of answers
        # Check that there is at least one answer to compare to
        if not isinstance(answers, tuple):
            msg = "Expected answers to be a tuple of answers, instead received {}"
            raise ConfigError(msg.format(type(answers)))
        if not answers:
            raise ConfigError("Expected at least one answer in answers")

        # Make sure the input is in the expected format
        if not isinstance(student_input, basestring):
            msg = "Expected string for student_input, received {}"
            raise ConfigError(msg.format(type(student_input)))

        # Compute the results for each answer
        results = [self.check_response(answer, student_input) for answer in answers]

        # Now find the best result for the student
        best_score = max([r['grade_decimal'] for r in results])
        best_results = [r for r in results if r['grade_decimal'] == best_score]
        best_result_with_longest_msg = max(best_results, key=lambda r: len(r['msg']))

        # Add in wrong_msg if appropriate
        if best_result_with_longest_msg['msg'] == "" and best_score == 0:
            best_result_with_longest_msg['msg'] = self.config["wrong_msg"]

        return best_result_with_longest_msg

    @abc.abstractmethod
    def check_response(self, answer, student_input):
        """
        Compares student_input against a single answer.
        Differs from check, which must compare against all possible answers.
        This must be implemented by inheriting classes.

        Arguments:
            answer (schema_answer): The answer to compare to
            student_input (str): The student's input passed by edX
        """
        pass
