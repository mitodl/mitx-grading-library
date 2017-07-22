from __future__ import division
import munkres
import numbers
import abc
from voluptuous import Schema, Required, All, Any, Range, MultipleInvalid, Invalid, humanize
import voluptuous as v
import voluptuous.humanize as vh
from validatorfuncs import PercentageString

class ObjectWithSchema(object):
    "Represents a user-facing object whose configuration needs validation."
    
    __meta__ = abc.ABCMeta
    
    @abc.abstractproperty
    def schema_config(self):
        pass
    
    def validate_config(self, config):
        """Validates config and prints human-readable error messages."""
        return vh.validate_with_humanized_errors(config, self.schema_config)
    
    def __init__(self, config={}):
        self.config = self.validate_config(config)
    
    def __repr__(self):
        return "{classname}({config})".format(classname=self.__class__.__name__, config = self.config)    

class AbstractGrader(ObjectWithSchema):
    
    __meta__ = abc.ABCMeta
    
    @abc.abstractmethod
    def check(self, answer, student_input):
        """ Check student_input for correctness and provide feedback.
        
        Args:
            answer (dict): The expected result and grading information; has form
                {'expect':..., 'ok':..., 'msg':..., 'grade_decimal':...}
            student_input (str): The student's input passed by EdX
        """
        pass
    
    def cfn(self, expect, student_input):
        """Ignores expect and grades student_input. Used by EdX.
            
        Arguments:
            expect (str): The value of EdX customresponse expect attribute.
            student_input (str): The student's input passed by EdX
            
        NOTES:
            This function ignores the value of expect. Reason:            

            EdX requires a two-parameter check function cfn with 
            the signature above. In the graders module, we NEVER use
            the <customresponse /> tag's expect attribute for grading.
            
            (Our check functions require an answer dictionary, as described
            in the documentation for check.)
        
            But we do want to allow authors to use the edX <customresponse />
            expect attribute because it's value is diaplyed to students.
        """
        return self.check(None, student_input)
        
