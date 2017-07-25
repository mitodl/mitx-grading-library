from ..graders import ObjectWithSchema, ItemGrader
from ..voluptuous import Schema, Required, All, Any, Range, MultipleInvalid, Invalid, humanize, Length
from ..validatorfuncs import Positive, NonNegative, PercentageString
from ..calc import evaluator, UndefinedVariable
import abc
import numpy
import random
from numbers import Number


class AbstractSamplingSet(ObjectWithSchema):
    """Represents a set from which random samples are taken."""
    pass

class VariableSamplingSet(AbstractSamplingSet):
    """Represents a set from which variable random samples are taken."""
    pass

class FunctionSamplingSet(AbstractSamplingSet):
    """Represents a set from which function random samples are taken."""
    pass

class RealInterval(VariableSamplingSet):
    """Represents an interval of real numbers from which to sample.
    
    Usage
    =====
    
    Generate 5 random floats betweens -2 and 4
    >>> ri = RealInterval({'start':-2, 'stop':4})
    >>> [ri.gen_sample() for j in range(5)] # doctest: +SKIP
    [ 2.44247 -0.67699 -1.36759 -0.11255  1.39864]
    
    You can initialize with a pair instead of a dict:
    >>> ri = RealInterval([-2,4])
    >>> [ri.gen_sample() for j in range(5)] # doctest: +SKIP
    [ 2.9973   2.95767  0.069    0.23813 -1.49541]
    
    The default is {'start':1, 'stop':3}:
    >>> ri = RealInterval()
    >>> [ri.gen_sample() for j in range(5)] # doctest: +SKIP
    [ 2.61484  1.38107  2.61687  1.00507  1.87933]    
    """
    
    def standardize_alternate_config(config_as_list):
        alternate_form = Schema(All(
            [Number, Number],
            Length(min=2,max=2)
        ))
        config_as_list = alternate_form(config_as_list)
        return {'start':config_as_list[0], 'stop':config_as_list[1]}
        
    schema_config = Schema(Any(
        {
            Required('start', default=1): Number,
            Required('stop', default=3): Number
        },
        standardize_alternate_config
    ))

    def gen_sample(self):
        "Returns a list of n random reals in range [self.start, self.stop]"
        start, stop = self.config['start'], self.config['stop']
        
        width = stop - start
        uniform_iid = start + width*numpy.random.rand(1)
        
        return uniform_iid[0]

class NiceFunctions(FunctionSamplingSet):
    """Represents space of 'nice' functions from which to sample.
    
    Usage
    =====
    
    Generate a random continous function:
    >>> funcs = NiceFunctions()
    >>> f = funcs.gen_sample()
    >>> [f(1.2), f(1.2), f(1.3), f(4)] # doctest: +SKIP
    [-1.89324 -1.89324 -2.10722  0.85814]
    
    By default, the generated functions are R-->R. You can specify the
    input and output dimensions:
    >>> funcs = NiceFunctions({'dims':[3,2]})
    >>> f = funcs.gen_sample()
    >>> f(2.3, -1, 4.2) # doctest: +SKIP
    [-1.74656 -0.96909]
    >>> f(2.3, -1.1, 4.2) # doctest: +SKIP
    [-1.88769 -1.32087]
    
    NOTE:
        1. Sadly, calc.evaluator can only handle unary functions
        2. Currently implemented as a sum of trigonometric functions
        with random phases and periods.
    """
    
    schema_config = Schema({
        Required('dims', default=[1,1]): All(
            list,
            Length(min=2, max=2),
            [All(int, Range(0,float('inf')))]
        ),
    })
    
    def gen_sample_component(self):
        """Generates one component of the sample function
        
        Current Implementation:
        If x1, x2, x3, ... are inputs, then function is of form
        
        sin(a11 x1 + b11) + sin(a12 x1 + b12) + ... + sin(a1k x1 + b1k) +
        sin(a21 x2 + b21) + sin(a22 x2 + b22) + ... + sin(a2k x2 + b2k) +
        sin(a31 x3 + b31) + sin(a32 x3 + b32) + ... + sin(a3k x3 + b3k) +
        ...
        = 
        sum(numpy.sin(C))
        where
        C_ij = A_ij*x_i + B_ij
        """
        num_terms = 3 # the k-value in docstring
        dim_input = self.config['dims'][0]
        
        A = 1 + numpy.random.rand(dim_input, num_terms)
        B = numpy.pi*numpy.random.rand(dim_input, num_terms)
        def component(*args):
            X = numpy.array([args,]*num_terms).transpose()
            return numpy.sum( numpy.sin(A*X + B) )

        return component
        
    def gen_sample(self):
        """Returns a randomly chosen 'nice' function."""
        
        dim_output = self.config['dims'][1]
        components = [self.gen_sample_component() for j in range(dim_output)]
        
        def f(*args):
            value = numpy.matrix([comp(*args) for comp in components])
            return value if dim_output>1 else float(value)
        
        return f

