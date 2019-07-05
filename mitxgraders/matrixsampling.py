"""
matrixsampling.py

Contains classes for sampling vector/matrix/tensor values:
* RealVectors
* ComplexVectors
* RealMatrices
* ComplexMatrices
* RealTensors
* ComplexTensors
* IdentityMatrixMultiples
* SquareMatrices
* OrthogonalMatrices
* UnitaryMatrices
All of these classes perform random sampling. To obtain a sample, use class.gen_sample()
"""
from __future__ import division
import abc
import numpy as np

class Unavailable(object):
    def rvs(self, dimension):
        raise NotImplementedError('This feature requires newer versions of numpy '
                                  'and scipy than are available.')

try:
    from scipy.stats import ortho_group, special_ortho_group, unitary_group
except ImportError:
    ortho_group = Unavailable()
    special_ortho_group = Unavailable()
    unitary_group = Unavailable()

from voluptuous import Schema, Required, All, Coerce, Any, Range

from mitxgraders.exceptions import ConfigError
from mitxgraders.sampling import VariableSamplingSet, RealInterval, ScalarSamplingSet
from mitxgraders.helpers.validatorfuncs import NumberRange, is_shape_specification
from mitxgraders.helpers.calc import MathArray

# Set the objects to be imported from this grader
__all__ = [
    "RealVectors",
    "ComplexVectors",
    "RealMatrices",
    "ComplexMatrices",
    "RealTensors",
    "ComplexTensors",
    "IdentityMatrixMultiples",
    "SquareMatrices",
    "OrthogonalMatrices",
    "UnitaryMatrices"
]

class Retry(Exception):
    """
    Raised to indicate that the randomly generated array cannot satisfy the desired
    constraints, and a new random draw should be taken.
    """


class ArraySamplingSet(VariableSamplingSet):
    """
    Represents a set from which random array variable samples are taken.

    The norm used is standard Euclidean norm: root-sum of all entries in the array.

    This is the most low-level array sampling set we have, and is subclassed for various
    specific purposes.

    Config:
    =======
        - shape (int|(int)|[int]): Dimensions of the array, specified as a list or tuple of
            the dimensions in each index as (n_1, n_2, ...). Can also use an integer
            to select a vector of that length. (required; no default)
        - norm ([start, stop]): Range for the overall norm of the array. Can be a
            list [start, stop] or a dictionary {'start':start, 'stop':stop}.
            (default [1, 5])
        - complex (bool): Whether or not the matrix is complex (default False)
    """
    # This is an abstract base class
    __metaclass__ = abc.ABCMeta

    schema_config = Schema({
        Required('shape'): is_shape_specification(min_dim=1),
        Required('norm', default=[1, 5]): NumberRange(),
        Required('complex', default=False): bool
    })

    def __init__(self, config=None, **kwargs):
        """
        Configure the class as normal, then set up norm as a RealInterval
        """
        super(ArraySamplingSet, self).__init__(config, **kwargs)
        self.norm = RealInterval(self.config['norm'])

    def gen_sample(self):
        """
        Generates an array sample and returns it as a MathArray.

        This calls generate_sample, which is the routine that should be subclassed if
        needed, rather than this one.
        """
        array = self.generate_sample()
        return MathArray(array)

    def generate_sample(self):
        """
        Generates a random array of shape and norm determined by config. After
        generation, the apply_symmetry and normalize functions are applied to the result.
        These functions may be shadowed by a subclass.

        If apply_symmetry or normalize raise the Retry exception, a new sample is
        generated, and the procedure starts anew.

        Returns a numpy array.
        """
        # Loop until a good sample is found
        loops = 0
        while loops < 100:
            loops += 1

            # Construct an array with entries in [-0.5, 0.5)
            array = np.random.random_sample(self.config['shape']) - 0.5
            # Make the array complex if needed
            if self.config['complex']:
                imarray = np.random.random_sample(self.config['shape']) - 0.5
                array = array + 1j*imarray

            try:
                # Apply any symmetries to the array
                array = self.apply_symmetry(array)

                # Normalize the result
                array = self.normalize(array)

                # Return the result
                return array
            except Retry:
                continue

        raise ValueError('Unable to construct sample for {}'
                         .format(type(self).__name__))  # pragma: no cover

    def apply_symmetry(self, array):
        """
        Applies the required symmetries to the array.

        This method exists to be shadowed by subclasses.
        """
        return array

    def normalize(self, array):
        """
        Normalizes the array to fall into the desired norm.

        This method can be shadowed by subclasses.
        """
        actual_norm = np.linalg.norm(array)
        desired_norm = self.norm.gen_sample()
        return array * desired_norm / actual_norm


