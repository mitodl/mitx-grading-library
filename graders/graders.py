from __future__ import division
from abc import ABCMeta, abstractmethod, abstractproperty
import munkres

class AbstractGrader(object):
    """Abstract base class for Grader classes"""
    __metaclass__ = ABCMeta
    
    @abstractproperty
    def CONFIG_DEFAULTS(self):
         pass
    
    @abstractproperty
    def CONFIG_REQUIRED_KEYS(self):
         pass
    
    @abstractmethod
    def cfn(self, expect, state):
        pass

    def set_config_defaults(self, config):
        for key in self.CONFIG_DEFAULTS:
            config.setdefault(key, self.CONFIG_DEFAULTS[key])
        return config

    def validate_config(self, config):
        for key in self.CONFIG_REQUIRED_KEYS:
            try:
                assert key in config
            except:
                raise Exception("Missing required key {key} in config".format(key=key))
        return
    
    def __init__(self, config):
        self.validate_config(config)
        self.config = self.set_config_defaults(config)

class SingleResponseGrader(AbstractGrader):
    """Provides helper methods to Graders intended for a single response field.
    
    SingleResponseGrader.cfn should return 
        {'ok':..., 'msg':..., 'decimal_grade':...}
    
    """
    
    @staticmethod
    def standardize_expect(expect):
        """Standard form of expect is a list of dictionaries with structure:
        [
            {'expect': ..., 'msg': ... , 'grade_decimal': ... }
        ]
        
        Three cases:
        1.  Input: A list of dctionaries, each containing key 'expect'
            Result: set defaults for 'msg' and 'grade_decimal' keys
        
        2.  Input: A non-list object or a list wherein NONE of the 
            items are dictionaries containing key 'expect.
            Result: Wrap input as single expected value,
                [{'expect':<Input>, 'msg':'', 'grade_decimal':1 }]
        
        3.  Input: A list wherein SOME BUT NOT ALL items are dicts
            containing key 'expect'.
            Result: Raise Exception.
        """
        try: # Case 1
            assert isinstance(expect, list)
            standardized_expect = []
            for item in expect:
                assert isinstance(item, dict)
                assert 'expect' in item
                item.setdefault('msg','')
                item.setdefault('grade_decimal', 1)
                item.setdefault('ok', SingleResponseGrader.grade_decimal_to_ok(item['grade_decimal']) )
                standardized_expect.append(item)
            return standardized_expect
        except AssertionError:
            pass
        
        try: # Case 2 and expect is not a list
            assert not isinstance(expect, list)
            return [{'expect':expect, 'msg':'', 'grade_decimal':1, 'ok':True}]
        except AssertionError: 
            pass
        
        try: # Case 2 and expect is a list
            for item in expect:
                if isinstance(item, dict):
                    assert 'expect' not in item
            return {'expect':expect, 'msg':'', 'grade_decimal':1, 'ok':True}
        except AssertionError:
            pass
        
        # Case 3
        raise Exception("expect is improperly formatted.")
    
    @staticmethod
    def assert_result_valid(result):
        assert result['ok'] in [True, False, 'partial']
        assert 0 <= result['grade_decimal'] <= 1
        assert 'msg' in result

    @staticmethod
    def assert_cfn_result_valid(cfn):
        """Asserts SingleResponseGrader.cfn returns a dict with
        key 'ok' and standardizes result to form:
            {'ok': ... , 'msg': ... , 'grade_decimal': ...}
        """

        def decorated_cfn(expect, answer):
            """cfn where output is guaranteed to have form
            {'ok': ... , 'msg': ... , 'grade_decimal': ...}
            """
            result = cfn(expect, answer)
            SingleResponseGrader.assert_result_valid(result)
            return result
           
        return decorated_cfn

    def iterate_cfn(self, cfn):
        def iterated_cfn(expect, answer):
            """Standardize expect to have form
            [
                {'expect': ... , 'msg': ... , 'grade_decimal': ...},
                {'expect': ... , 'msg': ... , 'grade_decimal': ...},
                ...
            ]
            Then compare answer to each 'expect' and take result with highest grade_decimal
            
            NOTE:
                cfn result should be standarized already
            """
            expect = self.config['expect'] if expect == None else expect
            standardized_expect = SingleResponseGrader.standardize_expect(expect)
            results = [ cfn(item, answer) for item in standardized_expect]
            
            maximal_score = max([ result['grade_decimal'] for result in results ])
            # There might be several
            maximal_scoring_results = [result for result in results if result['grade_decimal'] == maximal_score]
            # ... so take the one with the longest 'msg'
            best_result = max(maximal_scoring_results, key = lambda x: len(x['msg']))
            
            return best_result
            
        return iterated_cfn
        
    @staticmethod
    def grade_decimal_to_ok(grade_decimal):
        if grade_decimal >= 1:
            return True
        elif 0 < grade_decimal < 1:
            return 'partial'
        else:
            return False
    
    def __init__(self, config):
        super(SingleResponseGrader, self).__init__(config)
        self.cfn = self.assert_cfn_result_valid(self.cfn)
        self.cfn = self.iterate_cfn(self.cfn)