class DiscreteValues(VariableSamplingSet, FunctionSamplingSet):
    """Represents a discrete set of values from which to sample.
    
    Note:
        This class is provided just so that FormulaGrader has a consistent
        gen_sample() method to call when sampling.
    
    Usage
    =====
    
    >>> values = DiscreteValues([1,2,3,4])
    >>> values.gen_sample() in [1,2,3,4]
    True
    >>> values = DiscreteValues([numpy.sin, numpy.cos, numpy.tan])
    >>> values.gen_sample() in [numpy.sin, numpy.cos, numpy.tan]
    True
    """
    
    schema_config = Schema(list)
    
    def gen_sample(self):
        return random.choice(self.config)

class UniqueValue(VariableSamplingSet, FunctionSamplingSet):
    """Represents a unique value to sample.
    
    Note:
        This class is provided just so that FormulaGrader has a consistent
        gen_sample() method to call when sampling.
    
    Usage
    =====
    
    >>> values = UniqueValue(5)
    >>> values.gen_sample() == 5
    True
    >>> step_func = lambda x : 0 if x<0 else 1
    >>> values = UniqueValue(step_func)
    >>> values.gen_sample() == step_func
    True
    """
    
    schema_config = Schema(object)
    
    def gen_sample(self):
        return self.config

class NumericalGrader(ItemGrader):
    
    @staticmethod
    def within_tolerance(x, y, tolerance, hard_tolerance=10e-6):
        """Check that ||x-y||<tolerance or hard_tolerance with appropriate norm.
        
        Args:
            x: number or array (numpy array_like)
            y: number or array (numpy array_like)
            tolerance: Number or PercentageString
            hard_tolerance: Number, default to 10e-6
        
        Note:
            The purpose of hard_tolerance is that if tolerance is specified as
            a percentage and x is nearly zero, the calculated tolerance could 
            potential be smaller than Python's precision.
        
        Usage
        =====
        
        The tolerance can be a number:
        >>> NumericalGrader.within_tolerance(10, 9.01, 1)
        True
        >>> NumericalGrader.within_tolerance(10, 9.01, 0.5)
        False
        
        If tolerance is a percentage, it is a percent of (the norm of) x:
        >>> NumericalGrader.within_tolerance(10, 9.01, '10%')
        True
        >>> NumericalGrader.within_tolerance(9.01, 10, '10%')
        False
        
        Works for vectors and matrices:
        >>> A = numpy.matrix([[1,2],[-3,1]])
        >>> B = numpy.matrix([[1.1, 2], [-2.8, 1]])
        >>> diff = round(numpy.linalg.norm(A-B), 6)
        >>> diff
        0.223607
        >>> NumericalGrader.within_tolerance(A, B, 0.25)
        True
        """
        # When used within graders, tolerance has already been validated as a Number or PercentageString
        if isinstance(tolerance, str):
            tolerance = x * float(tolerance[:-1]) * 0.01 
            
        return numpy.linalg.norm(x-y) < max(tolerance, hard_tolerance) 
     
