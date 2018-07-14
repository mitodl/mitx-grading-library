"""
listgrader.py

Classes for grading inputs that look like lists:
* ListGrader (multiple inputs)
* SingleListGrader (delimiter-separated list in a single input)

Both work by farming out the individual objects to other graders.
"""
from __future__ import division
import numpy as np
from voluptuous import Required, Any
from mitxgraders.helpers import munkres
from mitxgraders.baseclasses import AbstractGrader, ItemGrader
from mitxgraders.exceptions import ConfigError, MissingInput
from mitxgraders.helpers.validatorfuncs import Positive

# Set the objects to be imported from this grader
__all__ = [
    "ListGrader",
    "SingleListGrader"
]

class _AutomaticFailure(object):  # pylint: disable=too-few-public-methods
    """Used as padding when grading unknown number of inputs on a single input line"""
    pass

def find_optimal_order(check, answers, student_list):
    """
    Finds optimal assignment (according to check function) of inputs to answers.

    Arguments:
        answers (list): A list [answers_0, answers_1, ...]
            wherein each answers_i is a valid ItemGrader.config['answers']
        student_list (list): a list of student inputs

    Returns:
        An optimally-grader input_list whose dictionaries match student_list in order.

    NOTE:
        uses https://github.com/bmc/munkres
        to solve https://en.wikipedia.org/wiki/Assignment_problem
    """
    result_matrix = [[check(a, i) for a in answers] for i in student_list]


    def calculate_cost(result):
        """
        The result matrix could contain short-form or long-form result dictionaries.
        If long-form, we need to consolidate grades.
        Either way, Munkres wants a cost matrix
        """
        if 'input_list' in result:
            grades = [r['grade_decimal'] for r in result['input_list']]
            result['grade_decimal'] = consolidate_grades(grades)
        return 1 - result['grade_decimal']

    cost_matrix = munkres.make_cost_matrix(result_matrix, calculate_cost)
    indexes = munkres.Munkres().compute(cost_matrix)

    input_list = [result_matrix[i][j] for i, j in indexes]
    return input_list

def get_padded_lists(list1, list2):
    """
    Pads the shorter of list1 and list2 and returns copies of both
    """
    maxlen = max(len(list1), len(list2))
    padded1 = list1 + [_AutomaticFailure()]*(maxlen-len(list1))
    padded2 = list2 + [_AutomaticFailure()]*(maxlen-len(list2))

    return padded1, padded2

def padded_check(check):
    """Wraps a check function to reject _AutomaticFailure"""
    def _check(ans, inp):
        if isinstance(ans, _AutomaticFailure) or isinstance(inp, _AutomaticFailure):
            return {'ok': False, 'msg': '', 'grade_decimal': 0}
        return check(ans, inp)
    return _check

def consolidate_grades(grade_decimals, n_expect=None):
    """
    Consolidate several grade_decimals into one.

    Arguments:
        grade_decimals (list): A list of floats between 0 and 1
        n_expect (int): expected number of answers, defaults to length of grade_decimals
    Returns:
        float, either:
            average of grade_decimals padded to length n_extra if
                necessary, and subtracting 1/n_extra for each extra, or
            zero
        whichever is larger.

    Usage:
        >>> consolidate_grades([1, 0, 0.5], 4)
        0.375
        >>> consolidate_grades([1, 0.5, 0], 2)
        0.25
        >>> consolidate_grades([1, 0.5, 0, 0, 0], 2)
        0
    """
    if n_expect is None:
        n_expect = len(grade_decimals)

    n_extra = len(grade_decimals) - n_expect
    if n_extra > 0:
        grade_decimals += [-1] * n_extra
    elif n_extra < 0:
        grade_decimals += [0] * abs(n_extra)

    avg = sum(grade_decimals)/n_expect

    return max(0, avg)