class ListGrader(AbstractGrader):
    """Grades Lists of items according to ItemGrader, unordered by default.
    
    ListGrader can be used to grade a list of answers according to the 
    supplied ItemGrader. Works with either multi-input customresponse
    or single-input customresponse.
    
    How learners enter lists in customresponse
    ==========================================
    
    Multi-input customresponse:
        <customresmse cfn="grader.cfn">
            <textline/> <!-- learner enters cat -->
            <textline/> <!-- learner enters dog -->
            <textline/> <!-- learner leaves blank -->
        </customresmse>
        Notes:
            grader.cfn receives a list: ['cat', 'dog', None]
            list will always contain exactly as many items as input tags
    
    Single-input customresponse:
        <customresmse cfn="grader.cfn">
            <textline/> <!-- learner enters 'cat, dog, fish, rabbit' -->
        </customresmse>
        Notes:
            learner is responsible for entering item separator (here: ',')
            grader.cfn receives a string: 'cat, dog, fish, rabbit'
            learner might enter fewer or more items than author expects
    
    Basic Usage
    ===========
    
    Grade a list of strings (multi-input)
        >>> grader = ListGrader({
        ...     'answers_list':[['cat'], ['dog'], ['fish']],
        ...     'item_grader': StringGrader()
        ... })
        >>> result = grader.cfn(None, ['fish', 'cat', 'moose'])
        >>> expected = {'input_list':[
        ...     {'ok': True, 'grade_decimal':1, 'msg':''},
        ...     {'ok': True, 'grade_decimal':1, 'msg':''},
        ...     {'ok': False, 'grade_decimal':0, 'msg':''}
        ... ], 'overall_message':''}
        >>> result == expected
        True
    
    Grade a string of comma-separated items through the same API:
        >>> result = grader.cfn(None, "cat, fish, moose")
        >>> expected = {'ok':'partial', 'grade_decimal':2/3, 'msg': '' }
        >>> result == expected
        True

    Extra items reduce score:
        >>> result = grader.cfn(None, "cat, fish, moose, rabbit")
        >>> expected = {'ok':'partial', 'grade_decimal':1/3, 'msg': '' }
        >>> result == expected
        True

    but not below zero:
        >>> result = grader.cfn(None, "cat, fish, moose, rabbit, bear, lion")
        >>> expected = {'ok':False, 'grade_decimal':0, 'msg': '' }
        >>> result == expected
        True
    
    Optionally, make order matter:
        >>> ordered_grader = ListGrader({
        ...     'ordered': True,
        ...     'answers_list':[['cat'], ['dog'], ['fish']],
        ...     'item_grader': StringGrader()
        ... })
        >>> result = ordered_grader.cfn(None, "cat, fish, moose")
        >>> expected = {'ok':'partial', 'grade_decimal':1/3, 'msg': '' }
        >>> result == expected
        True
    
    Optionally, change the separator for single-input:
        >>> semicolon_grader = ListGrader({
        ...     'separator': ';',
        ...     'answers_list':[['cat'], ['dog'], ['fish']],
        ...     'item_grader': StringGrader()
        ... })
        >>> result = semicolon_grader.cfn(None, "cat; fish; moose")
        >>> expected = {'ok':'partial', 'grade_decimal':2/3, 'msg': '' }
        >>> result == expected
        True
    
    
    """
    
    @property
    def schema_config(self):
        """Returns a voluptuous Schema object to validate config
        """
        # ListGrader's schema_config depends on the config object...different for different ItemGraders. Hence we need a function to dynamically create the schema. I would have prefered schema_config as a class attribute.
        item_grader = vh.validate_with_humanized_errors( self._item_grader, Schema(ItemGrader) )        
        schema = Schema({
            Required('ordered', default=False):bool,
            Required('separator', default=','): str,
            Required('item_grader'):ItemGrader,
            Required('answers_list'): [ item_grader.schema_answers ], 
        })
        return schema
    
    def __init__(self, config={}):
        self._item_grader = config['item_grader']
        super(ListGrader, self).__init__(config)
        self.item_check = self.config['item_grader'].check
    
    @staticmethod
    def find_optimal_order(check, answers_list, student_input_list):
        """ Finds optimal assignment (according to check) of inputs to answers.
        
        Inputs:
            answers_list (list): A list [answers_0, answers_1, ...] 
                wherein each answers_i is a valid ItemGrader.config['answers']
            student_input_list (list): a list of student inputs
        
        Returns:
            A re-ordered input_list to optimally match answers_list.
        
        NOTE:
            uses https://github.com/bmc/munkres 
            to solve https://en.wikipedia.org/wiki/Assignment_problem
        """
        
        result_matrix = [ [ check(a, i) for a in answers_list] for i in student_input_list ]
        cost_matrix  = munkres.make_cost_matrix(
            result_matrix,
            lambda r: 1 - r['grade_decimal']
            )
        indexes = munkres.Munkres().compute(cost_matrix)
        
        input_list = [ result_matrix[i][j] for i, j in indexes]
        return input_list

    def check(self, answers_list, student_input):
        """Checks student_input against answers_list."""
        answers_list = self.config['answers_list']
        multi_input = isinstance(student_input, list)
        single_input = isinstance(student_input, str) or isinstance(student_input, unicode)
        if multi_input:
            return ListGraderListInput(self.config).check(answers_list, student_input)
        elif single_input:
            return ListGraderStringInput(self.config).check(answers_list, student_input)
        else:
            raise Exception("Expected answer to have type <type list> or <type unicode>, but had {t}".format(t = type(student_input)))

class ListGraderListInput(ListGrader):
    """Delegated to by ListGrader.check when student_input is a list.
    I.e., when customresponse contains multiple inputs.
    """
    
    def check(self, answers_list, student_input_list):
        answers_list = self.config['answers_list'] if answers_list==None else answers_list
        
        if self.config['ordered']:
            input_list = [ self.item_check(a, i) for a, i in zip(answers_list, student_input_list) ]
        else:
            input_list = self.find_optimal_order(self.item_check, answers_list, student_input_list)
        
        return {'input_list':input_list, 'overall_message':''}