class MultiResponseGrader(AbstractGrader):
    """Provides helper methods to Graders intended for a single response field.
    
    MultiResponseGrader.cfn should return 
        {'overall_message':..., 'input_list':[...] }
    where input_list is a list SingleResponseGrader.cfn results
    
    """
    
    @staticmethod
    def assert_result_valid(overall_result):
        """Standardizes cfn return value.
        Required keys are:
            input_list (list): a list of SingleResponseGrader.cfn return values
        Optional keys are:
            overall_message (str): defaults to empty string
        
        The individual results in input_list are standardized with SingleResponseGrader.standardize_result
        """
        assert isinstance(overall_result['overall_message'], str)
        assert isinstance(overall_result['input_list'], list)
        for result in overall_result['input_list']:
            SingleResponseGrader.assert_result_valid(result)
            
        return overall_result

    @staticmethod
    def assert_cfn_result_valid(cfn):
        """Asserts MultiResponseGrader.cfn returns a dict with key-values:
            overall_message: str
            input_list: a list of SingleResponseGrader.cfn valid results
        """

        def decorated_cfn(expect, answer):
            """cfn where output is guaranteed to have form
            {'ok': ... , 'msg': ... , 'grade_decimal': ...}
            """
            result = cfn(expect, answer)
            MultiResponseGrader.assert_result_valid(result)
            return result
           
        return decorated_cfn

class ListGrader(AbstractGrader):
    """A generic grader for grading lists of input according to the same check function.
    
    Uses:
        1. Grade a comma-separated list in a single inputfield, i.e.,
            <customresponse>
                <textline />
            </customresponse>
        2. Grade several input-fields, i.e.,
            <customresponse>
                <textline />
                <textline />
            </customresponse>
    
    Input:
        A configuration object with keys
            ordered (default: False)
            item_grader (required): A grader instance that will grade individual items in the list.
            expect: A list of expect values to be passed to the item_grader
    """
    
    CONFIG_DEFAULTS = {
        'ordered':False
    }
    
    CONFIG_REQUIRED_KEYS = [
        'expect', # a list of values to be passed to item_grader.cfn
        'item_grader' # a SingleResponseGrader instance
     ]
     
    def __init__(self, config):
        super(ListGrader, self).__init__(config)
        self.item_cfn = config['item_grader'].cfn

    @staticmethod
    def _find_optimal_order(cfn, expect, answers):
        """ Finds optimal assignment of answers --> expect according to cfn
        Inputs:
            expect: a list of single-response expect values
            answers: a list of single-response answers
        
        Returns:
            an optimal matching input_list
        
        NOTE:
            uses https://github.com/bmc/munkres 
            to solve https://en.wikipedia.org/wiki/Assignment_problem
        """
        
        result_matrix = [ [ cfn(e, a) for e in expect] for a in answers ]
        cost_matrix  = munkres.make_cost_matrix(
            result_matrix,
            lambda r: 1 - r['grade_decimal']
            )
        indexes = munkres.Munkres().compute(cost_matrix)
        
        input_list = [ result_matrix[i][j] for i, j in indexes]
        return input_list

    def cfn(self, expect, answer):
        expect = self.config['expect']
        multi_input = isinstance(answer, list)
        single_input = isinstance(answer, str) or isinstance(answer, unicode)
        if multi_input:
            return ListMultiGrader(self.config).cfn(expect, answer)
        elif single_input:
            return ListSingleGrader(self.config).cfn(expect, answer)
        else:
            raise Exception("Expected answer to have type <type list> or <type unicode>, but had {t}".format(t = type(answer)))

