# Comparer Functions

By default, `FormulaGrader`, `NumericalGrader`, and `MatrixGrader` compare the numerically-sampled author formula and student formula for equality (within bounds specified by tolerance). Occasionally, it can be useful to compare author and student formulas in some other way. Functions that perform the actual comparison are called "comparers", and there are a few ways to invoke them.


## Employing Comparer Functions

When an answer is passed into `FormulaGrader`, `NumericalGrader` or `MatrixGrader`, it is automatically paired up with a comparer. For example, the default comparer is `equality_comparer`. When you construct a grader like the following,

```pycon
>>> from mitxgraders import *
>>> grader1 = FormulaGrader(
...     answers='a+b',
...     variables=['a', 'b']
... )

```

`FormulaGrader` automatically converts the `answers` key to the following:

```pycon
>>> grader2 = FormulaGrader(
...     answers={
...         'expect': {'comparer': equality_comparer, 'comparer_params': ['a+b']},
...         'grade_decimal': 1,
...         'msg': ''
...     },
...     variables=['a', 'b']
... )
>>> grader1 == grader2
True

```

To specify an alternate comparer, you can simply change the relevant answer to a dictionary `{'comparer': comparer_func, 'comparer_params': [list, of, params]}`. Different comparers use `comparer_params` in different ways.

For example, if grading angles in degrees, it may be useful to compare formulas modulo 2&#960;. You can write your own comparer functions, but for this we can use the pre-built `congruent_modulo` comparer. This grader will accept any input congruent to `'b^2/a'` modulo `2*pi`.

```pycon
>>> grader = FormulaGrader(
...     answers={
...         'comparer': congruence_comparer,
...         # first parameter is expected value, second is the modulus
...         'comparer_params': ['b^2/a', '2*pi']
...     },
...     variables=['a', 'b']
... )
>>> grader(None, 'b^2/a + 6*pi')['ok']
True
>>> grader(None, 'b^2/a + 5.5*pi')['ok']
False

```

Here, the `comparer_params` (`['b^2/a', '2*pi']`) are evaluated just like the student input, and used by the comparer function during grading.


## Changing Defaults

The default comparer function for each of `FormulaGrader`, `NumericalGrader` and `MatrixGrader` can be set by calling `set_default_comparer` as follows:

```pycon
>>> FormulaGrader.set_default_comparer(LinearComparer())

```

This sets the default comparer to `LinearComparer()` (see below) for all `FormulaGrader`s in the given problem. Comparers set in this manner must only take a single comparer parameter. Using this default set approach is typically simpler than setting comparers explicitly, and allows answers to be inferred from `expect` values. However, comparers that require two or more `comparer_params` cannot use this method.

If for some reason you need to reset the default comparer, you can use

```pycon
>>> FormulaGrader.reset_default_comparer()

```

which is equivalent to setting the default comparer to `equality_comparer`.


## Available Comparers

The table below lists the pre-built comparers along with the expected comparer parameters. Note that `comparer_params` is **always** a list of strings, and can use any variables available to the student. When using an ordered `ListGrader`, they can also use sibling values.

| `comparer`   | use with | `comparer_params` <br/> (a list of strings)  | purpose |
|---|---|---|---|
| `equality_comparer` | `FormulaGrader` <br/> `NumericalGrader` <br/> `MatrixGrader` | `[expected]` | checks that student input and `expected` differ by less than grader's tolerance. |
| `congruence_comparer` |  `FormulaGrader` <br/> `NumericalGrader` | `[expected, modulus]` | reduces student input modulo modulus, then checks for equality within grader's tolerance. |
| `between_comparer` |  `FormulaGrader` <br/> `NumericalGrader` | `[start, stop]` | checks that student input is real and between `start` and `stop`.  |
| `eigenvector_comparer` | `MatrixGrader`  | `[matrix, eigenvalue]`  | checks that student input is an eigenvector of `matrix` with eigenvalue `eigenvalue` within grader's tolerance.  |
| `vector_phase_comparer` | `MatrixGrader`  | `[comparison_vector]`  | checks that student input is equal to `comparison_vector` up to a phase, within grader's tolerance. |
| `vector_span_comparer` | `MatrixGrader`  | `[vector1, vector2, ...]`  | checks that student input is nonzero and in the span of the given list of vectors, within grader's tolerance. If only a single vector is given, checks if the student input is equal to the given vector up to a (possibly complex) constant of proportionality.  |

