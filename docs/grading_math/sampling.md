# Sampling

Whenever random variables/functions are involved, they need to be sampled from an appropriate distribution. In this library, distributions are defined in classes that are called _sampling sets_. We have defined a number of sampling sets for various common situations, but you can also create your own by using plugins.

These sampling classes are available for use in `FormulaGrader`, `MatrixGrader`, etc.

## Variable Sampling: Numbers (Scalars)

These sampling sets generate a random number on demand. It may be real or complex.


### RealInterval

Sample from a real interval defined by a `start` and a `stop` value. RealInterval can be initialized using explicit values, or an interval.

```python
>>> from mitxgraders import *
>>> # Generate random real numbers between 3 and 7
>>> sampler = RealInterval(start=3, stop=7)
>>> # This is equivalent to
>>> sampler = RealInterval([3, 7])
>>> # The default is [1, 5]
>>> sampler = RealInterval()
>>> # A list can also be used to specify an interval
>>> sampler = [3, 7]

```

### IntegerRange

Sample from an integer defined by a `start` and a `stop` value (both start and stop are included in the range). IntegerRange can be initialized using explicit values, or an interval.

```python
>>> # Generate random integers between 3 and 7 inclusive
>>> sampler = IntegerRange(start=3, stop=7)
>>> # This is equivalent to
>>> sampler = IntegerRange([3, 7])
>>> # The default is [1, 5]
>>> sampler = IntegerRange()

```


### ComplexRectangle

Sample complex numbers from a rectangle in the complex plane, specified by a real range and an imaginary range.

```python
>>> # Select random complex numbers from 0 to 1 + i
>>> sampler = ComplexRectangle(re=[0, 1], im=[0, 1])
>>> # The default is re=[1, 3], im=[1, 3]
>>> sampler = ComplexRectangle()

```


### ComplexSector

Sample complex numbers from an annular sector in the complex plane, specified by a modulus range and an argument range.

```python
>>> import numpy as np
>>> # Select random complex numbers from inside the unit circle
>>> sampler = ComplexSector(modulus=[0, 1], argument=[-np.pi, np.pi])
>>> # The default is modulus=[1, 3], argument=[0, pi/2]
>>> sampler = ComplexSector()

```

## Variable Sampling: Vectors and Matrices

### RealVectors
Sample real vectors with specified shape (number of components) and norm.

```python
>>> # sample real vectors with 4 components and norm between 5 and 10
>>> sampler = RealVectors(shape=4, norm=[5, 10])
>>> # For consistency with RealMatrices, shape can be specified as list:
>>> sampler = RealVectors(shape=[4], norm=[5, 10])
>>> # The default is 3 component vectors with norm from 1 to 5
>>> sampler = RealVectors()

```

### RealMatrices

Sample real matrices of a specific shape and norm. (`RealMatrices` uses the Frobenius norm.)

```python
>>> # Sample 3 by 2 real matrices with norm between 5 and 10
>>> sampler = RealMatrices(shape=[3, 2], norm=[5, 10])
>>> # the default is shape=[2, 2] and norm=[1, 5]
>>> RealMatrices()

```

If you want to sample a matrix in a way that depends on a scalar, see `DependentSampler` below.

### IdentityMatrixMultiples

Sample square matrices of a given dimension consisting of the identity matrix multiplied by a scalar. The `sampler` parameter can be any scalar sampling set listed above. This sampling set is useful when you want a variable that will commute with other matrices, but can also be added to them.

```python
>>> # Sample 3x3 matrices consisting of a random number between 1 and 3 multiplying the identity
>>> sampler = IdentityMatrixMultiples(dimension=3, sampler=[1, 3])
>>> # The default is dimension=2 and sampler=[1, 5]
>>> IdentityMatrixMultiples()

```


### Special Matrices: Orthogonal and Unitary

These sampling sets sample orthogonal `O(n)`, special orthogonal `SO(n)`, unitary `U(n)` and special unitary `SU(n)` matrices of a given dimension.

```python
>>> # Sample matrices from O(3)
>>> sampler = OrthogonalMatrices(dimension=3, unitdet=False)
>>> # Sample matrices from SO(4)
>>> sampler = OrthogonalMatrices(dimension=4, unitdet=True)
>>> # Sample matrices from U(3)
>>> sampler = UnitaryMatrices(dimension=3, unitdet=False)
>>> # Sample matrices from SU(4)
>>> sampler = UnitaryMatrices(dimension=4, unitdet=True)
>>> # The default is dimension=2 and unitdet=True
>>> OrthogonalMatrices()
>>> UnitaryMatrices()

```


## Variable Sampling: Generic

### DiscreteSet

Sample from any discrete set of values that are specified in a tuple. A single value may also be provided, but this case should usually be specified as a constant instead of as a sampling set.

```python
>>> # Select random numbers from (1, 3, 5, 7, 9)
>>> sampler = DiscreteSet((1, 3, 5, 7, 9))
>>> # Always select 3.5
>>> sampler = DiscreteSet(3.5)
>>> # A tuple can also be used to specify a discrete set
>>> sampler = (1, 3, 5, 7, 9)

```

### DependentSampler

Compute a value for a variable based on the values of other variables. The sampler must be initialized with a list of variables that it depends on, as well as the formula used to perform the computation. The formula can use any base functions, but no user-defined functions. `DependentSampler`s can depend on other dependent variables. If you construct a self-referential chain, an error will occur. Note that `DependentSampler` can depend on vector/matrix quantities as well as scalars.

```python
>>> # Set radius based on the random values of x, y and z
>>> sampler = DependentSampler(depends=["x", "y", "z"], formula="sqrt(x^2+y^2+z^2)")
>>> # Construct a matrix that depends on a variable
>>> sampler = DependentSampler(depends=["x"], formula="[[x,0],[0,-x^2]]")

```


## Function Sampling

When a random function can be specified, we need a sampling set that returns a random function on demand.


### SpecificFunctions

Samples functions from a specific list of functions. You can also specify just a single function, but usually this shouldn't be done as a sampling set.

```python
>>> # Select either sin or cos randomly
>>> functionsampler = SpecificFunctions([np.cos, np.sin])
>>> # Always select a single lambda function
>>> functionsampler = SpecificFunctions(lambda x: x*x)

```

### RandomFunction

Generate a random well-behaved function. The function is constructed from the sum of sinusoids with random amplitudes, frequencies and phases. It oscillates about a specified center value with up to a specified amplitude.

```python
>>> # Generate a random function
>>> functionsampler = RandomFunction(center=1, amplitude=2)
>>> # The default is center=0, amplitude=10
>>> functionsampler = RandomFunction()

```

You can control how many random sinusoids are added together by specifying `num_terms`.

```python
>>> # Generate a random sinusoid
>>> functionsampler = RandomFunction(num_terms=1)

```

You can also generate a non-unary function by specifying the input dimension, and generate vector output by specifying the output dimension.

```python
>>> # Generate a function that takes in two scalar values and outputs a 3D vector
>>> functionsampler = RandomFunction(input_dim=2, output_dim=3)

```

Finally, if you want to generate a complex random function, simply set `complex=True`. In this situation, the randomly generated function works as previously, but the sinusoid coefficients are complex numbers.

```python
>>> functionsampler = RandomFunction(complex=True)
```