class VectorSamplingSet(ArraySamplingSet):
    """
    Sampling set of vectors. This is an abstract class; you should use RealVectors or
    ComplexVectors instead.

    Config:
    =======
        Same as ArraySamplingSet, but:
            - shape can be a plain integer indicating number of components
            - if shape is tuple/list, must have length 1
            - default shape is (3, ), for a 3D vector
    """
    # This is an abstract base class
    __metaclass__ = abc.ABCMeta

    schema_config = ArraySamplingSet.schema_config.extend({
        Required('shape', default=(3,)): is_shape_specification(min_dim=1, max_dim=1)
    })


class RealVectors(VectorSamplingSet):
    """
    Sampling set of real vectors.

    Config:
    =======
        Same as VectorSamplingSet, but:
            - complex is always False

    Usage:
    ======

    By default, vectors have 3 components:
    >>> vectors = RealVectors()
    >>> vectors.gen_sample().shape
    (3,)
    """
    schema_config = VectorSamplingSet.schema_config.extend({
        Required('complex', default=False): False
    })


class ComplexVectors(VectorSamplingSet):
    """
    Sampling set of complex vectors.

    Config:
    =======
        Same as VectorSamplingSet, but:
            - complex is always True

    Usage:
    ======

    Complex vectors have complex components:
    >>> vectors = ComplexVectors()
    >>> v = vectors.gen_sample()
    >>> np.array_equal(v, np.conj(v))
    False
    """
    schema_config = VectorSamplingSet.schema_config.extend({
        Required('complex', default=True): True
    })


class TensorSamplingSet(ArraySamplingSet):
    """
    Sampling set of tensors. This is an abstract class; you should use RealTensors or
    ComplexTensors instead.

    Config:
    =======
        Same as ArraySamplingSet, but:
            - shape must be a tuple with at least 3 dimensions
    """
    # This is an abstract base class
    __metaclass__ = abc.ABCMeta

    schema_config = ArraySamplingSet.schema_config.extend({
        Required('shape'): is_shape_specification(min_dim=3)
    })


class RealTensors(TensorSamplingSet):
    """
    Sampling set of real tensors.

    Config:
    =======
        Same as TensorSamplingSet, but:
            - complex is always False

    Usage:
    ======
    Sample tensors with shape [4, 2, 5]:
    >>> real_tensors = RealTensors(shape=[4, 2, 5])
    >>> sample = real_tensors.gen_sample()
    >>> sample.shape
    (4, 2, 5)

    Samples are of class MathArray:
    >>> isinstance(sample, MathArray)
    True

    Specify a range for the tensor's norm:
    >>> real_tensors = RealTensors(shape=[4, 2, 5], norm=[10, 20])
    >>> sample = real_tensors.gen_sample()
    >>> 10 < np.linalg.norm(sample) < 20
    True

    """
    schema_config = TensorSamplingSet.schema_config.extend({
        Required('complex', default=False): False
    })