All of these comparers (as well as the ones below) are available when using `from mitxgraders import *`.


## Special Comparers

There are three special built-in comparer classes that can be used as comparers that take in a single input.


### EqualityComparer

The `EqualityComparer` class simply checks for equality up to tolerance. In fact, `equality_comparer = EqualityComparer()`. The reason this class exists, however, is to allow for an extra option to be used when desired.

The `transform` option allows the author to specify a transforming function to be called on both the answer and the student input prior to comparison. Here is an example:

```pycon
>>> import numpy as np
>>> comparer = EqualityComparer(transform=np.real)

```

This comparer will take the real part of the answer and the student input before comparing the results. This is useful if only the real part of the answers need to agree.


### LinearComparer

The `LinearComparer` checks if the student's answer is linearly related to the problem's answer, and can provide partial credit as appropriate. Here are all of the options:

```python
comparer = LinearComparer(
    equals=float,  # default 1
    proportional=(None | float),  # default 0.5
    offset=(None | float),  # default None
    linear=(None | float),  # default None
    equals_msg=(None | str),  # default None
    proportional_msg=(None | str),  # default 'The submitted answer differs from an expected answer by a constant factor.'
    offset_msg=(None | str),  # default None
    linear_msg=(None | str),  # default None
)
```

The first four settings specify how much credit to award the different situations, while the next four describe a message to display when that credit is awarded. Note that setting credit to `None` means that that type of credit will never be awarded, while setting credit to `0` means that it can be awarded (usually to display the relevant message). When the grading is performed, the largest credit of the available settings is awarded.

Here is an example of a `LinearComparer` that can be used to award partial credit if students are off from the answer by a constant multiple.

```pycon
>>> comparer = LinearComparer()

```

Easy, isn't it? You can combine this with `set_default_comparer` to enable partial credit of this sort with one line in each problem!

Here is an example of setting up a `LinearComparer` that doesn't care about shift offsets (useful when describing indefinite integration).

```pycon
>>> comparer = LinearComparer(proportional=None, linear=1)

```

Note that `LinearComparer` can only perform meaningful comparisons when random variables are used. If the answer is a numerical constant, then student answers will always be proportional to that constant, which probably isn't the desired behavior. Also note that when the answer is zero or the student supplies zero as their answer, partial credit cannot be assigned.


### MatrixEntryComparer

This comparer is used only for `MatrixGrader`s. It has a `transform` option that is exactly equivalent to `EqualityComparer`, but it also has two options related to partial credit.

```python
comparer = MatrixEntryComparer(
    transform=(None | func),  # default None
    entry_partial_credit=('proportional' | float),  # default 0
    entry_partial_msg=str,  # default "Some array entries are incorrect, marked below:\n{error_locations}"
)
```

When `entry_partial_credit` is set to a number, if at least one entry in the array is correct (but not all of them), that amount of credit is assigned. When partial credit is assigned, the message `entry_partial_msg` is displayed to the student, with the text `{error_locations}` replaced by a graphic displaying which entries are correct/incorrect. To turn off the message, simply set `entry_partial_msg=''`. Setting `entry_partial_msg=''` and `entry_partial_credit=0` makes this grader equivalent to `EqualityComparer`.

Because this ability to assign partial credit to array input is so useful, `MatrixEntryComparer` can be set as the grader for `MatrixGrader`s using configuration options.


## Custom Comparer Functions

In addition to using the built-in comparers, you can write your own.

See [comparers.py](https://github.com/mitodl/mitx-grading-library/tree/master/mitxgraders/comparers/comparers.py) for documentation and examples.