class FormulaGrader(NumericalGrader):
    """ Grades mathematical expressions.
    
    Similar to EdX formularesponse but more flexible. Allows author
    to specify functions in addition to variables.
    
    Usage
    =====
    
    Grade a formula containing variables and functions:
    >>> grader = FormulaGrader({
    ...     'answers':['a*b + f(c-b) + f(g(a))'],
    ...     'variables':['a', 'b','c'],
    ...     'functions':['f', 'g']
    ... })
    >>> input0 = 'f(g(a)) + a*b + f(-b+c)'
    >>> grader.cfn(None, input0)['ok']
    True
    >>> input1 = 'f(g(b)) + 2*a*b + f(b-c)'
    >>> grader.cfn(None, input1)['ok']
    False
    
    The learner's input is compared to expected answer using numerical
    numerical evaluations. By default, 5 evaluations are used with variables
    sampled on the interval [1,3]. The defaults can be overidden:
    >>> grader = FormulaGrader({
    ...     'answers': ['b^2 - f(g(a))/4'],
    ...     'variables': ['a', 'b'],
    ...     'functions': ['f', 'g'],
    ...     'samples': 3,
    ...     'sample_from': {
    ...         'a': [-4,1]    
    ...     },
    ...     'tolerance': 0.1
    ... })
    >>> input0 = "b*b - 0.25*f(g(a))"
    >>> grader.cfn(None, input0)['ok']
    True
    
    You can also provide specific values to use for any variable or function:
    >>> def square(x):
    ...     return x**2
    >>> grader = FormulaGrader({
    ...     'answers': ['4*f(a)+b'],
    ...     'variables': ['a','b'],
    ...     'functions': ['f'],
    ...     'sample_from': {
    ...         'f': UniqueValue(square)
    ...     }
    ... })
    >>> input0 = 'f(2*a)+b'             # f(2*a) = 4*f(a) for f = sq uare
    >>> grader.cfn(None, input0)['ok']
    True
    
    Configuration Dictionary Keys
    =============================
    
    answers (list): answers, each specified as a string or dictionary.
    variables (list of str): variable names, default []
    functions (list of str): function names, default []
    samples (int): Positive number of samples to use, default 5
    sample_from: A dictionary mapping synbol (variable or function name) to
        sampling sets. Default sampling sets are:
            for variables, RealInterval([1,3])
            for functions, NiceFunctions({dims=[1,1]})
    tolerance (int or PercentageString): A positive tolerance with which to 
        compare numerical evaluations. Default '0.1%'
    case_sensitive (bool): whether symbol names are case senstive. Default True
    failable_evals (int): The nonnegative maximum number of evaluation
         comparisons that can fail with grader still passing. Default 0
    
    """
    
    schema_expect = Schema(str)
    
    @property
    def schema_config(self):
        schema = super(FormulaGrader, self).schema_config
        
        # We need to dynamically create the samples_from Schema based on number variable and function names
        
        default_variables_sample_from = {
            Required(varname, default=RealInterval() ) : Any(
                VariableSamplingSet,
                lambda pair : RealInterval(pair)
            )
            for varname in self.config['variables']
        }
        
        default_functions_sample_from = {
            Required(funcname, default=NiceFunctions() ) : FunctionSamplingSet
            for funcname in self.config['functions']
        }
        
        schema_samples_from = Schema(default_variables_sample_from).extend(default_functions_sample_from)
        
        return schema.extend({
            Required('variables', default=[]): [str],
            Required('functions', default=[]): [str],
            Required('samples', default=5):Positive(int),
            Required('sample_from', default=schema_samples_from({})): schema_samples_from,
            Required('tolerance', default='0.1%'): Any(Positive(Number), PercentageString),
            Required('case_sensitive', default=True):bool,
            Required('failable_evals', default=0):NonNegative(int)
        })
    
    @staticmethod
    def gen_symbols_samples(symbols, samples, sample_from):
        """Generates a list of dictionaries mapping variable names to values.
        
        The symbols argument will usually be self.config['variables']
        or self.config['functions'].
        
        Usage
        =====
        
        >>> variable_samples = FormulaGrader.gen_symbols_samples(
        ...     ['a', 'b'],
        ...     3,
        ...     {
        ...         'a': RealInterval([1,3]),
        ...         'b': RealInterval([-4,-2])
        ...     }
        ... )
        >>> variable_samples # doctest: +SKIP
        [
            {'a': 1.4765130193614819, 'b': -2.5596368656227217},
            {'a': 2.3141937628942406, 'b': -2.8190938526155582},
            {'a': 2.8169225565573566, 'b': -2.6547771579673363}
        ]
        """
        
        return [ 
            { symbol: sample_from[symbol].gen_sample() for symbol in symbols }
            for j in range(samples)
        ]
    
    def raw_check(self, answer, student_input):
        """Check student_input against answer but do not format exceptions."""
        var_samples = self.gen_symbols_samples(
                            self.config['variables'],
                            self.config['samples'],
                            self.config['sample_from'])
        
        func_samples = self.gen_symbols_samples(
                            self.config['functions'],
                            self.config['samples'],
                            self.config['sample_from'])
        
        expected_evals = [ evaluator(
                                variables,
                                functions,
                                answer['expect'],
                                case_sensitive=self.config['case_sensitive'])
                            for variables, functions in 
                            zip(var_samples, func_samples)]
        
        learner_evals = [ evaluator(
                                variables,
                                functions,
                                student_input,
                                case_sensitive=self.config['case_sensitive'])
                            for variables, functions in 
                            zip(var_samples, func_samples)]

        failures = [ not self.within_tolerance(
                            e1, 
                            e2, 
                            self.config['tolerance'])
                        for e1, e2 in zip(expected_evals, learner_evals)]
        num_failures = sum(failures)
        
        if num_failures <= self.config['failable_evals']:
            return {
                'ok':answer['ok'],
                'grade_decimal':answer['grade_decimal'],
                'msg':answer['msg']
            }
        else:
            return {'ok':False, 'grade_decimal':0, 'msg':''}
    
    def check(self, answer, student_input):
        try:
            return self.raw_check(answer, student_input)
        except UndefinedVariable as e:
            message = "Invalid Input: {varname} not permitted in answer".format(varname=str(e))
            raise UndefinedVariable(message)
    