def consolidate_cfn_return(input_list, overall_message="", n_expect=None, partial_credit=True):
    """
    Consolidates a long-form customresponse return dictionary.

    Arguments:
        input_list (list): a list of customresponse single-answer dictionaries
            each has keys 'ok', 'grade_decimal', 'msg'
        overall_message (str): an overall message
        n_expect: The expected number of answers, defaults to len(input_list).
            Used in assigning partial credit.

    Usage
    =====
    >>> input_list = [
    ...     {'ok': True, 'msg': 'msg_0', 'grade_decimal':1},
    ...     {'ok': 'partial', 'msg': 'msg_1', 'grade_decimal':0.5},
    ...     {'ok': False, 'msg': 'msg_2', 'grade_decimal':0},
    ...     {'ok': 'partial', 'msg': 'msg_3', 'grade_decimal':0.1},
    ... ]
    >>> expect = {
    ...     'ok':'partial',
    ...     'grade_decimal': (1 + 0.5 + 0 + 0.1)/4,
    ...     'msg': 'summary\\nmsg_0\\nmsg_1\\nmsg_2\\nmsg_3' # escape newlines in docstring
    ... }
    >>> result = consolidate_cfn_return(input_list,
    ...     overall_message = "summary"
    ... )
    >>> expect == result
    True
    """
    if n_expect is None:
        n_expect = len(input_list)

    grade_decimals = [result['grade_decimal'] for result in input_list]
    grade_decimal = consolidate_grades(grade_decimals, n_expect)
    if not partial_credit:
        if grade_decimal < 1:
            grade_decimal = 0
    ok_status = ItemGrader.grade_decimal_to_ok(grade_decimal)

    # TODO Discuss: Do we want the overall_message to go first or last?
    messages = [overall_message] + [result['msg'] for result in input_list]

    result = {
        'grade_decimal': grade_decimal,
        'ok': ok_status,
        'msg': '\n'.join([message for message in messages if message != ''])
    }

    return result

