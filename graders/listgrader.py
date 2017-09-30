"""
ListGrader class

This class is responsible for grading anything that contains multiple inputs.
Also deals with delimiter-separated inputs within a single input box.

Works by farming out the individual objects to other graders.
"""
from __future__ import division
from graders.helpers import munkres
from graders.voluptuous import Schema, Required, Any
from graders.voluptuous.humanize import validate_with_humanized_errors as voluptuous_validate
from graders.baseclasses import AbstractGrader, ItemGrader

# Set the objects to be imported from this grader
__all__ = [
    "ListGrader",
    "ConfigError"
]

class ConfigError(Exception):
    """Raised whenever a configuration error occurs"""
    pass

class _AutomaticFailure(object):  # pylint: disable=too-few-public-methods
    """Used as padding when grading unknown number of inputs on a single input line"""
    pass

class ListGrader(AbstractGrader):
    """
    TODO This docstring is outdated and should be updated once ListGrader conforms
    to the specifications.

    Grades Lists of items according to a specified subgrader, unordered by default.

    ListGrader can be used to grade a list of answers according to the
    supplied subgrader. Works with either multi-input customresponse
    or single-input customresponse.

    How learners enter lists in customresponse
    ==========================================

    Multi-input customresponse:
        <customresmse cfn="grader">
            <textline/> <!-- learner enters cat -->
            <textline/> <!-- learner enters dog -->
            <textline/> <!-- learner leaves blank -->
        </customresmse>
        Notes:
            grader receives a list: ['cat', 'dog', None]
            list will always contain exactly as many items as input tags

    Single-input customresponse:
        <customresmse cfn="grader">
            <textline/> <!-- learner enters 'cat, dog, fish, rabbit' -->
        </customresmse>
        Notes:
            learner is responsible for entering item delimiter (here: ',')
            grader receives a string: 'cat, dog, fish, rabbit'
            learner might enter fewer or more items than author expects

    Basic Usage
    ===========

    Grade a list of strings (multi-input)
        >>> from stringgrader import StringGrader
        >>> grader = ListGrader({
        ...     'answers':['cat', 'dog', 'fish'],
        ...     'subgrader': StringGrader(),
        ...     'length_error': False
        ... })
        >>> result = grader(None, ['fish', 'cat', 'moose'])
        >>> expected = {'input_list':[
        ...     {'ok': True, 'grade_decimal':1, 'msg':''},
        ...     {'ok': True, 'grade_decimal':1, 'msg':''},
        ...     {'ok': False, 'grade_decimal':0, 'msg':''}
        ... ], 'overall_message':''}
        >>> result == expected
        True

    Grade a string of comma-separated items through the same API:
        >>> result = grader(None, "cat, fish, moose")
        >>> expected = {'ok':'partial', 'grade_decimal':2/3, 'msg': '' }
        >>> result == expected
        True

    Extra items reduce score:
        >>> result = grader(None, "cat, fish, moose, rabbit")
        >>> expected = {'ok':'partial', 'grade_decimal':1/3, 'msg': '' }
        >>> result == expected
        True

    but not below zero:
        >>> result = grader(None, "cat, fish, moose, rabbit, bear, lion")
        >>> expected = {'ok':False, 'grade_decimal':0, 'msg': '' }
        >>> result == expected
        True

    Optionally, make order matter:
        >>> ordered_grader = ListGrader({
        ...     'answers':['cat', 'dog', 'fish'],
        ...     'subgrader': StringGrader(),
        ...     'ordered': True
        ... })
        >>> result = ordered_grader(None, "cat, fish, moose")
        >>> expected = {'ok':'partial', 'grade_decimal':1/3, 'msg': '' }
        >>> result == expected
        True

    Optionally, change the delimiter for single-input:
        >>> semicolon_grader = ListGrader({
        ...     'delimiter': ';',
        ...     'answers':['cat', 'dog', 'fish'],
        ...     'subgrader': StringGrader()
        ... })
        >>> result = semicolon_grader(None, "cat; fish; moose")
        >>> expected = {'ok':'partial', 'grade_decimal':2/3, 'msg': '' }
        >>> result == expected
        True
    """

    # The voluptuous Schema object to validate ListGrader configurations
    schema_config = Schema({
            Required('ordered', default=False): bool,
            Required('length_error', default=True): bool,
            Required('delimiter', default=','): str,
            Required('subgrader'): Any(ItemGrader, [ItemGrader]),
            Required('answers', default=[]): list
        })

    def __init__(self, config=None):
        """
        Validate the ListGrader's configuration.
        This is a bit different from other graders, because the validation of the answers
        depends on the subgrader items in the config. Hence, we validate in three steps:
        0. subgrader classes are initialized and checked before this class is initialized.
           No answers are checked in this part.
        1. Validate the config for this class, checking that answers is a list
        2. Validate the answers by passing them into the subgrader classes.
        """
        # Step 1: Validate the configuration of this list using the usual routines
        super(ListGrader, self).__init__(config)

        # Step 2: Validate the answers using the subgrader items
        answers = self.config['answers']  # reference to the list of answers
        if len(answers) == 1:
            raise ConfigError('ListGrader does not work with a single answer')

        if isinstance(self.config['subgrader'], list):
            # We have a list of subgraders
            self.subgrader_list = True
            # First, ensure that multiple subgraders are valid
            subgraders = self.config['subgrader']
            if len(subgraders) != len(self.config['answers']):
                raise ConfigError('The number of subgraders and answers are different')
            if not self.config['ordered']:
                raise ConfigError('Cannot use unordered lists with multiple graders')
            # Next, validate the answers using the subgraders
            for index, answer in enumerate(answers):
                answers[index] = subgraders[index].schema_answers(answer)
        else:
            # We have a single subgrader
            self.subgrader_list = False
            # Use it to validate all of the answers
            subgrader = self.config['subgrader']
            for index, answer in enumerate(answers):
                answers[index] = subgrader.schema_answers(answer)

    def check(self, answers, student_input):
        """Checks student_input against answers."""
        answers = self.config['answers']
        if isinstance(student_input, list):
            return self.multi_check(answers, student_input)
        elif isinstance(student_input, basestring):
            return self.single_check(answers, student_input)
        else:
            msg = "Expected answer to have type <type list>, <type string> " + \
                  "or <type unicode>, but received {t}"
            raise ValueError(msg.format(t=type(student_input)))

    def multi_check(self, answers, student_list):
        """
        Delegated to by ListGrader.check when student_input is a list.
        I.e., when customresponse contains multiple inputs.
        """
        answers = self.config['answers'] if answers is None else answers

        if len(answers) != len(student_list):
            msg = "The number of answers ({}) and the number of inputs ({}) are different"
            raise ConfigError(msg.format(len(answers), len(student_list)))

        if self.config['ordered']:
            compare = zip(answers, student_list)
            if self.subgrader_list:
                input_list = [self.config['subgrader'][index].check(*pair) for index, pair in enumerate(compare)]
            else:
                input_list = [self.config['subgrader'].check(*pair) for pair in compare]
        else:
            input_list = self.find_optimal_order(self.config['subgrader'].check, answers, student_list)

        return {'input_list': input_list, 'overall_message': ''}

    def single_check(self, answers, student_input):
        """
        Delegated to by ListGrader.check when student_input is a string.
        I.e., when customresponse contains a single input.
        """
        # First, check that we have a single subgrader
        if self.subgrader_list:
            raise ConfigError("Multiple subgraders cannot be used for single input lists")

        answers = self.config['answers'] if answers is None else answers
        student_list = student_input.split(self.config['delimiter'])

        if self.config['length_error'] and len(answers) != len(student_list):
            msg = 'List length error: Expected {} terms in the list, but received {}'
            raise ValueError(msg.format(len(answers), len(student_list)))

        if self.config['ordered']:
            input_list = [self.config['subgrader'].check(*pair) for pair in zip(answers, student_list)]
        else:
            input_list = self.padded_find_optimal_order(self.config['subgrader'].check, answers, student_list)

        grade_decimals = [g['grade_decimal'] for g in input_list]
        grade_decimal = self.calculate_single_grade(grade_decimals, len(answers))
        ok_status = ItemGrader.grade_decimal_to_ok(grade_decimal)

        result = {
            'grade_decimal': grade_decimal,
            'ok': ok_status,
            'msg': '\n'.join([result['msg'] for result in input_list if result['msg'] != ''])
        }

        return result

    @staticmethod
    def find_optimal_order(check, answers, student_input_list):
        """
        Finds optimal assignment (according to check) of inputs to answers.

        Inputs:
            answers (list): A list [answers_0, answers_1, ...]
                wherein each answers_i is a valid ItemGrader.config['answers']
            student_input_list (list): a list of student inputs

        Returns:
            A re-ordered input_list to optimally match answers.

        NOTE:
            uses https://github.com/bmc/munkres
            to solve https://en.wikipedia.org/wiki/Assignment_problem
        """
        result_matrix = [[check(a, i) for a in answers] for i in student_input_list]
        cost_matrix = munkres.make_cost_matrix(result_matrix, lambda r: 1 - r['grade_decimal'])
        indexes = munkres.Munkres().compute(cost_matrix)

        input_list = [result_matrix[i][j] for i, j in indexes]
        return input_list

    @staticmethod
    def padded_find_optimal_order(check, answers, student_list):
        """
        Same as find_optimal_order, but keeps track of missing and extra answers.

        Idea is:
            use _AutomaticFailure to pad expect and answers to equal length
            modify check to reject _AutomaticFailure
        """
        if len(answers) == len(student_list):
            return ListGrader.find_optimal_order(check, answers, student_list)

        maxlen = max(len(answers), len(student_list))
        padded_answers = answers + [_AutomaticFailure()]*(maxlen-len(answers))
        padded_student_list = student_list + [_AutomaticFailure()]*(maxlen-len(student_list))

        def _check(ans, inp):
            if isinstance(ans, _AutomaticFailure) or isinstance(inp, _AutomaticFailure):
                return {'ok': False, 'msg': '', 'grade_decimal': 0}
            return check(ans, inp)

        return ListGrader.find_optimal_order(_check, padded_answers, padded_student_list)

    @staticmethod
    def calculate_single_grade(grade_decimals, n_expect):
        """Consolidate several grade_decimals into one.

        Arguments:
            grade_decimals (list): A list of floats between 0 and 1
            n_expect (int): expected number of answers
        Returns:
            float, either:
                average of grade_decimals padded to length n_extra if
                    necessary, and subtracting 1/n_extra for each extra, or
                zero
            whichever is larger.

        Usage:
            >>> ListGrader.calculate_single_grade([1, 0, 0.5], 4)
            0.375
            >>> ListGrader.calculate_single_grade([1, 0.5, 0], 2)
            0.25
            >>> ListGrader.calculate_single_grade([1, 0.5, 0, 0, 0], 2)
            0
        """
        n_extra = len(grade_decimals) - n_expect
        if n_extra > 0:
            grade_decimals += [-1] * n_extra
        elif n_extra < 0:
            grade_decimals += [0] * abs(n_extra)

        avg = sum(grade_decimals)/n_expect

        return max(0, avg)