class ComplexTensors(TensorSamplingSet):
    """
    Sampling set of complex tensors.

    Config:
    =======
        Same as TensorSamplingSet, but:
            - complex is always True

    Usage:
    ======
    Sample tensors with shape [4, 2, 5]:
    >>> tensors = ComplexTensors(shape=[4, 2, 5])
    >>> t = tensors.gen_sample()
    >>> t.shape
    (4, 2, 5)

    Complex tensors have complex components:
    >>> np.array_equal(t, np.conj(t))
    False

    """
    schema_config = TensorSamplingSet.schema_config.extend({
        Required('complex', default=True): True
    })


class MatrixSamplingSet(ArraySamplingSet):
    """
    Base sampling set of matrices. This is an abstract base class; you should
    use a more specific subclass instead.

    Config:
    =======
        Same as ArraySamplingSet, but:
            - shape must be a tuple/list with length 2
            - default shape is (2, 2), for a 2x2 matrix

    """
    # This is an abstract base class
    __metaclass__ = abc.ABCMeta

    schema_config = ArraySamplingSet.schema_config.extend({
        Required('shape', default=(2, 2)): is_shape_specification(min_dim=2, max_dim=2)
    })


class GeneralMatrices(MatrixSamplingSet):
    """
    Base sampling set of general matrices. This is an abstract base class; you
    should use RealMatrices or ComplexMatrices instead.

    Config:
    =======
        Same as MatrixSamplingSet, but:
            - triangular (None, 'upper', 'lower'): Specify if you want a triangular
                matrix (default None)
    """
    # This is an abstract base class
    __metaclass__ = abc.ABCMeta

    schema_config = MatrixSamplingSet.schema_config.extend({
        Required('triangular', default=None): Any(None, 'upper', 'lower')
    })

    def apply_symmetry(self, array):
        """Impose the triangular requirement on the array"""
        if self.config['triangular'] is 'upper':
            return np.triu(array)
        elif self.config['triangular'] is 'lower':
            return np.tril(array)
        return array


class RealMatrices(GeneralMatrices):
    """
    Sampling set of real matrices.

    Config:
    =======
        Same as GeneralMatrices, but:
            - complex is always False

    Usage:
    ======

    By default, matrices have two rows and two columns:
    >>> matrices = RealMatrices()
    >>> matrices.gen_sample().shape
    (2, 2)

    We can generate upper triangular matrices:
    >>> from mitxgraders.helpers.calc import within_tolerance
    >>> matrices = RealMatrices(triangular='upper')
    >>> m = matrices.gen_sample()
    >>> within_tolerance(m, MathArray(np.triu(m)), 0)
    True

    and lower triangular matrices:
    >>> matrices = RealMatrices(triangular='lower')
    >>> m = matrices.gen_sample()
    >>> within_tolerance(m, MathArray(np.tril(m)), 0)
    True

    """
    schema_config = GeneralMatrices.schema_config.extend({
        Required('complex', default=False): False
    })


class ComplexMatrices(GeneralMatrices):
    """
    Sampling set of complex matrices.

    Config:
    =======
        Same as GeneralMatrices, but:
            - complex is always True

    Usage:
    ======

    Complex matrices have complex components:
    >>> matrices = ComplexMatrices()
    >>> m = matrices.gen_sample()
    >>> np.array_equal(m, np.conj(m))
    False
    """
    schema_config = GeneralMatrices.schema_config.extend({
        Required('complex', default=True): True
    })


class SquareMatrixSamplingSet(MatrixSamplingSet):
    """
    Base sampling set of square matrices. This is an abstract base class. You want to use
    a subclass instead (likely SquareMatrices).

    Config:
    =======
        Same as MatrixSamplingSet, but:
            - dimension (int, min 2): Dimension of the matrix (minimum 2).

    The 'shape' property is not used.
    """
    # This is an abstract base class
    __metaclass__ = abc.ABCMeta

    schema_config = MatrixSamplingSet.schema_config.extend({
        Required('shape', default=None): None,
        Required('dimension', default=2): All(int, Range(2, float('inf')))
    })

    def __init__(self, config=None, **kwargs):
        """
        Configure the class as normal, then modify the shape appropriately
        """
        super(SquareMatrixSamplingSet, self).__init__(config, **kwargs)
        self.config['shape'] = (self.config['dimension'], self.config['dimension'])


