from __future__ import division
from helpers import munkres
import numbers
import abc
from voluptuous import Schema, Required, All, Any, Range, MultipleInvalid
from voluptuous.humanize import validate_with_humanized_errors as voluptuous_validate

class ObjectWithSchema(object):
    "Represents a user-facing object whose configuration needs validation."

    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def schema_config(self):
        pass

    def validate_config(self, config):
        """Validates config and prints human-readable error messages."""
        return voluptuous_validate(config, self.schema_config)

    def __init__(self, config=None):
        # Set the config first before validating, so that schema_config has access to it
        # I don't like this; it makes for a tangled mess
        # (schema_config may access the config before it's been validated/manipulated into valid form)
        self.config = {} if config is None else config
        self.config = self.validate_config(self.config)

    def __repr__(self):
        return "{classname}({config})".format(classname=self.__class__.__name__, config = self.config)

class AbstractGrader(ObjectWithSchema):

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def check(self, answer, student_input):
        """ Check student_input for correctness and provide feedback.

        Args:
            answer (dict): The expected result and grading information; has form
                {'expect':..., 'ok':..., 'msg':..., 'grade_decimal':...}  #J: I don't think this is the form you've used later...
            student_input (str): The student's input passed by edX  #J: Is this always a string?
        """
        pass

    def __call__(self, expect, student_input):
        """
        Ignores expect and grades student_input.
        Used by edX as the check function (cfn).

        Arguments:
            expect (str): The value of edX customresponse expect attribute.  #J: Is this always a string?
            student_input (str): The student's input passed by edX  #J: Is this always a string?

        NOTES:
            This function ignores the value of expect. Reason:

            edX requires a two-parameter check function cfn with
            the signature above. In the graders module, we NEVER use
            the <customresponse /> tag's expect attribute for grading.

            (Our check functions require an answer dictionary, as described
            in the documentation for check.)

            But we do want to allow authors to use the edX <customresponse />
            expect attribute because it's value is displayed to students.
        """
        return self.check(None, student_input)

class ItemGrader(AbstractGrader):

    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def schema_expect(self):
        pass

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

    def validate_single_answer(self, answer):
        """
        Validates a single answer.
        Transforms the answer to conform with schema_answer and returns it.
        If invalid, raises ValueError.

        Two forms are acceptable:
        1. A schema_answer dictionary (we compute the 'ok' value if needed)
        2. A schema_answer['expect'] value (validated as {'expect': answer})
        """
        try:
            validated_answer = self.schema_answer(answer)
            if validated_answer['ok'] == 'computed':
                validated_answer['ok'] = self.grade_decimal_to_ok( validated_answer['grade_decimal'] )
            return validated_answer
        except MultipleInvalid:
            try:
                return self.schema_answer({'expect':answer, 'ok':True})
            except MultipleInvalid:
                raise ValueError

    @property
    def schema_answers(self):
        """
        Returns the schema to validate an answer list against.

        This will transform the input to a list as necessary, and then call
        validate_single_answer to validate individual answers.

        Usually used to validate config['answers'].

        Three forms for the answer list are acceptable:

        1. A list of dictionaries, each a valid schema_answer
        2. A list of schema_answer['expect'] values
        3. A single schema_answer['expect'] value
        """
        def validate_answers(answer_list):
            if not isinstance(answer_list, list):
                answer_list = [answer_list]
            schema = Schema([self.validate_single_answer])
            return schema(answer_list)

        return validate_answers

    @property
    def schema_config(self):
        return Schema({
            Required('answers', default=[]): self.schema_answers
        })

    def iterate_check(self, check):
        def iterated_check(answers, student_input):
            """
            Iterates check over each answer in answers
            """
            answers = self.config['answers'] if answers == None else answers

            results = [ check(answer, student_input) for answer in answers]

            best_score = max([ r['grade_decimal'] for r in results ])
            best_results = [ r for r in results if r['grade_decimal'] == best_score]
            best_result_with_longest_msg = max(best_results, key = lambda r: len(r['msg']))

            return best_result_with_longest_msg

        return iterated_check

    def __init__(self, config={}):
        super(ItemGrader, self).__init__(config)
        # Note that self.check MUST be shadowed by a subclass, so on the RHS
        # here, self.check refers to the subclassed function
        # However, we do overwrite it :-)
        # TODO this is pretty bad! We should figure out how to NOT do this!
        self.check = self.iterate_check(self.check)
