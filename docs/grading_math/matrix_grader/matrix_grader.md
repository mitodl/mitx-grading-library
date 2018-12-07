# MatrixGrader
MatrixGrader is an extended version of FormulaGrader used to grade mathematical expressions containing scalars, vectors, and matrices. Authors and students may enter matrix (or vector) expressions by using variables sampled from matrices, or by entering a matrix entry-by-entry.

## A first example
A typical use of MatrixGrader might look like

```pycon
>>> from mitxgraders import *
>>> grader1 = MatrixGrader(
...   answers='4*A*B^2*v',
...   variables=['A', 'B', 'v'],
...   identity_dim=2, # makes 'I' available to students as the 2x2 identity matrix
...   sample_from={
...      'A': RealMatrices(), # samples from 2 by 2 matrices by default
...      'B': RealMatrices(),
...      'v': RealVectors(shape=2), # sample 2-component vectors
...   }
... )

```

The next few lines call the grader as a check function. The inputs `'4*A*B^2*v'` and `'4*A*B*B*v'` are correct:
```pycon
>>> grader1(None, '4*A*B^2*v')
{'grade_decimal': 1, 'msg': '', 'ok': True}
>>> grader1(None, '4*A*B*B*v')
{'grade_decimal': 1, 'msg': '', 'ok': True}

```
while the input `'4*B*A*B*v'` is incorrect because the matrix-sampled variables are non-commutative:
```pycon
>>> grader1(None, '4*B*A*B*v')
{'msg': '', 'grade_decimal': 0, 'ok': False}

```

## Matrix Sampling

