"""
sampling.py

Contains classes for sampling numerical values
* RealInterval
* IntegerRange
* DiscreteSet
* ComplexRectangle
* ComplexSector
* DependentSampler
and for specifying functions
* SpecificFunctions
* RandomFunction

Contains some helper functions used in grading formulae:
* gen_symbols_samples
* construct_functions
* construct_constants
* construct_suffixes

All of these classes perform random sampling. To obtain a sample, use class.gen_sample()
"""
from __future__ import division
from numbers import Number
import abc
import random
import numpy as np
from mitxgraders.baseclasses import ObjectWithSchema, ConfigError
from mitxgraders.voluptuous import Schema, Required
from mitxgraders.helpers.validatorfuncs import (Positive, NumberRange, ListOfType,
                                                TupleOfType, is_callable)
from mitxgraders.helpers.mathfunc import (DEFAULT_FUNCTIONS, DEFAULT_SUFFIXES,
                                          DEFAULT_VARIABLES, METRIC_SUFFIXES)
from mitxgraders.helpers.calc import CalcError, evaluator

# Set the objects to be imported from this grader
__all__ = [
    "RealInterval",
    "IntegerRange",
    "DiscreteSet",
    "ComplexRectangle",
    "ComplexSector",
    "SpecificFunctions",
    "RandomFunction",
    "DependentSampler"
]

def set_seed(seed=None):
    random.seed(seed)
    np.random.seed(seed)

class AbstractSamplingSet(ObjectWithSchema):  # pylint: disable=abstract-method
    """Represents a set from which random samples are taken."""

    # This is an abstract base class
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def gen_sample(self):
        """Generate a sample from this sampling set"""


class VariableSamplingSet(AbstractSamplingSet):  # pylint: disable=abstract-method
    """Represents a set from which random variable samples are taken."""

    # This is an abstract base class
    __metaclass__ = abc.ABCMeta


class FunctionSamplingSet(AbstractSamplingSet):  # pylint: disable=abstract-method
    """Represents a set from which random function samples are taken."""

    # This is an abstract base class
    __metaclass__ = abc.ABCMeta


class RealInterval(VariableSamplingSet):
    """
    Represents an interval of real numbers from which to sample.

    Config:
        start (float): Lower end of the range (default 1)
        stop (float): Upper end of the range (default 5)

    Usage
    =====
    Generate random floats betweens -2 and 4
    >>> ri = RealInterval(start=-2, stop=4)

    You can also initialize with an interval as a list:
    >>> ri = RealInterval([-2,4])
    """
    schema_config = NumberRange()

    def __init__(self, config=None, **kwargs):
        """
        Validate the specified configuration.
        First apply the voluptuous validation.
        Then ensure that the start and stop are the right way around.
        """
        super(RealInterval, self).__init__(config, **kwargs)
        if self.config['start'] > self.config['stop']:
            self.config['start'], self.config['stop'] = self.config['stop'], self.config['start']

    def gen_sample(self):
        """Returns a random real number in the range [start, stop]"""
        start, stop = self.config['start'], self.config['stop']
        return start + (stop - start) * np.random.random_sample()


class IntegerRange(VariableSamplingSet):
    """
    Represents an interval of integers from which to sample.

    Config:
        start (int): Lower end of the range (default 1)
        stop (int): Upper end of the range (default 5)

    Both start and stop are included in the interval.

    Usage
    =====
    Generate random integers betweens -2 and 4
    >>> integer = IntegerRange(start=-2, stop=4)

    You can also initialize with an interval:
    >>> integer = IntegerRange([-2,4])
    """
    schema_config = NumberRange(int)

    def __init__(self, config=None, **kwargs):
        """
        Validate the specified configuration.
        First apply the voluptuous validation.
        Then ensure that the start and stop are the right way around.
        """
        super(IntegerRange, self).__init__(config, **kwargs)
        if self.config['start'] > self.config['stop']:
            self.config['start'], self.config['stop'] = self.config['stop'], self.config['start']

    def gen_sample(self):
        """Returns a random integer in range(start, stop)"""
        return np.random.randint(low=self.config['start'], high=self.config['stop'] + 1)


class ComplexRectangle(VariableSamplingSet):
    """
    Represents a rectangle in the complex plane from which to sample.

    Config:
        re (list): Range for the real component (default [1,3])
        im (list): Range for the imaginary component (default [1,3])

    Usage
    =====
    >>> rect = ComplexRectangle(re=[1,4], im=[-5,0])
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


class ComplexSector(VariableSamplingSet):
    """
    Represents an annular sector in the complex plane from which to sample,
    based on a given range of modulus and argument.

    Config:
        modulus (list): Range for the modulus (default [1,3])
        argument (list): Range for the argument (default [0,pi/2])

    Usage
    =====
    Sample from the unit circle
    >>> sect = ComplexSector(modulus=[0,1], argument=[-np.pi,np.pi])
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