class ListGraderStringInput(ListGrader):
    """Delegated to by ListGrader.check when student_input is a string.
    I.e., when customresponse contains a single input.
    """
    
    @staticmethod
    def calculate_grade(grade_decimals, n_expect):
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
            >>> ListGraderStringInput.calculate_grade([1, 0, 0.5], 4)
            0.375
            >>> ListGraderStringInput.calculate_grade([1,0.5,0], 2)
            0.25
            >>> ListGraderStringInput.calculate_grade([1,0.5,0,0,0],2)
            0
        """
        n_extra = len(grade_decimals) - n_expect
        if n_extra > 0:
            grade_decimals += [-1] * n_extra
        elif n_extra < 0:
            grade_decimals += [0] * abs(n_extra)
        
        avg = sum(grade_decimals)/n_expect
        
        return max(0, avg)

    @staticmethod
    def find_optimal_order(check, answers_list, student_input_list):
        """Same as ListGrader.find_optimal_order, but keeps track 
        of missing and extra answers.
        
        Idea is:
            create local class AutomaticFailure
            use AutomaticFailure to pad expect and answers to equal length
            modify check to reject AutomaticFailure
        """
        
        class AutomaticFailure(object):
            pass
        L = max(len(answers_list), len(student_input_list))
        
        padded_answers_list       = answers_list       + [AutomaticFailure()]*(L-len(answers_list))
        padded_student_input_list = student_input_list + [AutomaticFailure()]*(L-len(student_input_list))
        
        def _check(ans, inp):
            if isinstance(ans, AutomaticFailure) or isinstance(inp, AutomaticFailure):
                return {'ok':False, 'msg':'', 'grade_decimal':0}
            else:
                return check(ans,inp)
        
        return ListGrader.find_optimal_order(_check, padded_answers_list, padded_student_input_list)

    def check(self, answers_list, student_input):
        answers_list = self.config['answers_list'] if answers_list==None else answers_list
        student_input_list = student_input.split( self.config['separator'] )
        
        if self.config['ordered']:
            input_list = [ self.item_check(ans, inp) for ans, inp in zip(answers_list, student_input_list) ]
        else:
            input_list = self.find_optimal_order( self.item_check, answers_list, student_input_list)
        
        grade_decimals = [g['grade_decimal'] for g in input_list]
        grade_decimal = self.calculate_grade(grade_decimals, len(answers_list))
        ok = ItemGrader.grade_decimal_to_ok(grade_decimal)
        
        result = {
            'grade_decimal': grade_decimal,
            'ok': ok,
            'msg': '\n'.join([result['msg'] for result in input_list if result['msg'] != ''])
        }
        
        return result

class ItemGrader(AbstractGrader):
    
    __meta__ = abc.ABCMeta
    
    @staticmethod
    def grade_decimal_to_ok(gd):
        if gd == 0 :
            return False
        elif gd == 1:
            return True
        else:
            return 'partial'
    
    @abc.abstractmethod
    def validate_input(self, value):
        pass
    
    @property
    def schema_answer(self):
        return Schema({
            Required('expect', default=None): self.validate_input,
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

    def iterate_check(self, check):
        def iterated_check(answers, student_input):
            """Iterates check over each answer in answers
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
        self.check = self.iterate_check( self.check)

class NumberGrader(ItemGrader):
    
    @property
    def schema_config(self):
        schema = super(NumberGrader, self).schema_config
        return schema.extend({
            Required('tolerance', default=0.1) : Any(
                All(numbers.Number, Range(0,float('inf'))),
                PercentageString
            )
        })

    def validate_input(self, value):
        if isinstance(value, numbers.Number):
            return value
        raise ValueError

class StringGrader(ItemGrader):
    
    @property
    def schema_config(self):
        schema = super(StringGrader, self).schema_config
        return schema.extend({
            Required('strip', default=True): bool,
            Required('case_sensitive', default=True) : bool
        })
    
    def validate_input(self, value):
        if isinstance(value, str):
            return value
        raise ValueError
    
    def check(self, answer, student_input):
        if self.config['strip']:
            answer['expect'] = answer['expect'].strip()
            student_input = student_input.strip()
        
        if student_input.strip() == answer['expect'].strip():
            return {'ok':answer['ok'], 'grade_decimal':answer['grade_decimal'], 'msg':answer['msg']}
        else:
            return {'ok':False, 'grade_decimal':0, 'msg':''}

class FormulaGrader(ItemGrader):
    pass