class ListGrader(AbstractGrader):
    """
    ListGrader grades lists of items according to a specified subgrader or list of
    subgraders. It works with multi-input customresponse problems.

    Multi-input customresponse:
        <customresponse cfn="grader">
            <textline/> <!-- learner enters cat -->
            <textline/> <!-- learner enters dog -->
            <textline/> <!-- learner leaves blank -->
        </customresponse>
        Notes:
            grader receives a list: ['cat', 'dog', None]
            The list will always contain exactly as many items as input tags

    Configuration options:
        ordered (bool): Whether or not the entries should be in the correct order
            (default False)

        subgraders (AbstractGrader): A grader or a list of graders to use in grading the
            individual entries (required)

        grouping ([int]): The way to group together inputs when using nested ListGrader
            classes. See documentation. (default [])

        answers (list, tuple of lists): The list of answers, or a tuple of lists of answers
            if multiple "correct lists" are available. Each individual answer must conform
            to the appropriate answer schema for the subgrader. The default is [], as an
            empty list is allowable if SingleListGrader is being used as a subgrader.
    """

    @property
    def schema_config(self):
        """Define the configuration options for ListGrader"""
        # Construct the default AbstractGrader schema
        schema = super(ListGrader, self).schema_config
        # Append options
        return schema.extend({
            Required('ordered', default=False): bool,
            Required('subgraders'): Any(AbstractGrader, [AbstractGrader]),
            Required('grouping', default=[]): [Positive(int)],
            Required('answers', default=[]): Any(list, (list,))  # Allow for a tuple of lists
        })

    def __init__(self, config=None, **kwargs):
        """
        Validate the ListGrader's configuration.
        This is a bit different from other graders, because the validation of the answers
        depends on the subgrader items in the config. Hence, we validate in a few steps:
        0. Subgrader classes are initialized and checked before this class is initialized
        1. Validate the config for this class, checking that answers is a list
        2. Validate the answers by using the subgrader classes
        3. Validate the grouping
        """
        # Step 1: Validate the configuration of this list using the usual routines
        super(ListGrader, self).__init__(config, **kwargs)

        # Step 2: Validate the answers
        self.subgrader_list = isinstance(self.config['subgraders'], list)
        self.config['answers'] = self.schema_answers(self.config['answers'])

        # Step 3: Validate the grouping
        if self.config['grouping']:
            # Create the grouping map
            self.grouping = self.create_grouping_map(self.config['grouping'])
            self.validate_grouping()
        else:
            self.grouping = None

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
        elif not isinstance(answers_tuple, tuple):  # pragma: no cover
            # Should not get here; voluptuous should catch this beforehand
            raise ConfigError("Answer list must be a list or a tuple of lists")

        # Check that all lists in the tuple have the same length
        for answer_list in answers_tuple:
            if len(answer_list) != len(answers_tuple[0]):
                raise ConfigError("All possible list answers must have the same length")

        # Check that the subgraders are commensurate with the answers
        if self.subgrader_list:
            # We have a list of subgraders
            subgraders = self.config['subgraders']

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
            subgrader = self.config['subgraders']

            # Validate answer_list using the subgraders
            for answer_list in answers_tuple:
                for index, answer in enumerate(answer_list):
                    answer_list[index] = subgrader.schema_answers(answer)

        return answers_tuple

    @staticmethod
    def create_grouping_map(grouping):
        """Creates an array mapping groups to input index

        Usage
        =====
        >>> grouping = [3, 1, 1, 2, 2, 1, 2]
        >>> expect = [
        ...     [1, 2, 5],
        ...     [3, 4, 6],
        ...     [0]
        ... ]
        >>> expect == ListGrader.create_grouping_map(grouping)
        True
        """
        # Validate the list of groups
        group_nums = set(grouping)
        if not group_nums == set(range(1, max(group_nums) + 1)):
            msg = "Grouping should be a list of contiguous positive integers starting at 1."
            raise ConfigError(msg)

        # Create the grouping map
        group_map = [[] for group in group_nums]
        for index, group_num in enumerate(grouping):
            group_map[group_num - 1].append(index)

        return group_map

    def validate_grouping(self):
        """Validate a grouping list"""
        # Single subgraders must be a ListGrader
        if not self.subgrader_list and not isinstance(self.config['subgraders'], ListGrader):
            msg = "A ListGrader with groupings must have a ListGrader subgrader " + \
                  "or a list of subgraders"
            raise ConfigError(msg)

        # Unordered, each group must have the same number of entries
        if not self.config['ordered']:
            group_len = len(self.grouping[0])
            for group in self.grouping:
                if len(group) != group_len:
                    raise ConfigError("Groups must all be the same length when unordered")

        # If using multiple subgraders, make sure we have the right number of subgraders
        if self.subgrader_list:
            if len(self.grouping) != len(self.config['subgraders']):
                raise ConfigError("Number of subgraders and number of groups are not equal")
            # Furthermore, lists (groups with more than one entry) must go to ListGraders
            for py_idx, group in enumerate(self.grouping):
                group_idx = py_idx + 1
                num_items = len(group)
                subgrader = self.config['subgraders'][py_idx]
                if num_items > 1 and not isinstance(subgrader, ListGrader):
                    msg = "Grouping index {} has {} items, but has a {} subgrader " + \
                          "instead of ListGrader"
                    raise ConfigError(msg.format(group_idx, num_items, type(subgrader).__name__))

    def check(self, answers, student_input, **kwargs):
        """Checks student_input against answers, which may be provided"""
        # If no answers provided, use the internal configuration
        answers = self.config['answers'] if answers is None else answers

        # answers should now be a tuple of answers
        # Check that there is at least one answer to compare to
        if not isinstance(answers, tuple):  # pragma: no cover
            msg = "Expected answers to be a tuple of answers, instead received {}"
            raise ConfigError(msg.format(type(answers)))
        if not answers:
            raise ConfigError("Expected at least one answer in answers")

        # Pass our debuglog to the subgraders, so that any that have debug=True can use it
        if self.subgrader_list:
            for subgrader in self.config['subgraders']:
                subgrader.debuglog = self.debuglog
        else:
            self.config['subgraders'].debuglog = self.debuglog

        # Go and grade the responses
        if isinstance(student_input, list):
            # Compute the results for each answer
            results = [self.perform_check(answer_list, student_input) for answer_list in answers]
            return self.get_best_result(results)
        else:
            msg = "Expected answer to have type <type list>, but received {}"
            raise ConfigError(msg.format(type(student_input)))

    @staticmethod
    def groupify_list(grouping, thelist):
        """
        Group inputs in student_list according to grouping

        Arguments:
            grouping (list): an array whose entries are lists of indices in original list
            thelist (list): the list to be groupified

        Usage
        =====
        >>> grouping = [[1, 2, 5], [3, 4, 6], [0]]
        >>> student_input = ['a', 'b', 'c', 'd', 'e', 'f', 'g']
        >>> expected = [
        ...     ['b', 'c', 'f'],
        ...     ['d', 'e', 'g'],
        ...     'a'
        ... ]
        >>> result = ListGrader.groupify_list(grouping, student_input)
        >>> result == expected
        True
        """
        if grouping is None:
            return thelist
        result = [
            thelist[group[0]] if len(group) == 1 else [thelist[idx] for idx in group]
            for group in grouping
        ]
        return result

    @staticmethod
    def ungroupify_list(grouping, grouped_list):
        """
        Inverse of groupify_list.

        Usage
        =====
        >>> grouping = [[1, 2, 5], [3, 4, 6], [0]]
        >>> student_input = ['a', 'b', 'c', 'd', 'e', 'f', 'g']
        >>> expected_grouped = [
        ...     ['b', 'c', 'f'],
        ...     ['d', 'e', 'g'],
        ...     'a'
        ... ]
        >>> grouped = ListGrader.groupify_list(grouping, student_input)
        >>> grouped == expected_grouped
        True
        >>> ungrouped = ListGrader.ungroupify_list(grouping, grouped)
        >>> ungrouped == student_input
        True
        """
        if grouping is None:
            return grouped_list

        # Get the maximum index we're going to need
        length = max([item for row in grouping for item in row]) + 1
        # Initialize the output list
        ungrouped = [None for _ in range(length)]

        for indices, items in zip(grouping, grouped_list):
            items = [items] if len(indices) == 1 else items
            for idx, item in zip(indices, items):
                ungrouped[idx] = item
        return ungrouped

    def validate_submission(self, answers, student_list):
        """
        Make sure that the student_list has the right number of entries.
        Compares to both grouping and answers.
        """
        if self.config['grouping']:
            if len(self.config['grouping']) != len(student_list):
                msg = "Grouping indicates {} inputs are expected, but only {} inputs exist."
                raise ConfigError(msg.format(len(self.config['grouping']), len(student_list)))
        else:
            if len(answers) != len(student_list):
                msg = "The number of answers ({}) and the number of inputs ({}) are different"
                raise ConfigError(msg.format(len(answers), len(student_list)))

    def get_ordered_input_list(self, answers, grouped_inputs):
        """
        Pass answers and inputs to the appropriate grader, along with sibling
        information.
        """
        # If 'subgraders' is a single grader, create a list of references to it.
        graders = (self.config['subgraders'] if self.subgrader_list
                   else [self.config['subgraders'] for _ in answers])
        compare = zip(graders, answers, grouped_inputs)
        siblings = [
            {'grader': grader, 'input': theinput}
            for grader, _, theinput in compare
            ]

        input_list = [
            grader.check(answer, theinput, siblings=siblings)
            for (grader, answer, theinput) in compare
        ]

        return input_list

    def perform_check(self, answers, student_list):
        """
        Compare the list of responses from a student against a specific list of answers.
        """
        self.validate_submission(answers, student_list)

        # Group the inputs in preparation for grading
        grouped_inputs = self.groupify_list(self.grouping, student_list)
        if self.config['ordered']:
            input_list = self.get_ordered_input_list(answers, grouped_inputs)
        else:
            # If unordered, then there is a single subgrader. Find optimal grading.
            input_list = find_optimal_order(self.config['subgraders'].check,
                                            answers,
                                            grouped_inputs)

        # We need to restore the original order of inputs.
        # At this point, input_list contains items each of which is either:
        #   1. short-form item results {'ok':..., 'msg': ..., 'grade_decimal': ...}
        #   2. long-form list results {'overall_message':..., 'input_list': ...}
        # Let's change to a nested list of short-results, then ungroup
        nested = [
            r['input_list'] if 'input_list' in r else r
            for r in input_list
        ]
        ungrouped = self.ungroupify_list(self.grouping, nested)

        # TODO We're discarding any overall_messages at this point. We should
        # combine them to form the resulting overall_message

        return {'input_list': ungrouped, 'overall_message': ''}

    @staticmethod
    def get_best_result(results):
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

