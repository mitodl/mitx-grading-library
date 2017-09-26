"""
Contains base classes for the library:
* ObjectWithSchema
* AbstractGrader
* ItemGrader
"""
from __future__ import division
from helpers import munkres
import numbers
import abc
from voluptuous import Schema, Required, All, Any, Range, MultipleInvalid
from voluptuous.humanize import validate_with_humanized_errors as voluptuous_validate

class ObjectWithSchema(object):
    """Represents a user-facing object whose configuration needs validation."""

    # This is an abstract base class
    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def schema_config(self):
        """The schema that defines the configuration of this object"""
        pass

    def validate_config(self, config):
        """
        Validates the supplied config with human-readable error messages.
        Returns a mutated config variable that conforms to the schema.
        """
        return voluptuous_validate(config, self.schema_config)

    def __init__(self, config=None):
        """Validate the supplied config for the object"""
        # Set the config first before validating, so that schema_config has access to it
        # I don't like this; it makes for a tangled mess
        # (schema_config may access the config before it's been validated/manipulated into valid form)
        self.config = {} if config is None else config
        self.config = self.validate_config(self.config)

    def __repr__(self):
        """Printable representation of the object"""
        return "{classname}({config})".format(classname=self.__class__.__name__, config=self.config)

class AbstractGrader(ObjectWithSchema):
    """Abstract grader class. All graders must build on this class."""

    # This is an abstract base class
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def check(self, answer, student_input):
        """
        Check student_input for correctness and provide feedback.

        Arguments:
            answer: The expected result and grading information
            student_input: The student's input passed by edX
        """
        pass

    def __call__(self, expect, student_input):
        """
        Ignores expect and grades student_input.
        Used by edX as the check function (cfn).

        Arguments:
            expect: The value of edX customresponse expect attribute
            student_input: The student's input passed by edX

        NOTES:
            This function ignores the value of expect. Reason:

            edX requires a two-parameter check function cfn with
            the signature above. In the graders module, we NEVER use
            the <customresponse /> tag's expect attribute for grading.

            (Our check functions require an answer dictionary, as described
            in the documentation.)

            But we do want to allow authors to use the edX <customresponse />
            expect attribute because its value is displayed to students.

            The answer that we pass to check is None, indicating that the
            grader should read the answer from its internal configuration.
        """
        return self.check(None, student_input)

class ItemGrader(AbstractGrader):

    __metaclass__ = abc.ABCMeta

    @property
    def schema_expect(self):
        """
        The default schema for ItemGraders is to have the answer supplied in a string.
        This is because it is the expect value, which a student would have to supply in
        a text box.
        """
        return Schema(str)

    @staticmethod
    def grade_decimal_to_ok(gd):
        if gd == 0 :
            return False
        elif gd == 1:
            return True
        else:
            return 'partial'

    @property
    def schema_answer(self):
        return Schema({
            Required('expect', default=None): self.schema_expect,
            Required('grade_decimal', default=1): All(numbers.Number, Range(0,1)),
            Required('msg', default=''): str,
            Required('ok',  default='computed'):Any('computed', True, False, 'partial')
        })

    @property
    def schema_answers(self):
        def validate_and_transform_answer(answer_or_expect):
            """ XXX = answer_or_expect
            If XXX is a valid schema_answer, compute  the 'ok' value if needed.
            If XXX is not a valid schema, try validating {'expect':XXX}

            """

            try:
                answer = self.schema_answer(answer_or_expect)
                if answer['ok'] == 'computed':
                    answer['ok'] = self.grade_decimal_to_ok( answer['grade_decimal'] )
                return answer
            except MultipleInvalid:
                try:
                    return self.schema_answer({'expect':answer_or_expect,'ok':True})
                except MultipleInvalid:
                    raise ValueError

        return Schema( [validate_and_transform_answer] )

    @property
    def schema_config(self):
        return Schema({
            Required('answers', default=[]): self.schema_answers
        })

    def check(self, answers, student_input):
        """
        Compares student input to each answer in answers, using check_response.
        Computes the best outcome for the student.
        """
        # If no answers provided, use the internal configuration
        answers = self.config['answers'] if answers == None else answers

        # Compute the results for each answer
        results = [ self.check_response(answer, student_input) for answer in answers]

        # Compute the best result for the student
        best_score = max([ r['grade_decimal'] for r in results ])
        best_results = [ r for r in results if r['grade_decimal'] == best_score]
        best_result_with_longest_msg = max(best_results, key = lambda r: len(r['msg']))

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
