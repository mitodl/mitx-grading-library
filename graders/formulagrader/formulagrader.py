from ..graders import ObjectWithSchema, ItemGrader
from ..voluptuous import Schema, Required, All, Any, Range, MultipleInvalid, Invalid, humanize, Length
import abc
import numpy
import numbers

class AbstractSamplingSet(ObjectWithSchema):
    """Represents a set from which random samples are taken."""
    pass

class RealInterval(AbstractSamplingSet):
    """Represents an interval of real numbers from which to sample."""
    
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

    def gen_samples(self,n):
        "Returns a list of n random reals in range [self.start, self.stop]"
        start, stop = self.config['start'], self.config['stop']
        
        width = stop - start
        uniform_iid = start + width*numpy.random.rand(n)
        
        return list(uniform_iid)

class NiceFunctions(AbstractSamplingSet):
    """Represents space of 'nice' functions from which to sample.
    """
    
    schema_config = Schema({
        Required('dims', default=1): All(
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
    """