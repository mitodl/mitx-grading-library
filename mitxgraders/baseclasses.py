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
from voluptuous import Schema, Required, All, Any, Range, MultipleInvalid
from voluptuous.humanize import validate_with_humanized_errors as voluptuous_validate
from mitxgraders.version import __version__
from mitxgraders.exceptions import ConfigError, MITxError, StudentFacingError

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
            Required('debug', default=False): bool,  # Use to turn on debug output
            Required('suppress_warnings', default=False): bool
        })

    @abc.abstractmethod
    def check(self, answers, student_input, **kwargs):
        """
        Check student_input for correctness and provide feedback.

        Arguments:
            answers: The expected result(s) and grading information
            student_input: The student's input passed by edX
            **kwargs: Anything else that has been passed in. For example, sibling
                graders when a grader is used as a subgrader in a ListGrader.
        """

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
        # Initialize the debug log
        # The debug log always exists and is written to, so that it can be accessed
        # programmatically. It is only output with the grading when config["debug"] is True
        # When subgraders are used, they need to be given access to this debuglog.
        # Note that debug=True must be set on parents to obtain debug output from children
        # when nested graders (lists) are used.
        self.debuglog = []
        # Add the version to the debug log
        self.log("MITx Grading Library Version " + __version__)
        # Add the student inputs to the debug log
        if isinstance(student_input, list):
            self.log("Student Responses:\n" + "\n".join(map(str, student_input)))
        else:
            self.log("Student Response:\n" + str(student_input))

        # Compute the result of the check
        try:
            result = self.check(None, student_input)
        except Exception as error:
            if self.config['debug']:
                raise
            elif isinstance(error, MITxError):
                # we want to re-raise the error with a modified message but the
                # same class type, hence calling __class__
                raise error.__class__(error.message.replace('\n', '<br/>'))
            else:
                # Otherwise, give a generic error message
                if isinstance(student_input, list):
                    msg = "Invalid Input: Could not check inputs '{}'"
                    formatted = msg.format("', '".join(student_input))
                else:
                    msg = "Invalid Input: Could not check input '{}'"
                    formatted = msg.format(student_input)
                raise StudentFacingError(formatted)

        # Append the debug log to the result if requested
        if self.config['debug']:
            if "input_list" in result:
                # Multiple inputs
                if result.get('overall_message', ''):
                    result['overall_message'] += "\n\n" + self.log_output()  # pragma: no cover
                else:
                    result['overall_message'] = self.log_output()
            else:
                # Single input
                if result.get('msg', ''):
                    result['msg'] += "\n\n" + self.log_output()
                else:
                    result['msg'] = self.log_output()

        self.format_messages(result)
        return result

    @staticmethod
    def format_messages(result):
        """Inserts HTML <br/> tags into messages where newlines are found."""

        if "input_list" in result:
            result["overall_message"] = result.get("overall_message", "").replace("\n", "<br/>\n")
            for subresult in result["input_list"]:
                subresult["msg"] = subresult.get("msg", "").replace("\n", "<br/>\n")
        else:
            result["msg"] = result.get("msg", "").replace("\n", "<br/>\n")

    def log(self, message):
        """Append a message to the debug log"""
        self.debuglog.append(message)

    def log_output(self):
        """Returns a string of the debug log output"""
        content = "\n".join(self.debuglog)
        return "<pre>{content}</pre>".format(content=content)

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
    The only other thing you may want to shadow is validate_expect, to add parsing to
    answers or transform author's answers into a standard form.

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
    Internally, an answer string will be converted into a dictionary with 'ok'=True.

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
        Defines the schema to validate an answer tuple against, used by
        config['answers'] above.

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

    @property
    def schema_answer(self):
        """Defines the schema that a fully-specified answer should satisfy."""
        return Schema({
            Required('expect'): self.validate_expect,
            Required('grade_decimal', default=1): All(numbers.Number, Range(0, 1)),
            Required('msg', default=''): str,
            Required('ok', default='computed'): Any('computed', True, False, 'partial')
        })

    @staticmethod
    def validate_expect(expect):
        """
        Defines the schema that author's answer should satisfy.

        Usually this is a just a string.
        """
        return Schema(str)(expect)

    @staticmethod
    def grade_decimal_to_ok(grade):
        """Converts a grade decimal into an 'ok' value: True, False or 'partial'"""
        return {0: False, 1: True}.get(grade, 'partial')

    @staticmethod
    def standardize_cfn_return(value):
        """
        Standardize an edX cfn return into dictionary form.

        Arguments:
            value: One of True, False, 'partial', or a dictionary with keys
                'grade_decimal' (required): number between 0 and 1
                'msg' (optional): string
        Returns:
            A dictionary with keys 'ok', 'grade_decimal', and 'msg'. The 'ok'
            value is always inferred.

        If input is True, False, or 'partial':
        >>> standardize_cfn_return = ItemGrader.standardize_cfn_return
        >>> standardize_cfn_return(True) == {
        ...     'ok': True, 'grade_decimal': 1.0, 'msg': ''
        ... }
        True
        >>> standardize_cfn_return(False) == {
        ...     'ok': False, 'grade_decimal': 0.0, 'msg': ''
        ... }
        True
        >>> standardize_cfn_return('partial') == {
        ...     'ok': 'partial', 'grade_decimal': 0.5, 'msg': ''
        ... }
        True

        If input is a dictionary with key 'grade_decimal':
        >>> standardize_cfn_return({'grade_decimal': 0.75}) == {
        ... 'ok': 'partial', 'msg': '', 'grade_decimal': 0.75
        ... }
        True

        If 'msg' is present in input dict, it is preserved:
        >>> standardize_cfn_return({'grade_decimal': 1, 'msg': 'Nice!'}) == {
        ... 'ok': True, 'msg': 'Nice!', 'grade_decimal': 1.0
        ... }
        True

        """
        if value == True:
            return {'ok': True, 'msg': '', 'grade_decimal': 1.0}
        elif isinstance(value, str) and value.lower() == 'partial':
            return {'ok': 'partial', 'msg': '', 'grade_decimal': 0.5}
        elif value == False:
            return {'ok': False, 'msg': '', 'grade_decimal': 0}

        grade_decimal = value['grade_decimal']
        ok = ItemGrader.grade_decimal_to_ok(grade_decimal)
        msg = value.get('msg', '')
        return {'ok': ok, 'msg': msg, 'grade_decimal': grade_decimal}

    def check(self, answers, student_input, **kwargs):
        """
        Compares student input to each answer in answers, using check_response.
        Computes the best outcome for the student.

        Arguments:
            answer: A tuple of answers to compare to, or None to use internal config
            student_input (str): The student's input passed by edX
            **kwargs: Anything else that has been passed in. For example, sibling
                graders when a grader is used as a subgrader in a ListGrader.
        """
        # If no answers provided, use the internal configuration
        answers = self.config['answers'] if answers is None else answers

        # answers should now be a tuple of answers
        # Check that there is at least one answer to compare to
        if not isinstance(answers, tuple):  # pragma: no cover
            msg = ("There is a problem with the author's problem configuration: "
                   "Expected answers to be a tuple of answers, instead received {}")
            raise ConfigError(msg.format(type(answers)))
        if not answers:
            msg = ("There is a problem with the author's problem configuration: "
                   "Expected at least one answer in answers")
            raise ConfigError(msg)

        # Make sure the input is in the expected format
        if not isinstance(student_input, basestring):
            msg = "Expected string for student_input, received {}"
            raise ConfigError(msg.format(type(student_input)))

        # Compute the results for each answer
        results = [self.check_response(answer, student_input, **kwargs) for answer in answers]

        # Now find the best result for the student
        best_score = max([r['grade_decimal'] for r in results])
        best_results = [r for r in results if r['grade_decimal'] == best_score]
        best_result_with_longest_msg = max(best_results, key=lambda r: len(r['msg']))

        # Add in wrong_msg if appropriate
        if best_result_with_longest_msg['msg'] == "" and best_score == 0:
            best_result_with_longest_msg['msg'] = self.config["wrong_msg"]

        return best_result_with_longest_msg

    @abc.abstractmethod
    def check_response(self, answer, student_input, **kwargs):
        """
        Compares student_input against a single answer.
        Differs from check, which must compare against all possible answers.
        This must be implemented by inheriting classes.

        Arguments:
            answer (schema_answer): The answer to compare to
            student_input (str): The student's input passed by edX
            **kwargs: Anything else that has been passed in. For example, sibling
                graders when a grader is used as a subgrader in a ListGrader.
        """