class DiscreteSet(VariableSamplingSet):  # pylint: disable=too-few-public-methods
    """
    Represents a discrete set of values from which to sample.

    Initialize with a single value or a non-empty tuple of values. Note that we use a
    tuple instead of a list so that the range [0,1] isn't confused with (0,1). We would
    use a set, but unfortunately voluptuous doesn't work with sets.

    Usage
    =====
    Specify a single value
    >>> values = DiscreteSet(3.142)

    Specify a tuple of values
    >>> values = DiscreteSet((1,3,5,7,9))
    """

    # Take in an individual or tuple of numbers
    schema_config = Schema(TupleOfType(Number))

    def gen_sample(self):
        """Return a random entry from the given set"""
        return random.choice(self.config)


class RandomFunction(FunctionSamplingSet):  # pylint: disable=too-few-public-methods
    """
    Generates a random well-behaved function on demand.

    Currently implemented as a sum of trigonometric functions with random amplitude,
    frequency and phase. You can control the center and amplitude of the resulting
    oscillations by specifying center and amplitude.

    Config:
        input_dim (int): Number of input arguments. 1 is a unary function (default 1)
        output_dim (int): Number of output dimensions. 1 = scalar, more than 1 is a vector
            (default 1)
        num_terms (int): Number of random sinusoid terms to add together (default 3)
        center (float): Center around which oscillations occur (default 0)
        amplitude (float): Maximum amplitude of the function (default 10)

    Usage
    =====
    Generate a random continous function
    >>> funcs = RandomFunction()

    By default, the generated functions are R-->R. You can specify the
    input and output dimensions:
    >>> funcs = RandomFunction(input_dim=3, output_dim=2)

    To control the range of the function, specify a center and amplitude. The bounds of
    the function will be center - amplitude < func(x) < center + amplitude.
    The following will give oscillations between 0 and 1.
    >>> funcs = RandomFunction(center=0.5, amplitude=0.5)
    """

    schema_config = Schema({
        Required('input_dim', default=1): Positive(int),
        Required('output_dim', default=1): Positive(int),
        Required('num_terms', default=3): Positive(int),
        Required('center', default=0): Number,
        Required('amplitude', default=10): Positive(Number)
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
        # Amplitudes A range from 0.5 to 1
        A = np.random.rand(output_dim, num_terms, input_dim) / 2 + 0.5
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

            # Scale and translate to fit within center and amplitude
            fullsum = fullsum * self.config["amplitude"] / self.config["num_terms"]
            fullsum += self.config["center"]

            # Return the result
            return fullsum if output_dim > 1 else fullsum[0]

        return f


class SpecificFunctions(FunctionSamplingSet):  # pylint: disable=too-few-public-methods
    """
    Represents a set of user-defined functions for use in a grader, one of which will
    be randomly selected. A single function can be provided here, but this is intended
    for lists of functions to be randomly sampled from.

    Initialize with either a single function, or a list of functions.

    Usage
    =====
    Initialize with a specific function.
    >>> step_func = lambda x : 0 if x<0 else 1
    >>> functions = SpecificFunctions(step_func)

    Initialize with a list of functions.
    >>> functions = SpecificFunctions([np.sin, np.cos, np.tan])
    """

    # Take in a function or list of callable objects
    schema_config = Schema(ListOfType(object, is_callable))

    def gen_sample(self):
        """Return a random entry from the given list"""
        return random.choice(self.config)


class DependentSampler(VariableSamplingSet):
    """
    Represents a variable that depends on other variables.

    You must initialize with the list of variables this depends on as well as the formula
    for this variable. Note that only base formulas and suffixes are available for this
    computation.

    Usage
    =====
    Specify a single value
    >>> ds = DependentSampler(depends=['x', 'y', 'z'], formula="sqrt(x^2+y^2+z^2)")
    """

    # Take in an individual or tuple of numbers
    schema_config = Schema({
        Required('depends'): [str],
        Required('formula'): str,
        Required('case_sensitive', default=True): bool
    })

    def gen_sample(self):
        """Return a random entry from the given set"""
        raise Exception("DependentSampler must be invoked with compute_sample.")

    def compute_sample(self, sample_dict):
        """Compute the value of this sample"""
        try:
            result, _ = evaluator(formula=self.config['formula'],
                                  case_sensitive=self.config['case_sensitive'],
                                  variables=sample_dict,
                                  functions=DEFAULT_FUNCTIONS,
                                  suffixes=DEFAULT_SUFFIXES)
        except CalcError:
            raise ConfigError("Formula error in dependent sampling formula: " +
                              self.config["formula"])

        return result

def is_subset(iterable, iterable_superset):
    """
    Helper function for gen_symbols_samples below.
    Checks to see if every item in iterable is in iterable_superset.
    """
    for item in iterable:
        if item not in iterable_superset:
            return False
    return True

def gen_symbols_samples(symbols, samples, sample_from):
    """
    Generates a list of dictionaries mapping variable names to values.

    The symbols argument will usually be config['variables']
    or config['functions'].

    Usage
    =====
    >>> variable_samples = gen_symbols_samples(
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
    # Separate independent and dependent symbols
    independent = [
        symbol for symbol in symbols
        if not isinstance(sample_from[symbol], DependentSampler)
    ]

    # Generate the samples
    sample_list = []
    for _ in range(samples):
        # Generate independent samples
        sample_dict = {symbol: sample_from[symbol].gen_sample() for symbol in independent}

        # Generate dependent samples, following chains as necessary
        unevaluated_dependents = {
            symbol: sample_from[symbol].config['depends'] for symbol in symbols
            if isinstance(sample_from[symbol], DependentSampler)
        }
        while unevaluated_dependents:
            progress_made = False
            for symbol, dependencies in unevaluated_dependents.items():
                if is_subset(dependencies, sample_dict):
                    sample_dict[symbol] = sample_from[symbol].compute_sample(sample_dict)
                    del unevaluated_dependents[symbol]
                    progress_made = True

            if not progress_made:
                bad_symbols = ", ".join(sorted(unevaluated_dependents.keys()))
                raise ConfigError("Circularly dependent DependentSamplers detected: " +
                                  bad_symbols)

        sample_list.append(sample_dict)
    return sample_list

def construct_functions(whitelist, blacklist, user_funcs):
    """
    Returns the dictionary of available functions

    Arguments:
        whitelist (list): List of function names to allow, ignored if empty.
            To disallow all functions, use whitelist = [None].

        blacklist (list): List of function names to disallow. whitelist and blacklist
            cannot be used in conjunction.

        user_funcs (dict): Dictionary of "name": function pairs specifying user-defined
            functions to include.

    Usage
    =====
    By default, just returns DEFAULT_FUNCTIONS
    >>> funcs, random_funcs = construct_functions([], [], {})
    >>> funcs == DEFAULT_FUNCTIONS
    True
    >>> random_funcs == {}
    True

    To remove all functions, pass in a whitelist of [None]
    >>> funcs, random_funcs = construct_functions([None], [], {})
    >>> funcs == {}
    True

    Whitelisting specifies exactly what functions are allowed
    >>> funcs, random_funcs = construct_functions(["sin"], [], {})
    >>> funcs == {"sin": np.sin}
    True

    Blacklisting removes a function from the list
    >>> funcs, random_funcs = construct_functions([], ["sin"], {})
    >>> funcs.get("sin", None) is None
    True
    >>> funcs["cos"] == np.cos
    True

    You can specify user-defined functions
    >>> func = lambda x: x
    >>> randfunc = RandomFunction()
    >>> funcs, random_funcs = construct_functions([], [], {"f": func, "g": randfunc})
    >>> funcs["f"] == func
    True
    >>> random_funcs["g"] == randfunc
    True
    """
    if whitelist:
        if blacklist:
            raise ConfigError("Cannot whitelist and blacklist at the same time")

        functions = {}
        for f in whitelist:
            if f is None:
                # This allows for you to have whitelist = [None], which removes
                # all functions from the function list
                continue
            try:
                functions[f] = DEFAULT_FUNCTIONS[f]
            except KeyError:
                raise ConfigError("Unknown function in whitelist: " + f)
    else:
        # Treat no blacklist as blacklisted with an empty list
        functions = DEFAULT_FUNCTIONS.copy()
        for f in blacklist:
            try:
                del functions[f]
            except KeyError:
                raise ConfigError("Unknown function in blacklist: " + f)

    # Add in any custom functions to the functions and random_funcs lists
    random_funcs = {}
    for f in user_funcs:
        if not isinstance(f, str):
            msg = str(f) + " is not a valid name for a function (must be a string)"
            raise ConfigError(msg)
        # Check if we have a random function or a normal function
        if isinstance(user_funcs[f], list):
            # A list of functions; convert to a SpecificFunctions class
            random_funcs[f] = SpecificFunctions(user_funcs[f])
        elif isinstance(user_funcs[f], FunctionSamplingSet):
            random_funcs[f] = user_funcs[f]
        else:
            # f is a normal function
            functions[f] = user_funcs[f]

    return functions, random_funcs

def construct_constants(user_consts):
    """
    Returns the dictionary of available constants
    user_consts is a dictionary of "name": value pairs of constants to add to the defaults

    Usage
    =====
    >>> construct_constants({})
    {'i': 1j, 'pi': 3.141592653589793, 'e': 2.718281828459045, 'j': 1j}
    >>> construct_constants({"T": 1.5})
    {'i': 1j, 'pi': 3.141592653589793, 'e': 2.718281828459045, 'T': 1.5, 'j': 1j}
    """
    constants = DEFAULT_VARIABLES.copy()

    # Add in any user constants
    for var in user_consts:
        if not isinstance(var, str):
            msg = str(var) + " is not a valid name for a constant (must be a string)"
            raise ConfigError(msg)
        constants[var] = user_consts[var]

    return constants

def construct_suffixes(metric=False):
    """
    Returns the dictionary of available suffixes.
    Setting metric=True adds in the metric suffixes.

    Usage
    =====
    >>> construct_suffixes()
    {'%': 0.01}
    >>> suff = construct_suffixes(True)
    >>> suff['G'] == 1e9
    True
    """
    suffixes = DEFAULT_SUFFIXES.copy()
    if metric:
        suffixes.update(METRIC_SUFFIXES)
    return suffixes
