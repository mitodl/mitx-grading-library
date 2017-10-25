"""
Classes for numerical and formula graders
* NumericalGrader
* FormulaGrader

Also defines classes for sampling values
* RealInterval
* IntegerRange
* DiscreteSet
* ComplexRectangle
* ComplexSector
and for specifying functions
* SpecificFunctions
* RandomFunction
"""
from __future__ import division
from numbers import Number
import abc
import random
import numpy as np
from graders.baseclasses import ObjectWithSchema, ItemGrader, ConfigError
from graders.voluptuous import Schema, Required, Any, All, Extra
from graders.helpers.calc import (UndefinedVariable, UndefinedFunction,
                                  UnmatchedParentheses, evaluator)
from graders.helpers.validatorfuncs import (Positive, NonNegative, PercentageString,
                                            NumberRange, ListOfType, TupleOfType, is_callable)
from graders.helpers.mathfunc import (DEFAULT_FUNCTIONS, DEFAULT_VARIABLES,
                                      DEFAULT_SUFFIXES, METRIC_SUFFIXES, within_tolerance)

# Set the objects to be imported from this grader
__all__ = [
    "NumericalGrader",
    "FormulaGrader",
    "RealInterval",
    "IntegerRange",
    "DiscreteSet",
    "ComplexRectangle",
    "ComplexSector",
    "SpecificFunctions",
    "RandomFunction",
    "UndefinedVariable",
    "UndefinedFunction",
    "UnmatchedParentheses",
    "InvalidInput"
]

class InvalidInput(Exception):
    """Handles special exceptions"""
    pass


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


class RealInterval(VariableSamplingSet):
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

    Specify start and stop or [start, stop] to initialize.

    Both start and stop are included in the interval.

    Usage
    =====
    Generate 5 random floats betweens -2 and 4
    >>> integer = IntegerRange(start=-2, stop=4)
    >>> integer.gen_sample() in list(range(-2,5))
    True

    You can also initialize with an interval:
    >>> integer = IntegerRange([-2,4])
    >>> integer.gen_sample() in list(range(-2,5))
    True

    The default is start=1, stop=5:
    >>> integer = IntegerRange()
    >>> integer.gen_sample() in list(range(1,6))
    True
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


class ComplexSector(VariableSamplingSet):
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
    random amplitude, frequency and phase. You can control the center and amplitude of
    the resulting oscillations by specifying center and amplitude.

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


class DiscreteSet(VariableSamplingSet):  # pylint: disable=too-few-public-methods
    """
    Represents a discrete set of values from which to sample.

    Can be initialized with a single value or a non-empty tuple of values.

    Note that we use a tuple instead of a list so that [0,1] isn't confused with (0,1).
    We would use a set, but unfortunately voluptuous doesn't work with sets.

    Usage
    =====
    >>> values = DiscreteSet(3.142)
    >>> values.gen_sample() == 3.142
    True
    >>> values = DiscreteSet((1,2,3,4))
    >>> values.gen_sample() in (1,2,3,4)
    True
    """

    # Take in an individual or tuple of numbers
    schema_config = Schema(TupleOfType(Number))

    def gen_sample(self):
        """Return a random entry from the given set"""
        return random.choice(self.config)


