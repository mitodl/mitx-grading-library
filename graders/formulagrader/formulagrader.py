from ..graders import ObjectWithSchema, ItemGrader
from ..voluptuous import Schema, Required, All, Any, Range, MultipleInvalid, Invalid, humanize, Length
import abc
import numpy
import numbers

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
            [numbers.Number, numbers.Number],
            Length(min=2,max=2)
        ))
        config_as_list = alternate_form(config_as_list)
        return {'start':config_as_list[0], 'stop':config_as_list[1]}
        
    schema_config = Schema(Any(
        {
            Required('start', default=1): numbers.Number,
            Required('stop', default=3): numbers.Number
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
        Currently implemented as a sum of trigonometric functions
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
            value = [comp(*args) for comp in components]
            return value if len(value)>1 else value[0]
        
        return f
        
class FormulaGrader(ItemGrader):
    """ Grades mathematical expressions, like EdX formularesponse but flexible.    
    FormulaGrader({
        'answers':['a+b^2'],
        'variables': ['a', 'b', 'c'],
        'functions': ['f', 'g', 'h'],
        'sample_from': {
            'a': [1,3],
            'b': [1,3],
            'c': RealInterval(1, 3),
            'd': IntegerInterval(-5,5),
            'd': MatrixGroupSO(2),
            'h': PolynomialFunction
        },
        'samples':5
    })
    """
    
    def validate_input(self, value):
        if isinstance(value, str):
            return value
        raise ValueError
    
    @property
    def schema_config(self):
        schema = super(FormulaGrader, self).schema_config
        
        # We need to dynamically create the samples_from Schema based on number variable and function names
        
        default_variables_sample_from = {
            Required(varname, default=RealInterval() ) : VariableSamplingSet
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
            Required('samples', default=5):All(int, Range(1, float('inf'))),
            Required('sample_from', default=schema_samples_from({})): schema_samples_from,
            Required('case_sensitive', default=True):bool
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
    
    
    def check(self, answer, student_input):
        pass