class ListMultiGrader(ListGrader):
    """Delegated to by ListGrader.cfn when answer is a list of answers.
    I.e., when customresponse contains multiple inputs.
    """
    
    def __init__(self, config):
        super(ListMultiGrader, self).__init__(config)
        self.cfn = MultiResponseGrader.assert_cfn_result_valid(self.cfn)
    
    def cfn(self, expect, answers):
        self.config['expect'] if expect==None else expect
        assert len(expect) == len(answers)
        
        if self.config['ordered']:
            input_list = [ self.item_cfn(e, a) for e, a in zip(expect, answers) ]
        else:
            input_list = self._find_optimal_order(self.item_cfn, expect, answers)
        
        return {'input_list':input_list, 'overall_message':''}

class ListSingleGrader(ListGrader):
    """Delegated to by ListGrader.cfn when answer is a string.
    I.e., when customresponse contains a single input.
    """
    CONFIG_DEFAULTS = ListGrader.CONFIG_DEFAULTS
    CONFIG_DEFAULTS['separator'] = ','
    
    @staticmethod
    def _assign_partial_credit(input_list, n_expect):
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
    def _find_optimal_order(cfn, expect, answers):
        """Same as ListGrader._find_optimal_order, but keeps track 
        of missing and extra answers.
        
        Idea is:
            create local class AutomaticFailure
            use AutomaticFailure to pad expect and answers to equal length
            modify cfn to reject AutomaticFailure
        """
        
        class AutomaticFailure(object):
            pass
        L = max(len(expect), len(answers))
        
        padded_expect  = expect  + [AutomaticFailure()]*(L-len(expect))
        padded_answers = answers + [AutomaticFailure()]*(L-len(answers))
        
        def _cfn(e, a):
            if isinstance(e, AutomaticFailure) or isinstance(a, AutomaticFailure):
                return {'ok':False, 'msg':'', 'grade_decimal':0}
            else:
                return cfn(e,a)
        
        return ListGrader._find_optimal_order(_cfn, padded_expect, padded_answers)
    
    def __init__(self, config):
        super(ListSingleGrader, self).__init__(config)
        self.cfn = SingleResponseGrader.assert_cfn_result_valid(self.cfn)
    
    def cfn(self, expect, answer):
        self.config['expect'] if expect==None else expect
        answers = answer.split(self.config['separator'])
        
        if self.config['ordered']:
            input_list = [ self.item_cfn(e, a) for e, a in zip(padded_expect, padded_answers) ]
        else:
            input_list = self._find_optimal_order( self.item_cfn, expect, answers)

        grade_decimal = self._assign_partial_credit(input_list, len(expect))
        ok = SingleResponseGrader.grade_decimal_to_ok(grade_decimal)
        
        result = {
            'grade_decimal': grade_decimal,
            'ok': ok,
            'msg': '\n'.join([result['msg'] for result in input_list if result['msg'] != ''])
        }
        
        return result

class StringGrader(SingleResponseGrader):
    CONFIG_DEFAULTS = {
        'strip':True,
        'expect':None
    }
    CONFIG_REQUIRED_KEYS = []

    def __init__(self, config={}):
        super(StringGrader, self).__init__(config)

    def cfn(self, wrapped_expect, answer):
        """Check function for string comparison.
        Inputs:
            wrapped_expect: a dict of form
                {'expect': ... , 'ok': ... , 'grade_decimal': ..., 'msg': ...}
            answer: a string submited by learner
        Returns:
            a dict of form
                {'ok': ... , 'grade_decimal': ..., 'msg': ...}
        """
        expect = wrapped_expect['expect']

        if self.config['strip']:
            expect, answer = expect.strip(), answer.strip()
        
        match_expected = str(expect) == str(answer)
        
        if match_expected:
            return {key: wrapped_expect[key] for key in ['ok', 'msg', 'grade_decimal'] }
        else:
            return {'ok':False, 'msg':'', 'grade_decimal':0}
        
        return result