class SpecificFunctions(FunctionSamplingSet):  # pylint: disable=too-few-public-methods
    """
    Represents a set of user-defined functions for use in a grader, one of which will
    be randomly selected. A single function can be provided here, but this is intended
    for lists of functions to be randomly sampled from.

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
    """
    Grades mathematical expressions.

    Similar to edX numericalresponse but much more flexible. Allows author to white/blacklist
    functions, as well as specify user functions and forbidden strings.
    A flag for metric affixes is provided.
    """

    @property
    def schema_config(self):
        """Define the configuration options for NumericalGrader"""
        # Construct the default ItemGrader schema
        schema = super(NumericalGrader, self).schema_config
        # Append options
        forbidden_default = "Invalid Input: This particular answer is forbidden"
        return schema.extend({
            Required('user_functions', default={}): {Extra: is_callable},
            Required('user_constants', default={}): {Extra: Number},
            Required('blacklist', default=[]): [str],
            Required('whitelist', default=[]): [Any(str, None)],
            Required('forbidden_strings', default=[]): [str],
            Required('forbidden_message', default=forbidden_default): str,
            Required('required_functions', default=[]): [str],
            Required('tolerance', default='0.1%'): Any(Positive(Number), PercentageString),
            Required('case_sensitive', default=True): bool,
            Required('metric_suffixes', default=False): bool
        })

    def __init__(self, config=None, **kwargs):
        """
        Validate the specified configuration.
        First apply the voluptuous validation.
        Next, construct the lists of functions, variables and suffixes.
        """
        super(NumericalGrader, self).__init__(config, **kwargs)

        self.functions = self.construct_functions(self.config["whitelist"],
                                                  self.config["blacklist"],
                                                  self.config["user_functions"])
        self.constants = self.construct_constants(self.config["user_constants"])
        self.suffixes = self.construct_suffixes(self.config["metric_suffixes"])

    @staticmethod
    def construct_functions(whitelist, blacklist, user_funcs):
        """Returns the list of available functions, based on the given configuration"""
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

        # Add in any custom functions
        for f in user_funcs:
            if not isinstance(f, str):
                msg = str(f) + " is not a valid name for a function (must be a string)"
                raise ConfigError(msg)
            functions[f] = user_funcs[f]

        return functions

    @staticmethod
    def construct_constants(user_consts):
        """Returns the list of available constants, based on the given configuration"""
        constants = DEFAULT_VARIABLES.copy()

        # Add in any user constants
        for var in user_consts:
            if not isinstance(var, str):
                msg = str(var) + " is not a valid name for a constant (must be a string)"
                raise ConfigError(msg)
            constants[var] = user_consts[var]

        return constants

    @staticmethod
    def construct_suffixes(metric=False):
        """Returns the list of available suffixes, based on the given configuration"""
        suffixes = DEFAULT_SUFFIXES.copy()
        if metric:
            suffixes.update(METRIC_SUFFIXES)
        return suffixes

    def check_response(self, answer, student_input):
        """Check the student response against a given answer"""
        # First, check for forbidden strings
        # Remove whitespace so that students can't trick this check by adding any
        check = student_input if self.config["case_sensitive"] else student_input.lower()
        check = "".join([char for char in check if char != " "])
        for x in self.config["forbidden_strings"]:
            forbid = x if self.config["case_sensitive"] else x.lower()
            if forbid in check:
                # Don't give away the specific string that is being checked for!
                raise InvalidInput(self.config["forbidden_message"])

        # Now perform the computations
        try:
            return self.raw_check(answer, student_input)

        # And now for all of the things that could possibly have gone wrong...
        except UndefinedVariable as e:
            message = "Invalid Input: {varname} not permitted in answer as a variable"
            raise UndefinedVariable(message.format(varname=str(e)))

        except UndefinedFunction as e:
            funcnames = e.args[0]
            valid_var = e.args[1]
            message = "Invalid Input: {varname} not permitted in answer as a function"
            if valid_var:
                message += " (did you forget to use * for multiplication?)"
            raise UndefinedFunction(message.format(varname=funcnames))

        except UnmatchedParentheses:
            # The error message is already written for this error
            raise

        except ValueError as err:
            if 'factorial' in err.message:
                # This is thrown when fact() or factorial() is used
                # that tests on negative and/or non-integer inputs
                # err.message will be: `factorial() only accepts integral values` or
                # `factorial() not defined for negative values`
                raise InvalidInput("Error evaluating factorial() or fact() in input. "
                                   "These functions can only be used on positive integers.")
            elif self.config["debug"]:
                # Check if debug mode is on
                raise
            else:
                # Otherwise, give a generic error message
                msg = "Invalid Input: Could not parse '{}' as a formula"
                raise InvalidInput(msg.format(student_input))

        except Exception as err:
            # Reraise InvalidInput messages
            if isinstance(err, InvalidInput):
                raise
            # Check if debug mode is on
            if self.config["debug"]:
                raise
            # Otherwise, give a generic error message
            msg = "Invalid Input: Could not parse '{}' as a formula"
            raise InvalidInput(msg.format(student_input))

    def raw_check(self, answer, student_input):
        """Perform the numerical check of student_input vs answer"""
        expected, _ = evaluator(formula=answer['expect'],
                                case_sensitive=self.config['case_sensitive'],
                                variables=self.constants,
                                functions=self.functions,
                                suffixes=self.suffixes)

        student, used_funcs = evaluator(student_input,
                                        case_sensitive=self.config['case_sensitive'],
                                        variables=self.constants,
                                        functions=self.functions,
                                        suffixes=self.suffixes)

        # Check that the required functions are used
        for f in self.config["required_functions"]:
            ftest = f
            if not self.config['case_sensitive']:
                ftest = f.lower()
                used_funcs = [x.lower() for x in used_funcs]
            if ftest not in used_funcs:
                msg = "Invalid Input: Answer must contain the function {}"
                raise InvalidInput(msg.format(f))

        # Check if the answers agree
        if not within_tolerance(expected, student, self.config['tolerance']):
            return {'ok': False, 'grade_decimal': 0, 'msg': ''}

        # This response appears to agree with the expected answer
        return {
            'ok': answer['ok'],
            'grade_decimal': answer['grade_decimal'],
            'msg': answer['msg']
        }


class FormulaGrader(NumericalGrader):
    """
    Grades mathematical expressions.

    Like NumericalGrader, but allows for variables that are randomly sampled repeatedly
    in order to determine correctness. Also allows for randomly sampled functions.

    Usage
    =====
    Grade a formula containing variables and functions:
    >>> grader = FormulaGrader(
    ...     answers='a*b + f(c-b) + f(g(a))',
    ...     variables=['a', 'b','c'],
    ...     random_functions=['f', 'g']
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
    ...     random_functions=['f', 'g'],
    ...     samples=3,
    ...     sample_from={
    ...         'a': [-4,1]
    ...     },
    ...     tolerance=0.1
    ... )
    >>> theinput = "b*b - 0.25*f(g(a))"
    >>> grader(None, theinput)['ok']
    True

    You can also provide specific functions using the user_functions key:
    >>> def square(x):
    ...     return x**2
    >>> grader = FormulaGrader(
    ...     answers='4*f(a)+b',
    ...     variables=['a','b'],
    ...     user_functions={
    ...         'f': square
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
    @property
    def schema_config(self):
        """Define the configuration options for FormulaGrader"""
        # Construct the default NumericalGrader schema
        schema = super(FormulaGrader, self).schema_config
        # Append options
        return schema.extend({
            Required('samples', default=5): Positive(int),
            Required('variables', default=[]): [str],
            Required('sample_from', default={}): dict,
            Required('random_functions', default=[]): [str],
            Required('functions_from', default={}): dict,
            Required('failable_evals', default=0): NonNegative(int)
        })

    def __init__(self, config=None, **kwargs):
        """
        Validate the Formulagrader's configuration.
        First, we allow the NumericalGrader initializer to construct the function list.
        Second, we refine the sample_from and random_functions_from entries.
        These two are separate so that there are no name collisions.
        """
        super(FormulaGrader, self).__init__(config, **kwargs)

        # Construct the schema for sample_from
        # First, accept all VariableSamplingSets
        # Then, accept any list that RealInterval can interpret
        # Finally, single numbers or tuples of numbers will be handled by DiscreteSet
        schema_sample_from = Schema({
            Required(varname, default=RealInterval()):
                Any(VariableSamplingSet,
                    All(list, lambda pair: RealInterval(pair)),
                    lambda tup: DiscreteSet(tup))
            for varname in self.config['variables']
        })
        self.config['sample_from'] = schema_sample_from(self.config['sample_from'])
        # Note that voluptuous ensures that there are no orphaned entries in sample_from

        # Construct the schema for random_functions_from
        # This can be given a FunctionSamplingSet, just a function, or a list of functions
        schema_functions_from = Schema({
            Required(funcname, default=RandomFunction()):
                Any(FunctionSamplingSet,
                    lambda func: SpecificFunctions(func))
            for funcname in self.config['random_functions']
        })
        self.config['functions_from'] = schema_functions_from(self.config['functions_from'])

    def raw_check(self, answer, student_input):
        """Perform the numerical check of student_input vs answer"""
        var_samples = self.gen_symbols_samples(self.config['variables'],
                                               self.config['samples'],
                                               self.config['sample_from'])

        func_samples = self.gen_symbols_samples(self.config['random_functions'],
                                                self.config['samples'],
                                                self.config['functions_from'])

        # Make a copy of the functions and variables lists
        # We'll add the sampled functions/variables in
        funclist = self.functions.copy()
        varlist = self.constants.copy()

        num_failures = 0
        for i in range(self.config['samples']):
            # Update the functions and variables listings with this sample
            funclist.update(func_samples[i])
            varlist.update(var_samples[i])

            # Compute expressions
            expected, _ = evaluator(formula=answer['expect'],
                                    case_sensitive=self.config['case_sensitive'],
                                    variables=varlist,
                                    functions=funclist,
                                    suffixes=self.suffixes)

            student, used_funcs = evaluator(student_input,
                                            case_sensitive=self.config['case_sensitive'],
                                            variables=varlist,
                                            functions=funclist,
                                            suffixes=self.suffixes)

            # Check that the required functions are used
            # But only the first time!
            if i == 0:
                for f in self.config["required_functions"]:
                    ftest = f
                    if not self.config['case_sensitive']:
                        ftest = f.lower()
                        used_funcs = [x.lower() for x in used_funcs]
                    if ftest not in used_funcs:
                        msg = "Invalid Input: Answer must contain the function {}"
                        raise InvalidInput(msg.format(f))

            # Check if expressions agree
            if not within_tolerance(expected, student, self.config['tolerance']):
                num_failures += 1
                if num_failures > self.config["failable_evals"]:
                    return {'ok': False, 'grade_decimal': 0, 'msg': ''}

        # This response appears to agree with the expected answer
        return {
            'ok': answer['ok'],
            'grade_decimal': answer['grade_decimal'],
            'msg': answer['msg']
        }

    @staticmethod
    def gen_symbols_samples(symbols, samples, sample_from):
        """
        Generates a list of dictionaries mapping variable names to values.

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