In the MatrixGrader example above, the variables `A` and `B` were sampled from `RealMatrices()`. The `RealMatrices` sampling class samples from 2 by 2 matrices by default but can be configured to sample matrices of different shapes. See [Sampling](../sampling.md#variable-sampling-vectors-and-matrices) for more information about matrix and vector sampling.

## Matrix Entry

In addition to using variables that vectors and matrices, students can also enter matrices and vectors directly, entry-by-entry.

| Input with symbols:   | Input entry-by-entry:   |
|---|---|
| <img src='../input_by_symbols.png' width='300px' alt='Variables sampled with vectors and matrices'/>   | <img src='../input_by_entries.png' width='300px' alt='students enter matrices/vectors directly'/>   |

!!! note
     - In order for matrices entered entry-by-entry to display correctly in edX, authors must use the AsciiMath renderer provided by `<textline math='true'/>`.

By default, students can only input vectors and **not matrices**. This is configured through the `max_array_dim` configuration key:

- `max_array_dim=1`: This (the default) allows students to enter vectors entry-by-entry but not matrices.
    - entering vector `[x, y + 1, z]` is OK.
    - entering matrix `[[1, x], [y, 2]]` raises an error.
- `max_array_dim=2`: This allows student to vectors and matrices.
    - entering vector `[x, y + 1, z]` is OK.
    - entering matrix `[[1, x], [y, 2]]` is OK.
    - entering tensor `[ [[1, 2], [3, 4]], [[5, 6], [7, 8]] ]` raises an error.

The decision to disable matrix-entry by default is intended to prevent students from entering single-row or single-column matrices when a vector is expected.

## Matrix Operations and MathArrays

`MatrixGrader` uses a custom subclass of [`numpy.ndarray`](https://docs.scipy.org/doc/numpy-1.14.0/reference/generated/numpy.ndarray.html) to internally represent matrices. Understanding how the `MathArray` class behaves is useful for creating `MatrixGrader` problems, and `MathArray` can be used directly by problem-authors to add extra matrices to a problem.

### How MatrixGrader uses MathArrays

Whether a matrix is input entry-by-entry or represented through variables, `MathArray`s are used to evaluate student expressions.

For example, consider the grader below.
```pycon
>>> grader = MatrixGrader(
...     answers='2*A*[1, 2, 3] + v',
...     user_constants={
...       'A': MathArray([[1, 2, 3], [4, 5, 6]])
...     },
...     variables=['v'],
...     sample_from={
...       'v': RealVectors(shape=2) # samples a random 2-component vector
...     }
... )

```
When a student inputs `v + A*2*[1, 2, 3]` to the grader above, a calculation similar to
```pycon
>>> v = MathArray([2, -1]) # Really, random samples would be chosen.
>>> A = MathArray([[1, 2, 3], [4, 5, 6]])
>>> v + A*2*MathArray([1, 2, 3])  # below is the result of evaluating student input, which would next be compared to author's answer
MathArray([30, 63])

```
is performed (but repeated multiple times with different values for the random variables).

### Dimension and Shape
`MathArray`s have dimension and shape. For example:

| Student Input | Converted to   | Name   | dimension   | shape   |
|---|---|---|---|---|
| `[1, 2, 3]`              | `MathArray([1, 2, 3])`               | "vector"               | `1`  | `(3,  )`    |
| `[[1, 2, 3], [4, 5, 6]]` | `MathArray([[1, 2, 3], [4, 5, 6]])`  | "matrix"               | `2`  | `(2, 3)`    |
| `[[1, 2, 3]]`            | `MathArray([[1, 2, 3]])`             | "single-row matrix"    | `2`  | `(1, 3)`    |
| `[[1], [2], [3]]`        | `MathArray([[1], [2], [3]])`         | "single-column matrix" | `2`  | `(3, 1)`    |
| `[[[1, 2]], [[3, 4]]]`   | `MathArray([[[1, 2]], [[3, 4]]])`    | "tensor"               | `3`  | `(1, 1, 2)` |

Tensor math arrays (dimension 3+) currently have very little support.

!!! warning
    Note that a vector, a single-column matrix, and a single-row matrix are distinct entities. We suggest avoiding single-row and single-column matrices.

    See [A note about vectors](#a-note-about-vectors)

### Allowed operations

 `MathArray` support the usual binary operations for vectors and matrices, with appropriate shape restrictions. Compared to `numpy.ndarray`, `MathArray` has much more stringent shape restrictions.

 - **Addition and Subtraction**: Performed elementwise.

    | Expression | raises error unless | result type |
    |---|---|---|
    | `MathArray +/- MathArray`  | both inputs have exactly the same shape | `MathArray` |
    | `MathArray +/- number`  | `number=0` | `MathArray` |
    | `number +/- MathArray`  | `number=0` | `MathArray` |

  - **Multiplication**: Note that `vector * vector` is a dot product

    | Expression   | left-input shape | right-input shape | raises error unless | result type |
    |---|---|---|---|---|
    | `vector * vector`     | `(k1, )`   | `(k2, )`   | `k1=k2` | `number` (dot product of two vectors)  |
    | `MathArray * number`  | any        | -          | -       | `MathArray` (elementwise multiplication) |
    | `number * MathArray`  | -          | any        | -       | `MathArray` (elementwise multiplication) |
    | `matrix * vector`     | `(m, n)`   | `(k)`      | `n=k`   | `vector` with `m` components |
    | `vector * matrix`     | `(k, )`    | `(m, n)`   | `m=k`   | `vector` with `n` components |
    | `matrix * matrix`     | `(m1, n1)` | `(m2, n2)` | `n1=m2` | `matrix` of shape `(m1, n2)`  |

  - **Division**: Division either raises an error, or is performed elementwise:

    | Expression | raises error unless | result type |
    |---|---|---|
    | `any / MathArray`     | always raises error | - |
    | `MathArray / number`  | -                   | `MathArray` (elementwise division) |

  - **Powers**: If `A` is a MathArray, then `A^k` will always raise an error unless
    - `A` is a square matrix, *and*
    - `k` is an integer.

    In this case, `A^k` is equivalent to:

    - `k` repeated multiplications of `A` if `k > 0`,
    - `(inverse of A)^|k|` if `k < 0`, and
    - the identity matrix if `k=0`.

    *Note*: Negative exponents can give students "too much power". For example, if you want students to enter the inverse of `[[1, 2], [3, 4]]`, you probably want them to enter `[[-2, 1], [1.5, -0.5]]` not `[[1, 2], [3, 4]]^-1`. To this end, you can disable negative powers in MatrixGrader problems by setting `negative_powers=False`.

### A note about vectors

Vectors are distinct from single-row matrices and single-column matrices, and can be left- or right-multiplied by a matrix:

```pycon
>>> vec = MathArray([1, 2, 3])
>>> row = MathArray([[1, 2, 3]])
>>> col = MathArray([[1], [2], [3]])
>>> vec + row # raises error
Traceback (most recent call last):
MathArrayShapeError: Cannot add/subtract a vector of length 3 with a matrix of shape (rows: 1, cols: 3).

>>> A = MathArray([[1, 2, 3], [4, 5, 6]])
>>> A * vec # matrix * vector
MathArray([14, 32])
>>> other_vec = MathArray([1, 2])
>>> other_vec * A # vector * matrix
MathArray([ 9, 12, 15])

```

We suggest avoiding single-column and single-row matrices.

### Shape Errors

When operations cannot be performed because of shape-mismatch, MathArray raises readable `StudentFacingError`s. These error messages are intended to be presented directly to students. For example:

```pycon
>>> A = MathArray([[1, 2], [3, 4], [5, 6]]) # matrix, shape (3, 2)
>>> B = MathArray([[1, 2], [3, 4]])         # matrix, shape (2, 2)
>>> v = MathArray([1, 2])                   # vector, shape (2,  )

```

Some sample error messages:

| Student input:  | Valid?  | Student receives error message:   |
|---  |--- |--- |
| `'A+B'` | No  |  Cannot add/subtract a matrix of shape (rows: 3, cols: 2) with a matrix of shape (rows: 2, cols: 2). |
| `'v*A'` | No  |  Cannot multiply a vector of length 2 with a matrix of shape (rows: 3, cols: 2).   |
| `'B*v'` | Yes |  n/a  |
| `'A^2'`   | No  |  Cannot raise a non-square matrix to powers.    |
| `'B^2'`   | Yes |  n/a    |

<!-- Test the messages -->
<!-- ```pycon
>>> A + B
Traceback (most recent call last):
MathArrayShapeError: Cannot add/subtract a matrix of shape (rows: 3, cols: 2) with a matrix of shape (rows: 2, cols: 2).


>>> v*A
Traceback (most recent call last):
MathArrayShapeError: Cannot multiply a vector of length 2 with a matrix of shape (rows: 3, cols: 2).

>>> A**2
Traceback (most recent call last):
MathArrayShapeError: Cannot raise a non-square matrix to powers.

``` -->

## Handling Errors

While grading a student's input, matrix-related errors can occur in three places:

  - while parsing the student's input,
  - while evaluating the student's input, and
  - while comparing the student's input to the author's stored answer.

### Parse errors:
For example, student enters `'[[1, 2],[3] ]'`, a matrix missing an entry in second row:

```pycon
>>> grader = MatrixGrader(
...     answers='[[1, 2], [3, 4]]',
...     max_array_dim=2, # allow students to enter matrices entry-by-entry
... )
>>> student_input = '[[1, 2], [3]]'
>>> try:
...     grader(None, student_input) # grade the input like edX would
... except StudentFacingError as error:
...     str(error.message) # students see this error message
"Unable to parse vector/matrix. If you're trying to enter a matrix, this is most likely caused by an unequal number of elements in each row."

```

Such parse errors are **always** displayed to students.

### Shape-mismatch errors during evaluation

If a student submits an answer that will raise shape-mismatch errors then an error is raised with a helpful message. This avoids consuming one of the student's attempts. For example:

```pycon
>>> grader = MatrixGrader(
...     answers='[11, 22, 33]',
... )
>>> student_input = '[10, 20, 30] + [1, 2]' # Error! Adding vectors with different shapes
>>> try:
...     grader(None, student_input) # grade the input like edX would
... except StudentFacingError as error:
...     str(error.message) # students see this error message
'Cannot add/subtract a vector of length 3 with a vector of length 2.'

```

If you would rather mark the student incorrect when shape errors occur (and also consume an attempt), set `shape_errors=False`.

### Shape-mismatch errors during comparison

If the author's answer is a 3-component vector, and the student submits a different 3-component vector, then they will be marked incorrect. However, if the student submits a 2-component vector or a number, they will receive an error message:

```pycon
>>> grader = MatrixGrader(
...     answers='[1, 2, 3]',
... )
>>> student_input = '[1, 2, -3]' # wrong answer
>>> grader(None, student_input) # grade the input like edX would
{'msg': '', 'grade_decimal': 0, 'ok': False}

>>> student_input = '[1, 2, 3, 4]' # too many components
>>> try:
...     grader(None, student_input) # grade the input like edX would
... except StudentFacingError as error:
...     str(error.message) # students see this error message
'Expected answer to be a vector, but input is a vector of incorrect shape'

>>> student_input = '0' # scalar; should be a vector
>>> try:
...     grader(None, student_input) # grade the input like edX would
... except StudentFacingError as error:
...     str(error.message) # students see this error message
'Expected answer to be a vector, but input is a scalar'

```

The default handling of shape errors that arise when comparing student input to author's answer is:

  - raise an error (do not mark student incorrect), and
  - reveal the desired type (above, a vector) but not the desired shape (above, 3-components)

This behavior can be configured through the `answer_shape_mismatch` key. For example, to

  - mark students wrong instead of raising an error, and
  - reveal the shape and the type

we can use:
```pycon
>>> grader = MatrixGrader(
...     answers='[1, 2, 3]',
...     answer_shape_mismatch={
...         'is_raised': False,
...         'msg_detail': 'shape' # must be one of: None, 'type', 'shape'
...     }
... )
>>> student_input = '0' # wrong shape
>>> grader(None, student_input) # grade the input like edX would
{'grade_decimal': 0, 'msg': 'Expected answer to be a vector of length 3, but input is a scalar', 'ok': False}

```

### Hiding all messages

MatrixGraders can be used to introduce non-commuting variables. In such a situation, students may not know that the variables they are using are matrices "under the hood", and so we want to suppress all matrix errors and messages. We can do this by setting `suppress_matrix_messages=True`, which overrides `answer_shape_mismatch={'is_raised'}` and `shape_errors`. In the following example, `A` and `B` are secretly matrices that don't commute, but students will never see a matrix error message from typing something like `1+A`.

```
grader = MatrixGrader(
    answers=['A*B'],
    variables=['A', 'B'],
    sample_from={
        'A': RealMatrices(),
        'B': RealMatrices()
    },
    max_array_dim=0,
    suppress_matrix_messages=True
)
```

Note that this will also suppress error messages from trying to do things like `sin([1, 2])` or `[1, 2]^2`. If your answer needs to take functions of the non-commuting variables, then this option is insufficient.


## Matrix Functions

MatrixGrader provides all the default functions of `FormulaGrader` (`sin`, `cos`, etc.) plus some extras such as `trans(A)` (transpose) and `det(A)` (determinant). See [Mathematical Functions]('../functions_and_constants.md') for full list.

Since `MatrixGrader` has all of `FormulaGrader`'s configuration options, additional functions can be supplied through the `user_functions` configuration key. If you supply addition matrix functions, you may wish you use the `specify_domain` decorator function. See [Function Listing: Specify Domain](../matrixfunctions.md) for details.

## Identity Matrix

To make an n by n identity matrix available to students, specify the configuration key `identity_dim=n`. That is, the grader `MatrixGrader(identity_dim=4, ...)` will automatically have a constant `'I'` whose value is the 4 by 4 identity matrix.

If you want a different name (besides `'I'`) for the identity, or if you encounter situations where identity matrices of different sizes are required, `mitxgraders.helpers.calc` provides an `identity` function. For example:
```pycon
>>> from mitxgraders import MatrixGrader
>>> from mitxgraders.helpers.calc import identity
>>> grader = MatrixGrader(
...     answers='[1, 2, 3]',
...     user_constants={
...         'I_2': identity(2),  # the 2 by 2 identity
...         'I_3': identity(3)  # the 3 by 3 identity
...     }
... )

```

## Configuration Options

`MatrixGrader` has all of [`FormulaGrader`](../formula_grader.md)'s configuration options, plus some extras. The extras are:

- `idenity_dim`: If specified as a positive integer `n`, then an n by n identity matrix is added to the available constants with name `'I'`. Defaults to `None`.
- `max_array_dim` (nonnegative int): Controls the maximum [dimension](#dimension-and-shape) of arrays that students can enter entry-by-entry. Default is `1`: vectors can be entered entry-by-entry, but not matrices.
- `negative_powers` (bool): whether negative powers are enabled for square matrices (which calculate powers of matrix inverse). Defaults to `True`.
- `shape_errors` (bool): See [Handling Errors: Shape-mismatch errors during evaluation](#shape-mismatch-errors-during-evaluation). Defaults to `True`.
- `answer_shape_mismatch` (dict): A dictionary whose keys are listed below. Some or all keys may be set. Unset keys take default values. See [Handling Errors: Shape-mismatch errors during comparison](#shape-mismatch-errors-during-comparison) for details.

    - `'is_raised'` (bool): defaults to `True`
    - `'msg_detail'`: one of `None`, `'type'`, or `'shape'`. Defaults to `'type'`
