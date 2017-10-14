"""
Classes for numerical and formula graders
* NumericalGrader
* FormulaGrader

Also defines classes for sampling values
* RealInterval
* IntegerInterval
* ComplexRectangle
* ComplexSector
* SpecificValues
and for specifying functions
* SpecificFunctions
* RandomFunction
"""
from numbers import Number
import abc
import math
import random
import numpy as np
from graders.baseclasses import ObjectWithSchema, ItemGrader, ConfigError
from graders.helpers import calc
from graders.helpers.calc import UndefinedVariable, UndefinedFunction
from graders.helpers.validatorfuncs import (Positive, NonNegative, PercentageString,
                                            NumberRange, ListOfType, is_callable)
from graders.voluptuous import Schema, Required, Any, All

# Set the objects to be imported from this grader
__all__ = [
    "NumericalGrader",
    "FormulaGrader",
    "ComplexRectangle",
    "RealInterval",
    "IntegerInterval",
    "UndefinedVariable",
    "UndefinedFunction",
    "SpecificValues",
    "SpecificFunctions",
    "RandomFunction",
    "ComplexSector"
]

class AbstractSamplingSet(ObjectWithSchema):  # pylint: disable=abstract-method
    """Represents a set from which random samples are taken."""

    # This is an abstract base class
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def gen_sample(self):
        """Generate a sample from this sampling set"""
        pass


class VariableSamplingSet(AbstractSamplingSet):  # pylint: disable=abstract-method
    """Represents a set from which random variable samples are taken."""

    # This is an abstract base class
    __metaclass__ = abc.ABCMeta


class FunctionSamplingSet(AbstractSamplingSet):  # pylint: disable=abstract-method
    """Represents a set from which random function samples are taken."""

    # This is an abstract base class
    __metaclass__ = abc.ABCMeta


class RealInterval(VariableSamplingSet):  # pylint: disable=too-few-public-methods
    """
    Represents an interval of real numbers from which to sample.

    Usage
    =====
    Generate 5 random floats betweens -2 and 4
    >>> ri = RealInterval(start=-2, stop=4)
    >>> [ri.gen_sample() for j in range(5)] # doctest: +SKIP
    [ 2.44247 -0.67699 -1.36759 -0.11255  1.39864]

    You can also initialize with an interval:
    >>> ri = RealInterval([-2,4])
    >>> [ri.gen_sample() for j in range(5)] # doctest: +SKIP
    [ 2.9973   2.95767  0.069    0.23813 -1.49541]

    The default is start=1, stop=5:
    >>> ri = RealInterval()
    >>> [ri.gen_sample() for j in range(5)] # doctest: +SKIP
    [ 2.61484  1.38107  2.61687  1.00507  1.87933]
    """
    schema_config = NumberRange()

    def gen_sample(self):
        """Returns a random real number in the range [start, stop]"""
        start, stop = self.config['start'], self.config['stop']
        return start + (stop - start) * np.random.random_sample()


class IntegerInterval(VariableSamplingSet):  # pylint: disable=too-few-public-methods
    """
    Represents an interval of integers from which to sample.

    Specify start and stop or [start, stop] to initialize.

    Uses the pythonic idiom that start is included but stop is not.

    Usage
    =====
    Generate 5 random floats betweens -2 and 4
    >>> integer = IntegerInterval(start=-2, stop=5)
    >>> integer.gen_sample() in list(range(-2,5))
    True

    You can also initialize with an interval:
    >>> integer = IntegerInterval([-2,5])
    >>> integer.gen_sample() in list(range(-2,5))
    True

    The default is start=1, stop=5:
    >>> integer = IntegerInterval()
    >>> integer.gen_sample() in list(range(1,5))
    True
    """
    schema_config = NumberRange(int)

    def gen_sample(self):
        """Returns a random integer in range(start, stop)"""
        start, stop = self.config['start'], self.config['stop']
        return np.random.randint(low=start, high=stop)


