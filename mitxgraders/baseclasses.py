"""
baseclasses.py

Contains base classes for the library:
* ObjectWithSchema
* AbstractGrader
* ItemGrader
"""
from __future__ import print_function, division, absolute_import, unicode_literals

import numbers
import abc
import pprint
import six
import json
import platform
from decimal import Decimal
from voluptuous import Schema, Required, All, Any, Range, MultipleInvalid
from voluptuous.humanize import validate_with_humanized_errors as voluptuous_validate
from mitxgraders.version import __version__
from mitxgraders.exceptions import ConfigError, MITxError, StudentFacingError
from mitxgraders.helpers.validatorfuncs import is_callable

class DefaultValuesMeta(abc.ABCMeta):
    """
    Metaclass that mixes ABCMeta behaviour and also provides a default_values parameter
    to every subclass that is NOT shared with superclasses/subclasses.
    """
    def __init__(self, name, bases, attrs):
        self.default_values = None
        super(DefaultValuesMeta, self).__init__(name, bases, attrs)

@six.add_metaclass(DefaultValuesMeta)  # This is an abstract base class with default_values
class ObjectWithSchema(object):
    """Represents an author-facing object whose configuration needs validation."""

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

    @classmethod
    def register_defaults(cls, values_dict):
        """Saves a dictionary of values to override the defaults"""
        if cls.default_values is None:
            cls.default_values = {}
        cls.default_values.update(values_dict)

    @classmethod
    def clear_registered_defaults(cls):
        """Clears all registered defaults"""
        cls.default_values = None

    def __init__(self, config=None, **kwargs):
        """
        Validate the supplied config for the object, using either a config dict or kwargs,
        but not both. Also loads any registered defaults.
        """
        # Select the appropriate source for configuration
        if config is None:
            use_config = kwargs
        else:
            use_config = config

        # Apply any registered defaults before overriding with the given configuration
        if isinstance(use_config, dict):
            use_config = self.apply_registered_defaults(use_config)

        # Coerce all strings in use_config to be unicode (both keys and values)
        use_config = ObjectWithSchema.coerce2unicode(use_config)

        # Validate the configuration
        self.config = self.validate_config(use_config)

    @staticmethod
    def coerce2unicode(obj):
        """
        Takes in an object and coerces every string
        contained in a list/dictionary/tuple key/value to unicode.

        Returns a copy of obj with coerced entries.

        Warning: this is a superficial deep copy with coercion;
        only tuples, lists, dicts and string types are recreated,
        with other references remaining intact.
        """
        if isinstance(obj, str):
            return str(obj)
        elif isinstance(obj, tuple):
            return tuple(ObjectWithSchema.coerce2unicode(item) for item in obj)
        elif isinstance(obj, list):
            return [ObjectWithSchema.coerce2unicode(item) for item in obj]
        elif isinstance(obj, dict):
            # Coerce both keys and values
            return {ObjectWithSchema.coerce2unicode(k): ObjectWithSchema.coerce2unicode(v)
                    for k, v in obj.items()}
        else:
            # obj is something else - return as is
            return obj

    def apply_registered_defaults(self, config):
        """
        Apply the registered defaults of this class and all superclasses to the
        configuration, then return the resulting configuration.
        """
        # Initialize a storage list
        config_dicts = []
        config_dicts.append(self.default_values)

        # Traverse the super classes to obtain default_values from all super classes
        current_class = self.__class__
        while True:
            # We never use multiple inheritance, so just follow the chain
            current_class = current_class.__bases__[0]
            config_dicts.append(current_class.default_values)
            if current_class == ObjectWithSchema:
                break

        # Go and apply all the default_values in reverse order
        base = {}
        config_dicts.reverse()
        for entry in config_dicts:
            if entry is not None:
                base.update(entry)

        # Report that modified defaults are being used
        self.save_modified_defaults(base)

        # Apply the provided configuration
        base.update(config)

        # Return the resulting configuration
        return base

    def save_modified_defaults(self, config):
        """
        Allows an ObjectWithSchema to save any modified defaults for later use.
        This function is intended to be shadowed as necessary.
        """
        pass

    def __repr__(self):
        """Printable representation of the object"""
        # Among other things, pprint.pformat ensures the config dict has
        # keys in alphabetical order
        pretty_config = pprint.pformat(self.config)
        return "{classname}({config})".format(classname=self.__class__.__name__,
                                              config=pretty_config)

    def __eq__(self, other):
        """
        Checks equality by checking class-equality and config equality.
        """
        return self.__class__ == other.__class__ and self.config == other.config