class IdentityMatrixMultiples(SquareMatrixSamplingSet):
    """
    Class representing a collection of multiples of the identity matrix
    of a given dimension.

    Config:
    =======
        Same as MatrixSamplingSet, but:
            - sampler: A scalar sampling set for the multiplicative constant
                (default [1, 5])

    Note that the 'complex' and 'norm' properties are ignored.

    Usage:
    ======

    By default, we generate 2x2 matrices:
    >>> matrices = IdentityMatrixMultiples()
    >>> matrices.gen_sample().shape
    (2, 2)

    We can generate NxN matrices by specifying the dimension:
    >>> matrices = IdentityMatrixMultiples(dimension=4)
    >>> matrices.gen_sample().shape
    (4, 4)

    The scalar multiple can be generated in a number of ways:
    >>> from mitxgraders import ComplexSector
    >>> matrices = IdentityMatrixMultiples(sampler=[1,3])
    >>> sect = ComplexSector(modulus=[0,1], argument=[-np.pi,np.pi])
    >>> matrices = IdentityMatrixMultiples(sampler=sect)

    The resulting samples are simply a scalar times the identity matrix:
    >>> matrices = IdentityMatrixMultiples()
    >>> m = matrices.gen_sample()
    >>> np.array_equal(m, m[0, 0] * np.eye(2))
    True

    """
    # Sampling set for the multiplicative constant
    # Accept anything that FormulaGrader would accept for a sampling set, restricted to
    # scalar sampling sets. Hence, ScalarSamplingSets and ranges are allowed.
    # Note: Does not support DependentSampler or DiscreteSet, as they are not guaranteed
    # to return a scalar value.
    schema_config = SquareMatrixSamplingSet.schema_config.extend({
        Required('sampler', default=RealInterval()): Any(ScalarSamplingSet,
                                                         All(list, Coerce(RealInterval)))
    })

    def generate_sample(self):
        """
        Generates an identity matrix of specified dimension multiplied by a random scalar
        """
        # Sample the multiplicative constant
        scaling = self.config['sampler'].gen_sample()
        # Create the numpy matrix
        array = scaling * np.eye(self.config['dimension'])
        # Return the result
        return array