class ComplexRectangle(VariableSamplingSet):  # pylint: disable=too-few-public-methods
    """
    Represents a rectangle in the complex plane from which to sample.

    Usage
    =====
    >>> rect = ComplexRectangle(re=[1,4], im=[-5,0])
    >>> rect.gen_sample() # doctest: +SKIP
    (1.90313791936 - 2.94195943775j)
    """
    schema_config = Schema({
        Required('re', default=[1, 3]): NumberRange(),
        Required('im', default=[1, 3]): NumberRange()
    })

    def __init__(self, config=None, **kwargs):
        """
        Configure the class as normal, then set up the real and imaginary
        parts as RealInterval objects
        """
        super(ComplexRectangle, self).__init__(config, **kwargs)
        self.re = RealInterval(self.config['re'])
        self.im = RealInterval(self.config['im'])

    def gen_sample(self):
        """Generates a random sample in the defined rectangle in the complex plane"""
        return self.re.gen_sample() + self.im.gen_sample()*1j


class ComplexSector(VariableSamplingSet):  # pylint: disable=too-few-public-methods
    """
    Represents an annular sector in the complex plane from which to sample,
    based on a given range of modulus and argument.

    Usage
    =====
    >>> sect = ComplexSector(modulus=[0,1], argument=[-np.pi,np.pi])
    >>> sect.gen_sample() # doctest: +SKIP
    (0.022537684419662009+0.093135340148676249j)
    """
    schema_config = Schema({
        Required('modulus', default=[1, 3]): NumberRange(),
        Required('argument', default=[0, np.pi/2]): NumberRange()
    })

    def __init__(self, config=None, **kwargs):
        """
        Configure the class as normal, then set up the modulus and argument
        parts as RealInterval objects
        """
        super(ComplexSector, self).__init__(config, **kwargs)
        self.modulus = RealInterval(self.config['modulus'])
        self.argument = RealInterval(self.config['argument'])

    def gen_sample(self):
        """Generates a random sample in the defined annular sector in the complex plane"""
        return self.modulus.gen_sample() * np.exp(1j * self.argument.gen_sample())


class RandomFunction(FunctionSamplingSet):  # pylint: disable=too-few-public-methods
    """
    Generates a random well-behaved function on demand.

    Currently implemented as a sum of trigonometric functions with
    random amplitude, frequency and phase.

    Usage
    =====
    Generate a random continous function:
    >>> funcs = RandomFunction()
    >>> f = funcs.gen_sample()
    >>> [f(1.2), f(1.2), f(1.3), f(4)] # doctest: +SKIP
    [-1.89324 -1.89324 -2.10722  0.85814]

    By default, the generated functions are R-->R. You can specify the
    input and output dimensions:
    >>> funcs = RandomFunction(input_dim=3, output_dim=2)
    >>> f = funcs.gen_sample()
    >>> f(2.3, -1, 4.2) # doctest: +SKIP
    [-1.74656 -0.96909]
    >>> f(2.3, -1.1, 4.2) # doctest: +SKIP
    [-1.88769 -1.32087]
    """

    schema_config = Schema({
        Required('input_dim', default=1): Positive(int),
        Required('output_dim', default=1): Positive(int),
        Required('num_terms', default=3): Positive(int)
    })

    def gen_sample(self):
        """
        Returns a randomly chosen 'nice' function.

        The output is a vector with output_dim dimensions:
        Y^i = sum_{jk} A^i_{jk} sin(B^i_{jk} X_k + C^i_{jk})

        i ranges from 1 to output_dim
        j ranges from 1 to num_terms
        k ranges from 1 to input_dim
        """
        # Generate arrays of random values for A, B and C
        output_dim = self.config['output_dim']
        input_dim = self.config['input_dim']
        num_terms = self.config['num_terms']
        # Amplitudes A range from 0.5 to 1.5
        A = np.random.rand(output_dim, num_terms, input_dim) + 0.5
        # Angular frequencies B range from -pi to pi
        B = 2 * np.pi * (np.random.rand(output_dim, num_terms, input_dim) - 0.5)
        # Phases C range from 0 to 2*pi
        C = 2 * np.pi * np.random.rand(output_dim, num_terms, input_dim)

        def f(*args):
            """Function that generates the random values"""
            # Check that the dimensions are correct
            if len(args) != input_dim:
                msg = "Expected {} arguments, but received {}".format(input_dim, len(args))
                raise ConfigError(msg)

            # Turn the inputs into an array
            xvec = np.array(args)
            # Repeat it into the shape of A, B and C
            xarray = np.tile(xvec, (output_dim, num_terms, 1))
            # Compute the output matrix
            output = A * np.sin(B * xarray + C)
            # Sum over the j and k terms
            # We have an old version of numpy going here, so we can't use
            # fullsum = np.sum(output, axis=(1, 2))
            fullsum = np.sum(np.sum(output, axis=2), axis=1)

            # Return the result
            return fullsum if output_dim > 1 else fullsum[0]

        return f