class AbstractGrader(ObjectWithSchema):
    """
    Abstract grader class. All graders must build on this class.

    Configuration options:
        debug (bool): Whether to add debug information to the output. Can also affect
            the types of error messages that are generated to be more technical (for
            authors) or more user-friendly (for students) (default False)

        suppress_warnings (bool): Whether to suppress warnings that the given
            configuration may lead to unintended consequences (default False)

        attempt_based_credit (None | function): Function to specify maximum credit available
            given the attempt number (function should be unary and return a number between
            0 and 1 inclusive). Set to None to disable attempt-based partial credit. This
            setting is applied to all inputs in the problem, and only needs to be set on
            the grader that is passed through to edX. (default None)

        attempt_based_credit_msg (bool): When maximum credit has been decreased due to
            attempt number, present the student with a message explaining so (default True)
    """

    @abc.abstractproperty
    def schema_config(self):
        """
        Defines the default config schema for abstract graders.
        Classes that inherit from AbstractGrader should extend this schema.
        """
        return Schema({
            Required('debug', default=False): bool,
            Required('suppress_warnings', default=False): bool,
            Required('attempt_based_credit', default=None): Any(None, is_callable),
            Required('attempt_based_credit_msg', default=True): bool
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

    log_created = False

    def create_debuglog(self, student_input):
        """
        Instantiates the debug log for the grader

        The debug log always exists and is written to, so that it can be accessed
        programmatically. It is only output with the grading when config["debug"] is True
        When subgraders are used, they need to be given access to this debuglog.
        Note that debug=True must be set on parents to obtain debug output from children
        when nested graders (lists) are used.
        """
        if self.log_created:
            # Get out if we've already initialized
            return

        self.debuglog = []
        # Add the version to the debug log
        self.log("MITx Grading Library Version " + __version__)
        self.log("Running on edX using python " + platform.python_version())
        # Add the student inputs to the debug log
        if isinstance(student_input, list):
            self.log("Student Responses:\n" + "\n".join(map(str, student_input)))
        else:
            self.log("Student Response:\n" + str(student_input))
        # Add in the modified defaults
        if self.modified_defaults:
            output = json.dumps(self.modified_defaults)
            self.log("Using modified defaults: {}".format(output))
        self.log_created = True

    def __call__(self, expect, student_input, **kwargs):
        """
        Used to ask the grading class to grade student_input.
        Used by edX as the check function (cfn).

        Arguments:
            expect: The value of edX customresponse expect attribute (often ignored)
            student_input: The student's input passed by edX
            **kwargs: Anything else that edX passes (using the "cfn_extra_args" XML tag)

        The only kwarg that can influence grading at all is 'attempt'.

        Notes:
            This function ignores the value of expect. The expect argument is
            provided because edX requires that a check function to have the
            signature above.

            Our graders usually read the author's expected answer from the
            grader configuration. This is because we generally use
            dictionaries to store the expected input along with correctness,
            grades, and feedback messages.

            Authors should still specify the <customresponse />
            expect attribute because its value is displayed to students as
            the "correct" answer.

            ItemGraders: If no answer is provided in the configuration, an
            ItemGrader will attempt to infer its answer from the expect
            parameter of a textline or CustomResponse tag. Note that this does
            not work when an ItemGrader is embedded inside a ListGrader. See
            ItemGrader.__call__ for the implementation.
        """
        student_input = self.ensure_text_inputs(student_input)

        # Initialize the debug log
        self.create_debuglog(student_input)
        # Clear the log_created flag so that a new log will be created when called again
        self.log_created = False

        # Compute the result of the check
        try:
            result = self.check(None, student_input)
        except Exception as error:
            if self.config['debug']:
                raise
            elif isinstance(error, MITxError):
                # we want to re-raise the error with a modified message but the
                # same class type, hence calling __class__
                raise error.__class__(str(error).replace('\n', '<br/>'))
            else:
                # Otherwise, give a generic error message
                if isinstance(student_input, list):
                    msg = "Invalid Input: Could not check inputs '{}'"
                    formatted = msg.format("', '".join(student_input))
                else:
                    msg = "Invalid Input: Could not check input '{}'"
                    formatted = msg.format(student_input)
                raise StudentFacingError(formatted)

        # Make sure we're only returning the relevant keys in the result.
        # List graders may use other keys to track information between nesting levels.
        keys = ['ok', 'grade_decimal', 'msg']
        if 'input_list' in result:
            # Multiple inputs
            for idx, entry in enumerate(result['input_list']):
                cleaned = {key: val for key, val in entry.items() if key in keys}
                result['input_list'][idx] = cleaned
        else:
            # Single input
            result = {key: val for key, val in result.items() if key in keys}

        # Handle partial credit based on attempt number
        if self.config['attempt_based_credit']:
            self.apply_attempt_based_credit(result, kwargs.get('attempt'))

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

    def apply_attempt_based_credit(self, result, attempt_number):
        """
        Apply attempt-based credit maximums to grading.
        Mutates result directly.
        """
        if attempt_number is None:
            msg = ("Attempt number not passed to grader as keyword argument 'attempt'. "
                   'The attribute <code>cfn_extra_args="attempt"</code> may need to be '
                   "set in the <code>customresponse</code> tag.")
            raise ConfigError(msg)

        if attempt_number < 1:  # Just in case edX has issues
            attempt_number = 1
        self.log("Attempt number {}".format(attempt_number))

        # Compute the maximum credit
        credit = self.config['attempt_based_credit'](attempt_number)
        credit = float(credit)  # In case graders return integers 0 or 1
        credit = round(credit, 4)
        if credit == 1:
            # Don't do any modifications
            return
        self.log("Maximum credit is {}".format(credit))

        # Multiply all grades by credit, updating from 'ok'=True to 'partial' as needed
        changed_result = False
        if "input_list" in result:
            for results_dict in result['input_list']:
                if results_dict['grade_decimal'] > 0:
                    grade = results_dict['grade_decimal'] * credit
                    results_dict['grade_decimal'] = grade
                    results_dict['ok'] = self.grade_decimal_to_ok(grade)
                    changed_result = True
        else:
            if result['grade_decimal'] > 0:
                grade = result['grade_decimal'] * credit
                result['grade_decimal'] = grade
                result['ok'] = self.grade_decimal_to_ok(grade)
                changed_result = True

        # Append the message if credit was reduced
        if self.config['attempt_based_credit_msg'] and changed_result:
            credit_decimal = Decimal(credit * 100).quantize(Decimal('.1'))
            if credit_decimal == int(credit_decimal):
                # Used to get rid of .0 appearing in percentages
                credit_decimal = int(credit_decimal)
            msg = "Maximum credit for attempt #{} is {}%."
            if "input_list" in result:
                key = 'overall_message'
            else:
                key = 'msg'
            if result[key]:
                result[key] += '\n\n'
            result[key] += msg.format(attempt_number, credit_decimal)

    @staticmethod
    def grade_decimal_to_ok(grade):
        """Converts a grade decimal into an 'ok' value: True, False or 'partial'"""
        return {0: False, 1: True}.get(grade, 'partial')

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

    def save_modified_defaults(self, config):
        """
        Make a copy of the modified defaults for future logging purposes.
        """
        self.modified_defaults = config.copy()

    @staticmethod
    def ensure_text_inputs(student_input, allow_lists=True, allow_single=True):
        """
        Ensures that student_input is a text string or a list of text strings,
        depending on arguments. Called by ItemGrader and ListGrader with
        appropriate arguments. Defaults are set to be friendly to user-defined
        grading classes.
        """
        # Try to perform validation
        try:
            if allow_lists and isinstance(student_input, list):
                return Schema([str])(student_input)
            elif allow_single and not isinstance(student_input, list):
                return Schema(str)(student_input)
        except MultipleInvalid as error:
            if allow_lists:
                pos = error.path[0] if error.path else None

        # The given student_input is invalid, so raise the appropriate error message
        if allow_lists and allow_single:
            msg = ("The student_input passed to a grader should be:\n"
                   " - a text string for problems with a single input box\n"
                   " - a list of text strings for problems with multiple input boxes\n"
                   "Received student_input of {}").format(type(student_input))
        elif allow_lists and not isinstance(student_input, list):
            msg = ("Expected student_input to be a list of text strings, but "
                   "received {}"
                   ).format(type(student_input))
        elif allow_lists:
            msg = ("Expected a list of text strings for student_input, but "
                   "item at position {pos} has {thetype}"
                   ).format(pos=pos, thetype=type(student_input[pos]))
        elif allow_single:
            msg = ("Expected string for student_input, received {}"
                   ).format(type(student_input))
        else:
            raise ValueError('At least one of (allow_lists, allow_single) must be True.')

        raise ConfigError(msg)

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

    def __init__(self, config=None, **kwargs):
        """
        Validate the ItemGrader's configuration, then call post-schema validation.
        """
        super(ItemGrader, self).__init__(config, **kwargs)
        self.config['answers'] = self.post_schema_ans_val(self.config['answers'])

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

    def post_schema_ans_val(self, answer_tuple):
        """
        Perform any post-schema validation on the answer tuple. This function should be
        idempotent, as it may be called on a configuration multiple times.

        Any post-schema validation that doesn't work with the answer tuple should be
        handled in a shadowed __init__ function. The reason this function is invoked
        separately is so that it can also be called on inferred answers.

        Returns the validated answer_tuple.

        This function exists to be shadowed.
        """
        return answer_tuple

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
            Required('expect'): self.validate_expect_tuple,
            Required('grade_decimal', default=1): All(numbers.Number, Range(0, 1)),
            Required('msg', default=''): str,
            Required('ok', default='computed'): Any('computed', True, False, 'partial')
        })

    def validate_expect_tuple(self, expect):
        """
        Defines the schema that a fully-specified expect entry should satisfy.
        Note that it coerces expect to a tuple if it isn't already.
        """
        if not isinstance(expect, tuple):
            expect = (expect, )
        return Schema((self.validate_expect,))(expect)

    @staticmethod
    def validate_expect(expect):
        """
        Defines the schema that author's answer should satisfy.

        Usually this is a just a string.
        """
        return Schema(str)(expect)

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

        # Compute the results for each answer
        results = []
        for answer in answers:
            # Iterate through each entry in the expect tuple
            answercopy = answer.copy()
            for entry in answer['expect']:
                answercopy['expect'] = entry
                result = self.check_response(answercopy, student_input, **kwargs)
                results.append(result)

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

    inferring_answers = False

    def __call__(self, expect, student_input, **kwargs):
        """
        The same as AbstractGrader.__call__, except that we try to infer
        answers from expect argument if answers are not specified in the
        grader configuration. The actual inference is done by infer_from_expect,
        which can be shadowed.
        """
        # If expect is provided, infer an answer if we either don't have an answer or
        # are always inferring answers
        if expect is not None and (self.inferring_answers or not self.config['answers']):
            inferred = self.infer_from_expect(expect)

            # Create the debug log...
            self.create_debuglog(student_input)
            # ... so that we can add the inferred answers to it before
            # calling AbstractGrader.__call__
            output = json.dumps(inferred)  # How to avoid unicode 'u' showing up!
            self.log("Expect value inferred to be {}".format(output))

            # Validate the answers
            self.config['answers'] = self.schema_answers(inferred)
            # Note that this answer is now stored for future calls, but
            # will be overridden if a new expect value is provided.

            # Perform post-schema answer validation
            self.config['answers'] = self.post_schema_ans_val(self.config['answers'])

            # Mark that we are using inferred answers
            self.inferring_answers = True

        # And punt the actual __call__ function to the superclass
        return super(ItemGrader, self).__call__(expect, student_input, **kwargs)

    def infer_from_expect(self, expect):
        """
        Infer the answer from the expect parameter and return it. For most purposes,
        the answer is just the expect parameter. However, this can be shadowed if need be.

        If you create a grader that cannot infer from expect, shadow this function, and
        simply raise ConfigError('Answer cannot be inferred for this grader')
        """
        return expect

    @staticmethod
    def ensure_text_inputs(student_input):
        return super(ItemGrader, ItemGrader).ensure_text_inputs(student_input, allow_lists=False)