class SquareMatrices(SquareMatrixSamplingSet):
    """
    Sampling set for square matrices. Various symmetry properties are possible, including
    diagonal, symmetric, antisymmetric, hermitian and antihermitian. The trace and
    determinant can also be controlled.

    There are four kinds of special square matrices that covered by other sampling sets:
        * OrthogonalMatrices
        * UnitaryMatrices
        * Multiples of the identity (use IdentityMatrixMultiples)
        * Triangular matrices (use RealMatrices or ComplexMatrices)

    Our approach to generating these matrices is to first generate a random real/complex
    matrix of the appropriate shape, and then enforce, in order:
        * diagonal/symmetric/antisymmetric/hermitian/antihermitian
        * tracelessness
        * determinant 0 or 1
        * norm (if determinant != 1)
    The determinant step is sometimes problematic. To achieve unit determinant, we attempt
    to rescale the matrix. This can't always be done, and we try a new random generation
    in such cases. To achieve zero determinant, we attempt to subtract lambda*I from the
    matrix. This can't be done for antisymmetric or traceless matrices while preserving
    those properties.

    Some special cases that don't exist:
        * Real, diagonal, traceless, unit determinant, 2x2 matrix
        * Real, symmetric, traceless, unit determinant, 2x2 matrix
        * Hermitian, traceless, unit determinant, 2x2 matrix
        * Odd-dimension, unit-determinant antisymmetric matrix
        * Odd-dimension, unit-determinant antihermitian matrix

    Config:
    =======
        Same as SquareMatrixSamplingSet, but:
            - symmetry (None, 'diagonal', 'symmetric', 'antisymmetric',
                'hermitian', 'antihermitian'): Entry describing the desired
                symmetry of the matrix. Note: If 'hermitian' or 'antihermitian'
                are chosen, 'complex' is set to True. (default None)
            - traceless (bool): Whether or not to ensure the matrix is traceless
                (default False)
            - determinant (None, 0, 1): If set to 0 or 1, sets the determinant of the
                matrix to be 0 or 1 correspondingly. If None or 0, uses 'norm' to
                normalize the matrix.

    Usage:
    ======
    By default, we generate real 2x2 matrices with no symmetry:
    >>> matrices = SquareMatrices()
    >>> mat = matrices.gen_sample()
    >>> mat.shape
    (2, 2)
    >>> np.array_equal(mat, np.conj(mat))
    True

    We can make it NxN by specifying the dimension:
    >>> matrices = SquareMatrices(dimension=4)
    >>> matrices.gen_sample().shape
    (4, 4)

    Some combinations: diagonal, complex, traceless and unit determinant
    >>> from mitxgraders.helpers.calc import within_tolerance
    >>> matrices = SquareMatrices(symmetry='diagonal', complex=True, traceless=True,
    ...                           determinant=1)
    >>> mat = matrices.gen_sample()
    >>> np.array_equal(np.diag(np.diag(mat)), mat)      # Diagonal
    True
    >>> np.array_equal(mat, np.conj(mat))               # Complex
    False
    >>> within_tolerance(mat.trace(), 0, 1e-14)         # Traceless
    True
    >>> within_tolerance(np.linalg.det(mat), 1, 1e-14)  # Unit determinant
    True

    More combinations: symmetric, real, zero determinant and norm in [6, 10]
    >>> matrices = SquareMatrices(symmetry='symmetric', determinant=0, norm=[6, 10])
    >>> mat = matrices.gen_sample()
    >>> np.array_equal(mat, mat.T)                      # Symmetric
    True
    >>> np.array_equal(mat, np.conj(mat))               # Real
    True
    >>> within_tolerance(np.linalg.det(mat), 0, 1e-13)  # Zero determinant
    True
    >>> 6 <= np.linalg.norm(mat) <= 10                  # Norm in [6, 10]
    True

    More combinations: antisymmetric and complex
    >>> matrices = SquareMatrices(symmetry='antisymmetric', complex=True)
    >>> mat = matrices.gen_sample()
    >>> np.array_equal(mat, -mat.T)                     # Antisymmetric
    True
    >>> np.array_equal(mat, np.conj(mat))               # Complex
    False

    More combinations: hermitian (enforces complex), zero determinant and norm in [6, 10]
    >>> matrices = SquareMatrices(symmetry='hermitian', determinant=0, norm=[6, 10])
    >>> mat = matrices.gen_sample()
    >>> np.array_equal(mat, np.conj(mat.T))             # Hermitian
    True
    >>> within_tolerance(np.linalg.det(mat), 0, 1e-13)  # Zero determinant
    True
    >>> 6 <= np.linalg.norm(mat) <= 10                  # Norm in [6, 10]
    True

    More combinations: antihermitian (enforces complex), unit determinant and traceless
    >>> matrices = SquareMatrices(symmetry='antihermitian', determinant=1, traceless=True)
    >>> mat = matrices.gen_sample()
    >>> np.array_equal(mat, -np.conj(mat.T))            # Antihermitian
    True
    >>> within_tolerance(np.linalg.det(mat), 1, 1e-13)  # Unit determinant
    True
    >>> within_tolerance(mat.trace(), 0, 1e-14)         # Traceless
    True

    """
    schema_config = SquareMatrixSamplingSet.schema_config.extend({
        Required('symmetry', default=None): Any(None, 'diagonal', 'symmetric',
                                                'antisymmetric', 'hermitian',
                                                'antihermitian'),
        Required('traceless', default=False): bool,
        Required('determinant', default=None): Any(None, 0, 1)
    })

    def __init__(self, config=None, **kwargs):
        """
        Configure the class as normal, then set complex for hermitian/antihermitian
        """
        super(SquareMatrices, self).__init__(config, **kwargs)
        if self.config['symmetry'] in ['hermitian', 'antihermitian']:
            self.config['complex'] = True

        # A couple of cases that we can't handle:
        if self.config['determinant'] == 0:
            if self.config['symmetry'] == 'antisymmetric':
                raise ConfigError("Unable to generate zero determinant antisymmetric matrices")
            if self.config['traceless']:
                raise ConfigError("Unable to generate zero determinant traceless matrices")
        if self.config['determinant'] == 1:
            if self.config['dimension'] == 2 and self.config['traceless']:
                if self.config['symmetry'] == 'diagonal' and not self.config['complex']:
                    raise ConfigError("No real, traceless, unit-determinant, diagonal 2x2 matrix exists")
                elif self.config['symmetry'] == 'symmetric' and not self.config['complex']:
                    raise ConfigError("No real, traceless, unit-determinant, symmetric 2x2 matrix exists")
                elif self.config['symmetry'] == 'hermitian':
                    raise ConfigError("No traceless, unit-determinant, Hermitian 2x2 matrix exists")
            if self.config['dimension'] % 2 == 1:  # Odd dimension
                if self.config['symmetry'] == 'antisymmetric':
                    # Eigenvalues are all imaginary, so determinant is imaginary
                    raise ConfigError("No unit-determinant antisymmetric matrix exists in odd dimensions")
                if self.config['symmetry'] == 'antihermitian':
                    # Eigenvalues are all imaginary, so determinant is imaginary
                    raise ConfigError("No unit-determinant antihermitian matrix exists in odd dimensions")

    def apply_symmetry(self, array):
        """
        Applies the required symmetries to the array
        """
        # Apply the symmetry property
        if self.config['symmetry'] == 'diagonal':
            working = np.diag(np.diag(array))
        elif self.config['symmetry'] == 'symmetric':
            working = array + array.transpose()
        elif self.config['symmetry'] == 'antisymmetric':
            working = array - array.transpose()
        elif self.config['symmetry'] == 'hermitian':
            working = array + np.conj(array.transpose())
        elif self.config['symmetry'] == 'antihermitian':
            working = array - np.conj(array.transpose())
        else:
            working = array

        # Apply the traceless property
        if self.config['traceless']:
            trace = np.trace(working)
            dim = self.config['dimension']
            working = working - trace / dim * np.eye(dim)

        return working

    def normalize(self, array):
        """
        Set either the norm or determinant of the matrix to the desired value.
        """
        if self.config['determinant'] == 1:
            # No need to normalize
            return self.make_det_one(array)
        elif self.config['determinant'] == 0:
            array = self.make_det_zero(array)
        return super(SquareMatrices, self).normalize(array)

    def make_det_one(self, array):
        """Scale an array to have unit determinant, or raise Retry if not possible"""
        det = np.linalg.det(array)
        # Have to treat different configuration cases separately
        if not self.config['complex']:
            if det > 0:
                # This is the easy case: Just scale the determinant
                return array / np.power(det, 1/self.config['dimension'])
            elif self.config['dimension'] % 2 == 1 and det < 0:
                # Odd-dimension matrices can also have their determinant scaled
                return - array / np.power(-det, 1/self.config['dimension'])
            else:
                # Even-dimension, real matrix: we can't rescale this to
                # set the determinant to unity. Also possible: zero determinant
                # (should basically never happen though, due to floating pointness!)
                raise Retry()
        else:
            # Complex matrices are generally easier
            # But certain symmetries can be problematic
            if self.config['symmetry'] in [None, 'diagonal',
                                           'symmetric', 'antisymmetric']:
                # Check to ensure that det isn't 0 before we get a division by zero
                if np.abs(det) < 1e-13:
                    raise Retry()  # pragma: no cover
                # We can just rescale the matrix
                return array / np.power(det + 0.0j, 1/self.config['dimension'])

            # If we get to here, det is real
            det = np.real(det)  # Get rid of numerical error
            if det > 0:
                # This is the easy case: Just scale the determinant
                return array / np.power(det, 1/self.config['dimension'])
            elif self.config['dimension'] % 2 == 1 and det < 0:
                # Odd-dimension matrices can also have their determinant scaled
                return - array / np.power(-det, 1/self.config['dimension'])
            else:
                # Can't rescale our way out of this one while maintaining the
                # desired symmetry
                raise Retry()

    def make_det_zero(self, array):
        """Modify an array to have zero determinant, or raise Retry if not possible"""
        if np.linalg.det(array) == 0:
            # This should never happen due to floating pointness. But just in case...
            return array  # pragma: no cover

        # Pick a random number!
        index = np.random.randint(self.config['dimension'])

        # What's our symmetry?
        if self.config['symmetry'] == 'diagonal':
            # Choose a random diagonal entry to be zero
            array[index, index] = 0
            return array
        elif self.config['symmetry'] in ['symmetric', 'hermitian']:
            # Eigenvalues are all real - use special algorithm to compute eigenvalues
            eigenvalues = np.linalg.eigvalsh(array)
        elif self.config['symmetry'] == 'antihermitian':
            # Eigenvalues are all imaginary
            # Temporarily convert the matrix into a hermitian matrix
            # and use the special algorithm
            eigenvalues = np.linalg.eigvalsh(1j * array)
            eigenvalues *= -1j
        else:
            # No relevant symmetry. Use a general algorithm to compute eigenvalues.
            eigenvalues = np.linalg.eigvals(array)
            if not self.config['complex']:
                # We need to select a real eigenvalue.
                idxs = np.where(np.abs(np.imag(eigenvalues)) < 1e-14)[0]
                # idxs now stores any indices that have real eigenvalues
                if len(idxs) == 0:
                    # No real eigenvalues. Try again.
                    raise Retry()  # pragma: no cover
                # np.random.choice was introduced in 1.7.0; edX has 1.6.0
                take = np.random.randint(len(idxs))
                index = idxs[take]

        # Subtract an eigenvalue from the array
        return array - np.eye(self.config['dimension']) * eigenvalues[index]


