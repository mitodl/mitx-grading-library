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
        
class FormulaGrader(ItemGrader):
    """ Grades mathematical expressions, like EdX formularesponse but flexible.    
    """