class SpecificValues(VariableSamplingSet):  # pylint: disable=too-few-public-methods
    """
    Represents a discrete set of values from which to sample.

    Can be initialized with a single value or a non-empty list of values.

    Usage
    =====
    >>> values = SpecificValues(3.142)
    >>> values.gen_sample() == 3.142
    True
    >>> values = SpecificValues([1,2,3,4])
    >>> values.gen_sample() in [1,2,3,4]
    True
    """

    # Take in an individual or list of numbers
    schema_config = Schema(ListOfType(Number))

    def gen_sample(self):
        """Return a random entry from the given list"""
        return random.choice(self.config)


class SpecificFunctions(FunctionSamplingSet):  # pylint: disable=too-few-public-methods
    """
    Represents user-defined functions for use in a grader.

    If desired, multiple functions can be provided in a list, and a random
    function will be selected when needed.

    Usage
    =====

    >>> functions = SpecificFunctions([np.sin, np.cos, np.tan])
    >>> functions.gen_sample() in [np.sin, np.cos, np.tan]
    True
    >>> step_func = lambda x : 0 if x<0 else 1
    >>> functions = SpecificFunctions(step_func)
    >>> functions.gen_sample() == step_func
    True
    """

    # Take in a function or list of callable objects
    schema_config = Schema(ListOfType(object, is_callable))

    def gen_sample(self):
        """Return a random entry from the given list"""
        return random.choice(self.config)