class SingleListGrader(ItemGrader):
    """
    Grades lists of items in a single input box according to a specified subgrader.

    Note that this is an ItemGrader, but has similar behavior to ListGrader.

    Single-input customresponse:
        <customresponse cfn="grader">
            <textline/> <!-- learner enters 'cat, dog, fish, rabbit' -->
        </customresponse>
        Notes:
            learner is responsible for entering item delimiter (here: ',')
            grader receives a string: 'cat, dog, fish, rabbit'
            learner might enter fewer or more items than author expects

    Configuration options:
        ordered (bool): Whether or not the entries should be in the correct order
            (default False)

        length_error (bool): Whether to raise an error if the student input has the wrong
            number of entries (default False)

        delimiter (str): Single character to use as the delimiter between entries (default ',')

        partial_credit (bool): Whether to award partial credit for a partly-correct answer
            (default True)

        subgrader (ItemGrader): The grader to use to grade each individual entry (required)

        answers (list, tuple of lists): The list of answers, or a tuple of lists of answers
            if multiple "correct lists" are available. Each individual answer must conform
            to the appropriate answer schema for the subgrader. The default is [], as an
            empty list is allowable if SingleListGrader is being used as a subgrader.
    """

    @property
    def schema_config(self):
        """Define the configuration options for SingleListGrader"""
        # Construct the default ItemGrader schema
        schema = super(SingleListGrader, self).schema_config
        # Append options, replacing the ItemGrader 'answers' key
        return schema.extend({
            Required('ordered', default=False): bool,
            Required('length_error', default=False): bool,
            Required('delimiter', default=','): str,
            Required('partial_credit', default=True): bool,
            Required('subgrader'): ItemGrader,
            Required('answers', default=[]): Any(list, (list,))  # Allow for a tuple of lists
        })

    # Make sure that the ItemGrader validate_expect isn't used
    validate_expect = None

    def __init__(self, config=None, **kwargs):
        """
        Validate the SingleListGrader's configuration.
        This is a bit different from other graders, because the validation of the answers
        depends on the subgrader item in the config. Hence, we validate in three steps:
        0. Subgrader class is initialized and checked before this class is initialized
        1. Validate the config for this class, checking that answers is a list
        2. Validate the answers by using the subgrader class
        """
        # Step 1: Validate the configuration of this list using the usual routines
        super(SingleListGrader, self).__init__(config, **kwargs)

        # Step 2: Validate the answers
        self.config['answers'] = self.schema_answers(self.config['answers'])

    def schema_answers(self, answer_tuple):
        """
        Defines the schema to validate an answer tuple against.

        This will transform the input to a tuple as necessary, and then attempt to
        validate the answer_tuple using the defined subgraders.

        Two forms for the answer tuple are acceptable:

        1. A list of answers
        2. A tuple of lists of answers
        """
        # Rename from the ItemGrader argument
        answers_tuple = answer_tuple

        # Turn answers_tuple into a tuple if it isn't already
        if isinstance(answers_tuple, list):
            if not answers_tuple:  # empty list
                # Nothing further to check here. This must be a nested grader, which will
                # be called upon to check answers again a bit later.
                return tuple()
            answers_tuple = (answers_tuple,)
        elif not isinstance(answers_tuple, tuple):  # pragma: no cover
            # Should not get here; voluptuous should catch this beforehand
            raise ConfigError("Answer list must be a list or a tuple of lists")

        # Check that all lists in the tuple have the same length
        for answer_list in answers_tuple:
            if len(answer_list) != len(answers_tuple[0]):
                raise ConfigError("All possible list answers must have the same length")

        # If subgrader is a SingleListGrader, check that it uses a different delimiter
        # TODO This does not check past the first level of nesting.
        if isinstance(self.config['subgrader'], SingleListGrader):
            subgrader = self.config['subgrader']
            if self.config['delimiter'] == subgrader.config['delimiter']:
                raise ConfigError("Nested SingleListGraders must use different delimiters.")

        # Validate answer_list using the subgrader
        for answer_list in answers_tuple:
            for index, answer in enumerate(answer_list):
                answer_list[index] = self.config['subgrader'].schema_answers(answer)
            if not answer_list:
                raise ConfigError("Cannot have an empty list of answers")

        return answers_tuple

    def check_response(self, answer, student_input, **kwargs):
        """Check student_input against a given answer list"""
        answers = answer  # Rename from the ItemGrader name
        student_list = student_input.split(self.config['delimiter'])

        if self.config['length_error'] and len(answers) != len(student_list):
            msg = 'List length error: Expected {} terms in the list, but received {}. ' + \
                  'Separate items with character "{}"'
            raise MissingInput(msg.format(len(answers),
                                          len(student_list),
                                          self.config['delimiter']))

        # We need to keep track of missing and extra answers.
        # Idea is:
        #    use _AutomaticFailure to pad expect and answers to equal length
        #    modify check to reject _AutomaticFailure
        pad_ans, pad_stud = get_padded_lists(answers, student_list)
        # Modify the check function to deal with the padding
        checker = padded_check(self.config['subgrader'].check)

        # Compute the results
        if self.config['ordered']:
            input_list = [checker(*pair) for pair in zip(pad_ans, pad_stud)]
        else:
            input_list = find_optimal_order(checker, pad_ans, pad_stud)

        result = consolidate_cfn_return(input_list,
                                        n_expect=len(answers),
                                        partial_credit=self.config['partial_credit'])

        return result
