# Sampling

Whenever random variables/functions are involved, they need to be sampled from an appropriate distribution. In this library, distributions are defined in classes that are called _sampling sets_. We have defined a number of sampling sets for various common situations, but you can also create your own by using plugins.

These sampling classes are available for use in `FormulaGrader`, `MatrixGrader`, etc.


## Variable Sampling: Numbers (Scalars)

These sampling sets generate a random number on demand. It may be real or complex.


### RealInterval

Sample from a real interval defined by a `start` and a `stop` value. RealInterval can be initialized using explicit values, or an interval.

```pycon
>>> from mitxgraders import *
>>> # Generate random real numbers between 3 and 7
>>> sampler = RealInterval(start=3, stop=7)
>>> # This is equivalent to
>>> sampler = RealInterval([3, 7])
>>> # The default is [1, 5]
>>> RealInterval() == RealInterval([1, 5])
True
>>> # A list can also be used to specify an interval
>>> sampler = [3, 7]

```


### IntegerRange

Sample from an integer defined by a `start` and a `stop` value (both start and stop are included in the range). `IntegerRange` can be initialized using explicit values, or an interval.

```pycon
>>> # Generate random integers between 3 and 7 inclusive
>>> sampler = IntegerRange(start=3, stop=7)
>>> # This is equivalent to
>>> sampler = IntegerRange([3, 7])
>>> # The default is [1, 5]
>>> IntegerRange() == IntegerRange([1, 5])
True

```


### ComplexRectangle

Sample complex numbers from a rectangle in the complex plane, specified by a real range and an imaginary range.

```pycon
>>> # Select random complex numbers in a rectangle from 0 to 1 + i
>>> sampler = ComplexRectangle(re=[0, 1], im=[0, 1])
>>> # The default is re=[1, 3], im=[1, 3]
>>> ComplexRectangle() == ComplexRectangle(re=[1, 3], im=[1, 3])
True

```


### ComplexSector

Sample complex numbers from an annular sector in the complex plane, specified by a modulus range and an argument range.

```pycon
>>> import numpy as np
>>> # Select random complex numbers from inside the unit circle
>>> sampler = ComplexSector(modulus=[0, 1], argument=[-np.pi, np.pi])
>>> # The default is modulus=[1, 3], argument=[0, pi/2]
>>> ComplexSector() == ComplexSector(modulus=[1, 3], argument=[0, np.pi/2])
True

```


## Variable Sampling: Vectors, Matrices and Tensors

We have a broad range of sampling sets for vectors, matrices and tensors. The following options are common to many of these sets:

- `shape`: Either be a number (to specify a vector of that dimension), or a tuple or list of numbers (to specify a matrix/tensor with those dimensions).
- `norm`: Specify a `RealInterval` for the norm of the object. (Frobenius norm is used.)