class NumericalGrader(ItemGrader):
    """Class that grades numerical input and expressions"""

    # The scimath variants have flexible domain. For example:
    #   np.sqrt(-4+0j) = 2j
    #   np.sqrt(-4) = nan, but
    #   np.lib.scimath.sqrt(-4) = 2j
    DEFAULT_FUNCTIONS = {
        'sin': np.sin,
        'cos': np.cos,
        'tan': np.tan,
        'sec': calc.functions.sec,
        'csc': calc.functions.csc,
        'cot': calc.functions.cot,
        'sqrt': np.lib.scimath.sqrt,
        'log10': np.lib.scimath.log10,
        'log2': np.lib.scimath.log2,
        'ln': np.lib.scimath.log,
        'exp': np.exp,
        'arccos': np.lib.scimath.arccos,
        'arcsin': np.lib.scimath.arcsin,
        'arctan': np.arctan,
        'arcsec': calc.functions.arcsec,
        'arccsc': calc.functions.arccsc,
        'arccot': calc.functions.arccot,
        'abs': np.abs,
        'fact': math.factorial,
        'factorial': math.factorial,
        'sinh': np.sinh,
        'cosh': np.cosh,
        'tanh': np.tanh,
        'sech': calc.functions.sech,
        'csch': calc.functions.csch,
        'coth': calc.functions.coth,
        'arcsinh': np.arcsinh,
        'arccosh': np.arccosh,
        'arctanh': np.lib.scimath.arctanh,
        'arcsech': calc.functions.arcsech,
        'arccsch': calc.functions.arccsch,
        'arccoth': calc.functions.arccoth,
        # lambdas because sometimes np.real/imag returns an array,
        're': lambda x: float(np.real(x)),
        'im': lambda x: float(np.imag(x)),
        'conj': np.conj,
    }
    DEFAULT_VARIABLES = {
        'i': np.complex(0, 1),
        'j': np.complex(0, 1),
        'e': np.e,
        'pi': np.pi
    }

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
        >>> A = np.matrix([[1,2],[-3,1]])
        >>> B = np.matrix([[1.1, 2], [-2.8, 1]])
        >>> diff = round(np.linalg.norm(A-B), 6)
        >>> diff
        0.223607
        >>> NumericalGrader.within_tolerance(A, B, 0.25)
        True
        """
        # When used within graders, tolerance has already been
        # validated as a Number or PercentageString
        if isinstance(tolerance, str):
            tolerance = np.linalg.norm(x) * float(tolerance[:-1]) * 0.01

        return np.linalg.norm(x-y) < max(tolerance, hard_tolerance)


class FormulaGrader(NumericalGrader):
    """ Grades mathematical expressions.

    Similar to edX formularesponse but more flexible. Allows author
    to specify functions in addition to variables.

    Usage
    =====

    Grade a formula containing variables and functions:
    >>> grader = FormulaGrader(
    ...     answers='a*b + f(c-b) + f(g(a))',
    ...     variables=['a', 'b','c'],
    ...     functions=['f', 'g']
    ... )
    >>> theinput0 = 'f(g(a)) + a*b + f(-b+c)'
    >>> grader(None, theinput0)['ok']
    True
    >>> theinput1 = 'f(g(b)) + 2*a*b + f(b-c)'
    >>> grader(None, theinput1)['ok']
    False

    The learner's input is compared to expected answer using numerical
    numerical evaluations. By default, 5 evaluations are used with variables
    sampled on the interval [1,3]. The defaults can be overidden:
    >>> grader = FormulaGrader(
    ...     answers='b^2 - f(g(a))/4',
    ...     variables=['a', 'b'],
    ...     functions=['f', 'g'],
    ...     samples=3,
    ...     sample_from={
    ...         'a': [-4,1]
    ...     },
    ...     tolerance=0.1
    ... )
    >>> theinput = "b*b - 0.25*f(g(a))"
    >>> grader(None, theinput)['ok']
    True

    You can also provide specific values to use for any variable or function:
    >>> def square(x):
    ...     return x**2
    >>> grader = FormulaGrader(
    ...     answers='4*f(a)+b',
    ...     variables=['a','b'],
    ...     functions=['f'],
    ...     sample_from={
    ...         'f': SpecificFunctions(square)
    ...     }
    ... )
    >>> theinput = 'f(2*a)+b'             # f(2*a) = 4*f(a) for f = square
    >>> grader(None, theinput)['ok']
    True

    Grade complex-valued expressions:
    >>> grader = FormulaGrader(
    ...     answers='abs(z)^2',
    ...     variables=['z'],
    ...     sample_from={
    ...         'z': ComplexRectangle()
    ...     }
    ... )
    >>> theinput = 're(z)^2+im(z)^2'
    >>> grader(None, theinput)['ok']
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
            for functions, RandomFunction({dims=[1,1]})
    tolerance (int or PercentageString): A positive tolerance with which to
        compare numerical evaluations. Default '0.1%'
    case_sensitive (bool): whether symbol names are case senstive. Default True
    failable_evals (int): The nonnegative maximum number of evaluation
         comparisons that can fail with grader still passing. Default 0

    """

    DEFAULT_VARIABLES = {
        'i': np.complex(0, 1),
        'j': np.complex(0, 1),
        'e': np.e,
        'pi': np.pi,
    }

    def __init__(self, config=None, **kwargs):
        """
        Validate the Formulagrader's configuration.
        First, validate the config in broad strokes, then refine the sample_from entry.
        """
        super(FormulaGrader, self).__init__(config, **kwargs)

        # Construct the schema for sample_from
        # Allow anything that RealInterval can make sense of to be valid
        variables_sample_from = {
            Required(varname, default=RealInterval()):
                Any(VariableSamplingSet, lambda pair: RealInterval(pair))
            for varname in self.config.get('variables', [])
        }
        functions_sample_from = {
            Required(funcname, default=RandomFunction()): FunctionSamplingSet
            for funcname in self.config.get('functions', [])
        }
        sample_from = variables_sample_from
        sample_from.update(functions_sample_from)
        schema_sample_from = Schema(sample_from)

        # Apply the schema to sample_from
        self.config['sample_from'] = schema_sample_from(self.config['sample_from'])

        # TODO: split sample_from into variables and functions
        # This will avoid any collisions

    @property
    def schema_config(self):
        """Define the configuration options for FormulaGrader"""
        # Construct the default ItemGrader schema
        schema = super(FormulaGrader, self).schema_config
        # Append options
        return schema.extend({
            Required('variables', default=[]): [str],
            Required('functions', default=[]): [str],
            Required('samples', default=5): Positive(int),
            Required('sample_from', default={}): dict,
            Required('tolerance', default='0.1%'): Any(Positive(Number), PercentageString),
            Required('case_sensitive', default=True): bool,
            Required('failable_evals', default=0): NonNegative(int)
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
            {symbol: sample_from[symbol].gen_sample() for symbol in symbols}
            for j in range(samples)
        ]

    def raw_check(self, answer, student_input):
        """Check student_input against answer but do not format exceptions."""
        var_samples = self.gen_symbols_samples(self.config['variables'],
                                               self.config['samples'],
                                               self.config['sample_from'])

        func_samples = self.gen_symbols_samples(self.config['functions'],
                                                self.config['samples'],
                                                self.config['sample_from'])

        expected_evals = [
            calc.evaluator(variables,
                           functions,
                           answer['expect'],
                           case_sensitive=self.config['case_sensitive'],
                           default_variables=self.DEFAULT_VARIABLES,
                           default_functions=self.DEFAULT_FUNCTIONS)
            for variables, functions in zip(var_samples, func_samples)
        ]

        learner_evals = [
            calc.evaluator(variables,
                           functions,
                           student_input,
                           case_sensitive=self.config['case_sensitive'],
                           default_variables=self.DEFAULT_VARIABLES,
                           default_functions=self.DEFAULT_FUNCTIONS)
            for variables, functions in zip(var_samples, func_samples)
        ]

        failures = [
            not self.within_tolerance(e1, e2, self.config['tolerance'])
            for e1, e2 in zip(expected_evals, learner_evals)
        ]
        num_failures = sum(failures)

        if num_failures <= self.config['failable_evals']:
            return {
                'ok': answer['ok'],
                'grade_decimal': answer['grade_decimal'],
                'msg': answer['msg']
            }

        return {'ok': False, 'grade_decimal': 0, 'msg': ''}

    def check_response(self, answer, student_input):
        """Check the student response against a given answer"""
        try:
            return self.raw_check(answer, student_input)
        except UndefinedVariable as e:
            message = "Invalid Input: {varname} not permitted in answer as a variable".format(varname=str(e))
            raise UndefinedVariable(message)
        except UndefinedFunction as e:
            funcnames = e.args[0]
            valid_var = e.args[1]
            message = "Invalid Input: {varname} not permitted in answer as a function".format(varname=funcnames)
            if valid_var:
                message += " (did you forget to use * for multiplication?)"
            raise UndefinedFunction(message)
