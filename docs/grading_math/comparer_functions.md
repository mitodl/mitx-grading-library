# Comparer Functions

By default, `FormulaGrader`, `NumericalGrader`, and `MatrixGrader` compare the numerically-sampled author formula and student formula for equality (within bounds specified by tolerance). Occasionally, it can be useful to compare author and student formulas in some other way. To use an alternate comparer, specify the `answers` key as a dictionary with keys `comparer` and `comparer_params` rather than a single string.

 For example, if grading angles in degrees, it may be useful to compare formulas modulo 2&#960;. You can write your own comparer functions, but for this we can use the `congruent_modulo` comparer from `mitxgraders.comparers`. This grader will accept any input congruent to `'b^2/a'` modulo `2*pi`.

```pycon
>>> from mitxgraders import FormulaGrader
>>> from mitxgraders.comparers import congruence_comparer
>>> grader = FormulaGrader(
...     answers={
...         'comparer': congruence_comparer,
...         # first parameter is expected value, second is the modulus
...         'comparer_params': ['b^2/a', '2*pi']
...     },
...     variables=['a', 'b'],
...     tolerance='1%'
... )

>>> grader(None, 'b^2/a + 6*pi')['ok']
True
>>> grader(None, 'b^2/a + 5.5*pi')['ok']
False

```

Here, the `comparer_params` (`['b^2/a', '2*pi']`) are evaluated just like the student input, and used by the comparer function during grading.

## Available Comparers

The table below lists the comparers are exported by `mitxgraders.comparers` along with the expected comparer parameters. Note that `comparer_params` is **always** a list of strings, and can use any variables available to the student. When using an ordered `ListGrader`, they can also use sibling values.

| `comparer`   | use with | `comparer_params` <br/> (a list of strings)  | purpose |
|---|---|---|---|
| `equality_comparer` | `FormulaGrader` <br/> `NumericalGrader` <br/> `MatrixGrader` | `[expected]` | checks that student input and `expected` differ by less than grader's tolerance. |
| `congruence_comparer` |  `FormulaGrader` <br/> `NumericalGrader` | `[expected, modulus]` | reduces student input modulo modulus, then checks for equality within grader's tolerance |
| `between_comparer` |  `FormulaGrader` <br/> `NumericalGrader` | `[start, stop]` | checks that student input is real and between `start` and `stop`  |
| `eigenvector_comparer` | `MatrixGrader`  | `[matrix, eigenvalue]`  | checks that student input is an eigenvector of `matrix` with eigenvalue `eigenvalue` within grader's tolerance  |

FormulaGrader (and its subclasses) use `equality_comparer` as the default. That is, specifying `FormulaGrader(answers='x*y', variables=['x', 'y'])` is equivalent to
```pycon
>>> from mitxgraders.comparers import equality_comparer
>>> grader = FormulaGrader(
...     answers={
...         'comparer': equality_comparer,
...         'comparer_params': ['x*y']
...     },
...     variables=['x', 'y']
... )

```

## Custom comparer functions

In addition to using the comparers provided by `mitxgraders.comparers`, you can write your own.

See [comparers.py](https://github.com/mitodl/mitx-grading-library/tree/master/mitxgraders/comparers/comparers.py) for examples