If you want to sample a vector/matrix/tensor in a way that depends on a scalar, see [`DependentSampler`](#dependentsampler) below.


### RealVectors and ComplexVectors

Sample real/complex vectors with specified shape (number of components) and norm.

```pycon
>>> # Sample real vectors with 4 components and unit norm
>>> sampler = RealVectors(shape=4, norm=[1, 1])
>>> # The default is 3 component vectors with norm from 1 to 5
>>> RealVectors() == RealVectors(shape=3, norm=[1, 5])
True
>>> # Similarly for complex vectors
>>> ComplexVectors() == ComplexVectors(shape=3, norm=[1, 5])
True

```


### RealMatrices and ComplexMatrices

Sample real/complex matrices of a specific shape and norm. An extra option exists to specify that the matrix be upper or lower triangular. The given shape must be a list or tuple of two numbers.

```pycon
>>> # Sample 3 by 2 real matrices with norm between 5 and 10
>>> sampler = RealMatrices(shape=[3, 2], norm=[5, 10])
>>> # The default is shape=[2, 2] and norm=[1, 5]
>>> RealMatrices() == RealMatrices({'norm': [1, 5], 'shape': (2, 2)})
True
>>> # Similarly for complex matrices
>>> ComplexMatrices() == ComplexMatrices({'norm': [1, 5], 'shape': (2, 2)})
True
>>> # Sample an upper triangular real 2x2 matrix.
>>> sampler = RealMatrices(triangular='upper')
>>> # Sample a lower triangular complex 2x2 matrix.
>>> sampler = ComplexMatrices(triangular='lower')

```


### RealTensors and ComplexTensors

Sample real/complex tensors of a specific shape and norm. A shape must be provided as a list or tuple of three or more numbers (there is no default).

```pycon
>>> # Sample 3x2x4 real tensors with norm between 5 and 10
>>> sampler = RealTensors(shape=[3, 2, 4], norm=[5, 10])
>>> # Sample 2x2x2x2 complex tensors with unit norm
>>> sampler = ComplexTensors(shape=[2, 2, 2, 2], norm=[1, 1])

```


### IdentityMatrixMultiples

Sample square matrices of a given dimension consisting of the identity matrix multiplied by a scalar. The `sampler` parameter can be any scalar sampling set listed above. This sampling set is useful when you want a variable that will commute with other matrices, but can also be added to them.

```pycon
>>> # Sample 3x3 matrices consisting of a random number between 1 and 3 multiplying the identity
>>> sampler = IdentityMatrixMultiples(dimension=3, sampler=[1, 3])
>>> # The default is dimension=2 and sampler=[1, 5]
>>> IdentityMatrixMultiples() == IdentityMatrixMultiples(dimension=2, sampler=[1, 5])
True

```


### SquareMatrices

This is a general sampling set for square matrices. A large number of options for specifying properties of square matrices are included:

- `dimension` (int): Specify the number of dimensions of the matrix (default 2)
- `complex` (bool): Should the matrix be complex (True) or real (False, default) (ignored if `hermitian` or `antihermitian` are selected)
- `traceless` (bool): Whether or not the matrix should be traceless (default False)
- `determinant` (None | 0 | 1): Specify the determinant of the matrix (default None for no restriction)
- `symmetry`: Choose from the following symmetries: `None`, `'diagonal'`, `'symmetric'`, `'antisymmetric'`, `'hermitian'`, `'antihermitian'` (default `None`)
- `norm` (float): Specify a `RealInterval` to sample the norm of the matrix (default `[1, 5]`; ignored if `determinant=1` is specified)

Note that some combinations of options do not exist (e.g., odd-dimension, unit-determinant antisymmetric matrix). If you select such a combination, an error message will result.

Other types of square matrices can be sampled using `RealMatrices`, `ComplexMatrices`, `IdentityMatrixMultiples`, `OrthogonalMatrices` and `UnitaryMatrices`.

Here are a handful of examples:

```pycon
>>> # By default, we generate real 2x2 matrices with no restrictions:
>>> SquareMatrices() == SquareMatrices(dimension=2, complex=False, traceless=False, determinant=None, symmetry=None, norm=[1,5])
True

>>> # Diagonal, complex, traceless and unit determinant
>>> matrices = SquareMatrices(symmetry='diagonal', complex=True, traceless=True,
...                           determinant=1)

>>> # Symmetric, real, zero determinant
>>> matrices = SquareMatrices(symmetry='symmetric', determinant=0)

>>> # Hermitian (enforces complex)
>>> matrices = SquareMatrices(symmetry='hermitian')

```


### OrthogonalMatrices

Sample from orthogonal matrices of a given dimension. To sample special orthogonal matrices (unit determinant), use the `unitdet=True` option.

```pycon
>>> # Sample 3x3 orthogonal matrices with unit determinant
>>> sampler = OrthogonalMatrices(dimension=3, unitdet=True)
>>> # The default is dimension=2 and unitdet=False
>>> OrthogonalMatrices() == OrthogonalMatrices(dimension=2, unitdet=False)
True

```

!!! Note
    - Orthogonal matrix sampling only works on versions of edX running python 3.5, which went live on edx.org around July 2020. You can see which version of python your edX server is running by turning on `debug=True` in any grader and submitting a response. 


### UnitaryMatrices

Sample from unitary matrices of a given dimension. To sample special unitary matrices (unit determinant), use the `unitdet=True` option.

```pycon
>>> # Sample 3x3 unitary matrices with unit determinant
>>> sampler = UnitaryMatrices(dimension=3, unitdet=True)
>>> # The default is dimension=2 and unitdet=False
>>> UnitaryMatrices() == UnitaryMatrices(dimension=2, unitdet=False)
True

```

!!! Note
    - Unitary matrix sampling only works on versions of edX running python 3.5, which went live on edx.org around July 2020. You can see which version of python your edX server is running by turning on `debug=True` in any grader and submitting a response. 


## Variable Sampling: Generic


### DiscreteSet

Sample from any discrete set of values that are specified in a tuple. A single value may also be provided, but this case should usually be specified as a constant instead of as a sampling set.

```pycon
>>> # Select random numbers from (1, 3, 5, 7, 9)
>>> sampler = DiscreteSet((1, 3, 5, 7, 9))
>>> # Always select 3.5
>>> sampler = DiscreteSet(3.5)
>>> # A tuple can also be used to specify a discrete set
>>> sampler = (1, 3, 5, 7, 9)
>>> # Select randomly between two matrices
>>> sampler = DiscreteSet((MathArray([[1, 0], [0, 1]]), MathArray([[0, 1], [1, 0]])))

```


### DependentSampler

Compute a value for a variable based on the values of other constants/variables. The sampler is simply initialized with the desired formula, which can use any base or user-defined functions (except for randomly sampled functions, see below). `DependentSampler`s can depend on other dependent variables. If you construct a self-referential chain, an error will occur. Note that `DependentSampler` can depend on vector/matrix quantities as well as scalars.

```pycon
>>> # Set radius based on the random values of x, y and z
>>> sampler = DependentSampler(formula="sqrt(x^2+y^2+z^2)")
>>> # Construct a matrix that depends on a variable
>>> sampler = DependentSampler(formula="[[x,0],[0,-x^2]]")

```

!!! Note
    - Previous versions required a list of variables that the formula depends on to be passed to `DependentSampler` using the `depends` key. This is now obsolete, as this variable list is dynamically inferred. Anything passed to the `depends` key is now ignored.


## Function Sampling

We have two methods for selecting a random function.


### SpecificFunctions

Samples functions from a specific list of functions. You can also specify just a single function, but usually this shouldn't be done as a sampling set.

```pycon
>>> # Select either sin or cos randomly
>>> functionsampler = SpecificFunctions([np.cos, np.sin])
>>> # Equivalent sampling set specified as a list
>>> functionsampler = [np.cos, np.sin]
>>> # Always select a single lambda function
>>> functionsampler = SpecificFunctions(lambda x: x*x)

```


### RandomFunction

Generate a random well-behaved function. The function is constructed from the sum of sinusoids with random amplitudes, frequencies and phases. It oscillates about a specified center value with up to a specified amplitude.

```pycon
>>> # Generate a random function
>>> functionsampler = RandomFunction(center=1, amplitude=2)
>>> # The default is center=0, amplitude=10
>>> functionsampler = RandomFunction()

```

You can control how many random sinusoids are added together by specifying `num_terms`.

```pycon
>>> # Generate a random sinusoid
>>> functionsampler = RandomFunction(num_terms=1)

```

You can also generate a non-unary function by specifying the input dimension, and generate vector output by specifying the output dimension.

```pycon
>>> # Generate a function that takes in two scalar values and outputs a 3D vector
>>> functionsampler = RandomFunction(input_dim=2, output_dim=3)

```

Finally, if you want to generate a complex random function, set `complex=True`. In this situation, the randomly generated function works as previously, but the sinusoid coefficients are complex numbers.

```pycon
>>> functionsampler = RandomFunction(complex=True)

```