class OrthogonalMatrices(SquareMatrixSamplingSet):
    """
    Sampling set for orthogonal matrices.

    Note: This will only work with scipy 0.18 and numpy 1.7.1, which requires the python3
    implementation of edX.

    Config:
    =======
        Same as SquareMatrixSamplingSet, but:
            - unitdet (bool): Boolean specifying whether to sample from unit determinant
                matrices SO(n) (True, default) or arbitrary determinant matrices O(n) (False)

    The options 'complex' and 'norm' are ignored.

    Usage:
    ======
    Note: These doctests can only work in python 3.
    We can't dynamically skip doctests before pytest 4.4 (we're using 3.6.2),
    so for the moment, we just skip things that don't work.

    By default, we generate 2x2 matrices:
    >>> matrices = OrthogonalMatrices()
    >>> matrices.gen_sample().shape                 # doctest: +SKIP
    (2, 2)

    We can generate NxN matrices by specifying the dimension:
    >>> matrices = OrthogonalMatrices(dimension=4)
    >>> matrices.gen_sample().shape                 # doctest: +SKIP
    (4, 4)

    If unitdet is specified, the determinant is 1:
    >>> from mitxgraders.helpers.calc import within_tolerance
    >>> matrices = OrthogonalMatrices(unitdet=True)
    >>> within_tolerance(np.linalg.det(matrices.gen_sample()), 1, 1e-14)  # doctest: +SKIP
    True

    Otherwise, it could be +1 or -1.

    The resulting samples are orthogonal matrices:
    >>> matrices = OrthogonalMatrices(unitdet=True)
    >>> m = matrices.gen_sample()                                           # doctest: +SKIP
    >>> within_tolerance(m * np.transpose(m), MathArray(np.eye(2)), 1e-14)  # doctest: +SKIP
    True

    >>> matrices = OrthogonalMatrices(unitdet=False)
    >>> m = matrices.gen_sample()                                           # doctest: +SKIP
    >>> within_tolerance(m * np.transpose(m), MathArray(np.eye(2)), 1e-14)  # doctest: +SKIP
    True

    """
    schema_config = SquareMatrixSamplingSet.schema_config.extend({
        Required('unitdet', default=True): bool
    })

    def generate_sample(self):
        """
        Generates an orthogonal matrix
        """
        # Generate the array
        if self.config['unitdet']:
            array = special_ortho_group.rvs(self.config['dimension'])
        else:
            array = ortho_group.rvs(self.config['dimension'])
        # Return the result
        return array


