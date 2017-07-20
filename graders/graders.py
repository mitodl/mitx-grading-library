from __future__ import division
import munkres
import numbers
import abc
from voluptuous import Schema, Required, All, Any, Range, MultipleInvalid, Invalid, humanize
import voluptuous.humanize as vh
from pprint import pprint

def PercentageString(value):
    if isinstance(value, str) and value.endswith("%"):
        try:
            percent = float(value[:-1])
            return percent
        except:
            pass
    
    raise ValueError("Not a percentage string.")

class AbstractGrader(object):
    
    __meta__ = abc.ABCMeta
    
    @abc.abstractmethod
    def cfn(self, answer, student_input):
        """Arguments:
            answer: a dictionary of form
                {'expect':..., 'ok':..., 'msg':..., 'grade_decimal':...}
            student_input: a string passed to grader by EdX
        """
        pass
    
    def validate_config(self, config):
        return vh.validate_with_humanized_errors(config, self.schema_config)
    
    def __init__(self, config={}):
        self.config = self.validate_config(config)
    
    def __repr__(self):
        return "{classname}({config})".format(classname=self.__class__.__name__, config = self.config)
        
class ListGrader(AbstractGrader):
    
    def make_schema_config(self, config):
        # ListGrader's schema_config depends on the config object...differe for different ItemGraders. Hence we need a function to dynamically create the schema.
        item_grader = vh.validate_with_humanized_errors( config['item_grader'], Schema(ItemGrader) )        
        schema = Schema({
            Required('ordered', default=False):bool,
            Required('separator', default=','): str,
            Required('item_grader'):ItemGrader,
            Required('answers_list'): [ item_grader.schema_answers ], 
        })
        return schema
    
    def __init__(self, config={}):
        self.schema_config = self.make_schema_config(config)
        super(ListGrader, self).__init__(config)
        self.item_cfn = self.config['item_grader'].cfn
    
    @staticmethod
    def find_optimal_order(cfn, answers_list, student_input_list):
        """ Finds optimal assignment of student_inputs --> answers according to cfn
        Inputs:
            answers_list: a list of answers
            student_input_list: a list of student inputs, one per input field
        
        Returns:
            an optimal matching input_list
        
        NOTE:
            uses https://github.com/bmc/munkres 
            to solve https://en.wikipedia.org/wiki/Assignment_problem
        """
        
        result_matrix = [ [ cfn(a, i) for a in answers_list] for i in student_input_list ]
        cost_matrix  = munkres.make_cost_matrix(
            result_matrix,
            lambda r: 1 - r['grade_decimal']
            )
        indexes = munkres.Munkres().compute(cost_matrix)
        
        input_list = [ result_matrix[i][j] for i, j in indexes]
        return input_list

    def cfn(self, answers_list, student_input):
        answers_list = self.config['answers_list']
        multi_input = isinstance(student_input, list)
        single_input = isinstance(student_input, str) or isinstance(student_input, unicode)
        if multi_input:
            return ListGraderListInput(self.config).cfn(answers_list, student_input)
        elif single_input:
            return ListGraderStringInput(self.config).cfn(answers_list, student_input)
        else:
            raise Exception("Expected answer to have type <type list> or <type unicode>, but had {t}".format(t = type(student_input)))

class ListGraderListInput(ListGrader):
    """Delegated to by ListGrader.cfn when student_input is a list.
    I.e., when customresponse contains multiple inputs.
    """
    
    def cfn(self, answers_list, student_input_list):
        answers_list = self.config['answers_list'] if answers_list==None else answers_list
        
        if self.config['ordered']:
            input_list = [ self.item_cfn(a, i) for a, i in zip(answers_list, student_input_list) ]
        else:
            input_list = self.find_optimal_order(self.item_cfn, answers_list, student_input_list)
        
        return {'input_list':input_list, 'overall_message':''}

class ListGraderStringInput(ListGrader):
    """Delegated to by ListGrader.cfn when student_input is a string.
    I.e., when customresponse contains a single input.
    """
    
    @staticmethod
    def assign_partial_credit(input_list, n_expect):
        """Given input list and expected number of inputs, assigns partial credit.
        Inputs:
            input_list, a list of SingleResponseGrader.cfn results
            n_expect: expected number of answers
        
        Assigns score linearly:
            +1 for each correct answer,
            -1 part for each extra answer.
        with a minimum score of zero.
        """
        points = sum([ result['grade_decimal'] for result in input_list ])
        n_extra = len(input_list) - n_expect
        grade_decimal = max(0, (points-n_extra)/n_expect )
        
        return grade_decimal

    @staticmethod
    def find_optimal_order(cfn, answers_list, student_input_list):
        """Same as ListGrader.find_optimal_order, but keeps track 
        of missing and extra answers.
        
        Idea is:
            create local class AutomaticFailure
            use AutomaticFailure to pad expect and answers to equal length
            modify cfn to reject AutomaticFailure
        """
        
        class AutomaticFailure(object):
            pass
        L = max(len(answers_list), len(student_input_list))
        
        padded_answers_list       = answers_list       + [AutomaticFailure()]*(L-len(answers_list))
        padded_student_input_list = student_input_list + [AutomaticFailure()]*(L-len(student_input_list))
        
        def _cfn(ans, inp):
            if isinstance(ans, AutomaticFailure) or isinstance(inp, AutomaticFailure):
                return {'ok':False, 'msg':'', 'grade_decimal':0}
            else:
                return cfn(ans,inp)
        
        return ListGrader.find_optimal_order(_cfn, padded_answers_list, padded_student_input_list)

    def cfn(self, answers_list, student_input):
        answers_list = self.config['answers_list'] if answers_list==None else answers_list
        student_input_list = student_input.split( self.config['separator'] )
        
        if self.config['ordered']:
            input_list = [ self.item_cfn(ans, inp) for ans, inp in zip(answers_list, student_input_list) ]
        else:
            input_list = self.find_optimal_order( self.item_cfn, answers_list, student_input_list)
        
        grade_decimal = self.assign_partial_credit(input_list, len(answers_list))
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

    def iterate_cfn(self, cfn):
        def iterated_cfn(answers, student_input):
            """Iterates cfn over each answer in answers
            """
            answers = self.config['answers'] if answers == None else answers
            results = [ cfn(answer, student_input) for answer in answers]            
            
            best_score = max([ r['grade_decimal'] for r in results ])
            best_results = [ r for r in results if r['grade_decimal'] == best_score]
            best_result_with_longest_msg = max(best_results, key = lambda r: len(r['msg']))
            
            return best_result_with_longest_msg
            
        return iterated_cfn

    def __init__(self, config={}):
        super(ItemGrader, self).__init__(config)
        self.cfn = self.iterate_cfn( self.cfn)

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
    
    def cfn(self, answer, student_input):
        if self.config['strip']:
            answer['expect'] = answer['expect'].strip()
            student_input = student_input.strip()
        
        if student_input.strip() == answer['expect'].strip():
            return {'ok':answer['ok'], 'grade_decimal':answer['grade_decimal'], 'msg':answer['msg']}
        else:
            return {'ok':False, 'grade_decimal':0, 'msg':''}

class FormulaGrader(ItemGrader):
    pass