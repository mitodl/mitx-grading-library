"""
ListGrader class

This class is responsible for grading anything that contains multiple inputs.
Also deals with delimiter-separated inputs within a single input box.

Works by farming out the individual objects to other graders.
"""
from __future__ import division
import numpy as np
from graders.helpers import munkres
from graders.voluptuous import Schema, Required, Any
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
        Required('subgrader'): Any(AbstractGrader, [AbstractGrader]),
        Required('answers', default=[]): Any(list, (list,))  # Allow for a tuple of lists
    })

    def __init__(self, config=None):
        """
        Validate the ListGrader's configuration.
        This is a bit different from other graders, because the validation of the answers
        depends on the subgrader items in the config. Hence, we validate in three steps:
        0. Subgrader classes are initialized and checked before this class is initialized
        1. Validate the config for this class, checking that answers is a list
        2. Validate the answers by using the subgrader classes
        """
        # Step 1: Validate the configuration of this list using the usual routines
        super(ListGrader, self).__init__(config)

        # Step 2: Validate the answers
        self.config['answers'] = self.schema_answers(self.config['answers'])

    def schema_answers(self, answers_tuple):
        """
        Defines the schema to validate an answer tuple against.

        This will transform the input to a tuple as necessary, and then attempt to
        validate the answers_tuple using the defined subgraders.

        Two forms for the answer tuple are acceptable:

        1. A list of answers
        2. A tuple of lists of answers
        """
        # Turn answers_tuple into a tuple if it isn't already
        if isinstance(answers_tuple, list):
            if len(answers_tuple) == 1:
                raise ConfigError('ListGrader does not work with a single answer')
            elif not answers_tuple:  # empty list
                # Nothing further to check here. This must be a nested grader, which will
                # be called upon to check answers again a bit later.
                return tuple()
            answers_tuple = (answers_tuple,)
        elif not isinstance(answers_tuple, tuple):
            # Should not get here; voluptuous should catch this beforehand
            raise ConfigError("Answer list must be a list or a tuple of lists")

        # Check that all lists in the tuple have the same length
        for answer_list in answers_tuple:
            if len(answer_list) != len(answers_tuple[0]):
                raise ConfigError("All possible list answers must have the same length")

        # Check that the subgraders are commensurate with the answers
        if isinstance(self.config['subgrader'], list):
            # We have a list of subgraders
            self.subgrader_list = True
            subgraders = self.config['subgrader']

            # Ensure that multiple subgraders are valid
            if len(subgraders) != len(answers_tuple[0]):
                raise ConfigError('The number of subgraders and answers are different')
            if not self.config['ordered']:
                raise ConfigError('Cannot use unordered lists with multiple graders')

            # Validate answer_list using the subgraders
            for answer_list in answers_tuple:
                for index, answer in enumerate(answer_list):
                    answer_list[index] = subgraders[index].schema_answers(answer)
        else:
            # We have a single subgrader
            self.subgrader_list = False
            subgrader = self.config['subgrader']

            # Validate answer_list using the subgraders
            for answer_list in answers_tuple:
                for index, answer in enumerate(answer_list):
                    answer_list[index] = subgrader.schema_answers(answer)

        return answers_tuple

    def check(self, answers, student_input):
        """Checks student_input against answers, which may be provided"""
        # If no answers provided, use the internal configuration
        answers = self.config['answers'] if answers is None else answers

        # answers should now be a tuple of answers
        # Check that there is at least one answer to compare to
        if not answers:
            raise ConfigError("Expected at least one answer in answers")
        if not isinstance(answers, tuple):
            msg = "Expected answers to be a tuple of answers, instead received {0}"
            raise ConfigError(msg.format(type(answers)))

        # Go and grade the responses
        if isinstance(student_input, list):
            # Compute the results for each answer
            results = [self.multi_check(answer_list, student_input) for answer_list in answers]
            return self.get_best_multi_result(results)
        elif isinstance(student_input, basestring):
            # Compute the results for each answer
            results = [self.single_check(answer_list, student_input) for answer_list in answers]
            return self.get_best_single_result(results)
        else:
            msg = "Expected answer to have type <type list>, <type string> " + \
                  "or <type unicode>, but received {t}"
            raise ConfigError(msg.format(t=type(student_input)))

    @staticmethod
    def get_best_multi_result(results):
        """Compute the best result from a multi-input problem"""
        # If we had a single list of answers, just return the results
        if len(results) == 1:
            return results[0]

        # Start by constructing a list of all the grades: question, result_number
        full_grades = np.zeros([len(results), len(results[0]['input_list'])])
        for index, result in enumerate(results):
            for qnum, grade in enumerate(result['input_list']):
                full_grades[index, qnum] = grade['grade_decimal']

        # Find the best scores
        scores = full_grades.sum(axis=1)
        max_score = np.max(scores)
        best_results = np.where(scores == max_score)[0]

        # best_results is now an array containing the indices of the results that score
        # the best. If there's only one best, return it
        if len(best_results) == 1:
            return results[best_results[0]]

        # To choose between the remaining bests, pick out the scores from the leaders
        culled_grades = full_grades[best_results].T
        culled_results = [result for index, result in enumerate(results) if index in best_results]

        # Find which of the culled results did best at each input
        max_vals = np.amax(culled_grades, axis=1)
        max_vals = np.array([max_vals]).T
        high_scoring = culled_grades == max_vals
        # high_scoring is a matrix the same shape as full_grades
        # It stores True/False values for whether that result was the best for that input

        # Run through the culled_grades matrix to figure out which results are still in
        # the running after each input
        in_the_running = np.array([True] * len(high_scoring))
        for scores in culled_grades:
            # Cull the list
            test_cull = np.logical_and(in_the_running, scores)
            if np.count_nonzero(test_cull) == 0:
                # Results that were already knocked out scored well here. Ignore
                continue
            in_the_running = test_cull
            if np.count_nonzero(in_the_running) == 1:
                # Return the winner!
                index = np.where(in_the_running)[0][0]
                return culled_results[index]

        # Everything is exactly the same, possibly excepting messages.
        # Just return the first result in our remaining list.
        return culled_results[np.where(in_the_running)[0][0]]

    @staticmethod
    def get_best_single_result(results):
        """Compute the best result from a single-input problem"""
        # If we had a single list of answers, just return the results
        if len(results) == 1:
            return results[0]

        # Compute the best result for the student in the same way ItemGrader does
        best_score = max([r['grade_decimal'] for r in results])
        best_results = [r for r in results if r['grade_decimal'] == best_score]
        best_result_with_longest_msg = max(best_results, key=lambda r: len(r['msg']))
        return best_result_with_longest_msg

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

        # TODO: If a subgrader was a ListGrader, we need to flatten the response

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