class UnitaryMatrices(SquareMatrixSamplingSet):
    """
    Sampling set for unitary matrices.

    Note: This will only work with scipy 0.18 and numpy 1.7.1, which requires the python3
    implementation of edX.

    Config:
    =======
        Same as SquareMatrixSamplingSet, but:
            - unitdet (bool): Boolean specifying whether to sample from unit determinant
                matrices SU(n) (True, default) or arbitrary determinant matrices U(n) (False)

    The options 'complex' and 'norm' are ignored.

    Usage:
    ======
    Note: These doctests can only work in python 3.
    We can't dynamically skip doctests before pytest 4.4 (we're using 3.6.2),
    so for the moment, we just skip things that don't work.

    By default, we generate 2x2 matrices:
    >>> matrices = UnitaryMatrices()
    >>> matrices.gen_sample().shape                 # doctest: +SKIP
    (2, 2)

    We can generate NxN matrices by specifying the dimension:
    >>> matrices = UnitaryMatrices(dimension=4)
    >>> matrices.gen_sample().shape                 # doctest: +SKIP
    (4, 4)

    If unitdet is specified, the determinant is 1:
    >>> from mitxgraders.helpers.calc import within_tolerance
    >>> matrices = UnitaryMatrices(unitdet=True)
    >>> within_tolerance(np.linalg.det(matrices.gen_sample()), 1, 1e-14)  # doctest: +SKIP
    True

    Otherwise, it's typically not (though it could randomly be):
    >>> matrices = UnitaryMatrices(unitdet=False)
    >>> within_tolerance(np.linalg.det(matrices.gen_sample()), 1, 1e-14)  # doctest: +SKIP
    False

    The resulting samples are unitary matrices:
    >>> matrices = UnitaryMatrices(unitdet=True)
    >>> m = matrices.gen_sample()                                         # doctest: +SKIP
    >>> within_tolerance(m * np.conjugate(np.transpose(m)), MathArray(np.eye(2)), 1e-14)  # doctest: +SKIP
    True

    >>> matrices = UnitaryMatrices(unitdet=False)
    >>> m = matrices.gen_sample()                                         # doctest: +SKIP
    >>> within_tolerance(m * np.conjugate(np.transpose(m)), MathArray(np.eye(2)), 1e-14)  # doctest: +SKIP
    True

    """
    schema_config = SquareMatrixSamplingSet.schema_config.extend({
        Required('unitdet', default=True): bool
    })

    def generate_sample(self):
        """
        Generates an orthogonal matrix as appropriate
        """
        # Generate the array
        array = unitary_group.rvs(self.config['dimension'])
        # Fix the determinant if need be
        if self.config['unitdet']:
            det = np.linalg.det(array)
            array /= det**(1/self.config['dimension'])
        # Return the result
        return array
