# FormulaGrader

`FormulaGrader` is the grading class used to grade mathematical formulas and closely resembles the behavior of edX's `<formularesponse />` tag, but with much more versatility.

!!! Note
    - All expressions are treated in a case sensitive manner. This means that variables `m` and `M` are distinct. Case-insensitive `FormulaGrader`s were deprecated in [Version 1.1.0](../changelog.md#version-110)
    - All whitespace is stripped from formulas that are entered. So, `1 + x ^ 2` is equivalent to `1+x^2`.


## Variables and Sampling

`FormulaGrader` grades a formula by numerical sampling. That is, random values are assigned to each of the unknown variables and unknown functions, and the numerical value of the student's input expression and author's answer are calculated. The sampling process is repeated, and if the student answer and author answer compare within the desired tolerance enough times, the student input is graded as correct.

Variables are configured by including a list of strings of each variable name as follows.

```pycon
>>> from mitxgraders import *
>>> grader = FormulaGrader(
...     answers='1+x^2+y',
...     variables=['x', 'y']
... )

```

Note that the `answers` parameter follows all of the usual allowances from `ItemGrader`.

The variables need to have numbers randomly assigned to them. Each is sampled from a [sampling set](sampling.md), which is `RealInterval()` by default (random numbers between 1 and 5). A variety of different sampling sets are available, including random complex numbers. To specify the sampling set to use for a variable, use the `sample_from` key.

```pycon
>>> grader = FormulaGrader(
...     answers='1+x^2+y+z/2',
...     variables=['x', 'y', 'z'],
...     sample_from={
...         'x': ComplexRectangle(),
...         'y': [2, 6],
...         'z': (1, 3, 4, 8)
...     }
... )

```

The `sample_from` key must be a dictionary of `'variable_name': sampling_set` pairs. You can specify a sampling set, a real interval, or a discrete set of values to sample from. The above example shows each of these in order.


### Variable Names

Variable names are case-sensitive. They must start with a letter, and can be proceded by any combination of letters and numbers. There are two ways to write subscripts and superscripts:

* Old edX style: `var_123` (we also allow the use of multiple underscores for backwards compatability with edX, although it is not recommended that this be used)
* Tensor style: `var_{123}`, `var_{123}^{456}` (subscript first), or `var^{456}`

Sub/superscripts can contain any combination of letters and numbers. Tensor style sub/superscripts are allowed to start with a `-` sign.

All types of variable names are allowed to end with an arbitrary number of primes `'` (apostrophes, useful to indicate differentiation or different reference frames). Students on tablets may need to disable "smart quotes" to enter this character.

The AsciiMath renderer used in `<textline>` entries in edX has a number of special symbols that can help make variable names look like particular mathematical entries. A handful of these are `hatx`, `vecx`, `tildex`, `barx`, `dotx` and `ddotx`. There are also a handful of other reserved names in AsciiMath; we recommend testing your variables to ensure that they render as expected.


### Numbered Variables

You can also specify special variables that are numbered. For example, if you specify that `a` is a numbered variable, students can include `a_{0}`, `a_{5}`, `a_{-2}`, etc, using any integer. All entries for a numbered variable will use the sampling set specified by the base name.

```pycon
>>> grader = FormulaGrader(
...     answers='a_{0} + a_{1}*x + 1/2*a_{2}*x^2',
...     variables=['x'],
...     numbered_vars=['a'],
...     sample_from={
...         'x': [-5, 5],
...         'a': [-10, 10]
...     }
... )

```

If you have a variable name that would clash with a numbered variable (say, you defined `a_{0}` and also a numbered variable `a`), then the specific variable has precedence.


## Samples and Failable Evaluations

To control the number of samples that are checked to ensure correctness, you can modify the `samples` key.

```pycon
>>> grader = FormulaGrader(
...     answers='1+x^2',
...     variables=['x'],
...     samples=10
... )

```

The default for `samples` is 5.

You may want to allow for a certain number of comparisons to fail before the student is marked incorrect. To do this, set `failable_evals`. This should be used very sparingly!

```pycon
>>> grader = FormulaGrader(
...     answers='1+x^2',
...     variables=['x'],
...     samples=10,
...     failable_evals=1
... )

```


## Constants

By default, four constants are defined: `e`, `pi`, and `i=j=sqrt(-1)`. You can define new constants by passing in a dictionary to `user_constants` as follows.

```pycon
>>> grader = FormulaGrader(
...     answers='1/sqrt(1-v^2/c^2)',
...     variables=['v'],
...     user_constants={
...         'c': 3e8
...     }
... )

```

Constants are treated as variables that only ever have one value.

If you want to remove a default constant, you can do so by setting it to `None`:

```pycon
>>> grader = FormulaGrader(
...     answers='sqrt(-1)',
...     user_constants={
...         'i': None,
...         'j': None
...     }
... )

```


### Infinities

When an expression results in an infinity, students are presented with an error message asking them to check for overflow. If you actually want infinity to be an acceptable answer, then you can specify `allow_inf=True`. This allows expressions to evaluate to infinity (or negative infinity), and also makes the constant `infty` available for students to use.

```pycon
>>> # Without allow_inf turned on:
>>> grader = FormulaGrader(
...     answers='infty',
...     user_constants={
...         'infty': float('inf')
...     }
... )
>>> try:
...     grader(None, 'infty')
... except CalcError as error:
...     print(error)
Numerical overflow occurred. Does your expression generate very large numbers?
>>> # With allow_inf turned on:
>>> grader = FormulaGrader(
...     answers='infty',
...     allow_inf=True
... )
>>> grader(None, 'infty') == {'ok': True, 'msg': '', 'grade_decimal': 1}
True

```


## Functions

By default, a large array of mathematical functions are available for use. See the full list [here](functions_and_constants.md). Note that all functions are capable of handling complex expressions unless otherwise stated. In the following example, `z*z` is recognized to be different from `abs(z)^2`.

```pycon
>>> grader = FormulaGrader(
...     answers='abs(z)^2',
...     variables=['z'],
...     sample_from={
...         'z': ComplexRectangle()
...     }
... )
>>> grader(None, 'z*z')['ok']
False
>>> grader(None, 'z*conj(z)')['ok']
True

```


### User Functions

You can make user-defined functions available for students to use in their answers. To add user-defined functions, pass in a dictionary to the `user_functions` key as follows.

```pycon
>>> grader = FormulaGrader(
...     answers='x*x',
...     variables=['x'],
...     user_functions={'f': lambda x: x*x}
... )

```

This defines a function `f(x) = x^2` that students may use. User-defined function names must start with a letter, and can use numbers and underscores, such as `my_func2`. They are also allowed to have apostrophes (primes) at the end of the name, such as to indicate derivatives. Eg, `f''`. Be careful about using quotation marks appropriately when using primes in function names, as in the following example.

```pycon
>>> grader = FormulaGrader(
...     answers="f''(x)",
...     variables=['x'],
...     user_functions={"f''": lambda x: x*x}
... )

```


### Choosing a Function Randomly

You can also specify random functions by specifying a sampling set for a function. You can provide a list of functions to randomly choose from as follows.

```pycon
>>> import numpy as np
>>> grader = FormulaGrader(
...     answers="f(x)",
...     variables=['x'],
...     user_functions={"f": [np.sin, np.cos]}
... )

```

Each time this formula is checked, the function `f` will be sampled from the list of available functions.

You can also specify a random well-behaved function by using the `RandomFunction()` sampling set.

```pycon
>>> grader = FormulaGrader(
...     answers="f''(x) + omega^2*f(x)",
...     variables=['x', 'omega'],
...     user_functions={
...         "f": RandomFunction(),
...         "f''": RandomFunction()
...     }
... )

```

This allows you to grade mathematical expressions that involve unknown functions, such as the differential equation described in this example. See [Sampling](sampling.md#randomfunction) for further options associated with `RandomFunction`.


## Overriding Default Functions and Constants

You can override default functions and constants if you really want, although this is discouraged and requires suppressing warnings with `suppress_warnings=True`. The following grader raises this warning when constructed:

```pycon
>>> try:
...     grader = FormulaGrader(
...         answers='x^2',
...         variables=['x'],
...         user_functions={'sin': lambda x: x*x},
...     )
... except ConfigError as error:
...     print(error)
Warning: 'user_functions' contains entries 'sin' which will override default values. If you intend to override defaults, you may suppress this warning by adding 'suppress_warnings=True' to the grader configuration.

```

The error can be suppressed by setting `suppress_warnings=True`.

```pycon
>>> grader = FormulaGrader(
...     answers='x^2',
...     variables=['x'],
...     user_functions={'sin': lambda x: x*x},
...     suppress_warnings=True
... )

```


## Restricting Student Input

For some questions, you will want to restrict the sorts of input that are marked correct. For example, if you want students to expand `sin(2*theta)`, then you don't want students to be able to just write `sin(2*theta)` and be graded correct.

`FormulaGrader` offers a number of ways to restrict what sort of answers will be marked correct.


### Instructor Variables

In some situations, you need an extra variable to help define the problem in some way, particularly when using `DependentSampler`. Alternatively, you may want to remove a default constant such as `e`, `i`, `j` or `pi` from the problem. Both of these situations can be addressed by specifying particular variables to be instructor variables, as in the following.

```pycon
>>> grader = FormulaGrader(
...     answers='s/c',
...     variables=['s', 'c', 'phi'],
...     sample_from={
...         's': DependentSampler(depends=['phi'], formula='sin(phi)'),
...         'c': DependentSampler(depends=['phi'], formula='cos(phi)')
...     },
...     instructor_vars=['phi']
... )

```

Here, students can use `s` and `c`, but not `phi` in their answer. The `instructor_vars` key accepts a list of the variables/constants you wish to make unavailable to students.


### Forbidden Strings

You can forbid students from entering certain strings using the `forbidden_strings` key:

```pycon
>>> grader = FormulaGrader(
...     answers='2*sin(theta)*cos(theta)',
...     variables=['theta'],
...     forbidden_strings=['*theta', 'theta*', 'theta/', '+theta', 'theta+', '-theta', 'theta-'],
...     forbidden_message="Your answer should only use trigonometric functions acting on theta, not multiples of theta"
... )

```

If a student tries to use one of these strings, then they receive the `forbidden_message`, without giving away what the forbidden string is. We recommend using this sparingly, as students may find it confusing. The default `forbidden_message` is "Invalid Input: This particular answer is forbidden".

Forbidden strings and student answers are stripped of whitespace before being compared. Thus, if `x + y` is forbidden, then answers containing `x+y` or `x   +   y` will be rejected.


### Blacklists and Whitelists

You can disallow specific functions by adding them to the blacklist of functions as a list of disallowed function names. In the following example, `sin` is disallowed in correct answers.

```pycon
>>> grader = FormulaGrader(
...     answers='sqrt(1 - cos(x)^2)',
...     variables=['x'],
...     sample_from={'x': [0, np.pi]},
...     blacklist=['sin']
... )

```

If you want to exclude everything except for a specific set of functions, instead use a whitelist. In the following example, the only allowed functions in correct answers are `sin` and `cos`.

```pycon
>>> grader = FormulaGrader(
...     answers='sin(x)/cos(x)',
...     variables=['x'],
...     whitelist=['sin', 'cos']
... )

```

If you want to exclude all functions, use `whitelist=[None]`:

```pycon
>>> grader = FormulaGrader(
...     answers='pi/2-x',
...     variables=['x'],
...     whitelist=[None]  # no functions are allowed
... )

```

You cannot use a whitelist and a blacklist at the same time.


### Required Functions

You can specifically require certain functions to appear in the solution. Any solution that does not include all of these functions will generate an error message. To do this, specify a list of strings of function names that are required.

```pycon
>>> grader = FormulaGrader(
...     answers='2*sin(theta)*cos(theta)',
...     variables=['theta'],
...     required_functions=['sin', 'cos']
... )

```


## Tolerance

Student inputs are compared to answers with a numerical tolerance. You can set this as an absolute number (eg, `0.1`) or a percentage (eg, `'0.01%'`, which is the default tolerance). Tolerances must be nonnegative numbers or percentages.

```pycon
>>> grader = FormulaGrader(
...     answers='2*sin(theta)*cos(theta)',
...     variables=['theta'],
...     tolerance=0.00001
... )

```

Tolerances are necessary because of numerical roundoff error that lead to small differences in evaluations of algebraically equivalent expressions. Zero tolerance should be used sparingly, perhaps only with integer sampling and answers.

Note that if the answer is exactly `0` (or can be sampled to be exactly `0`, such as when using integer sampling), percentage tolerances don't work (as any percentage of zero is still zero). This means that the student-supplied answer must also evaluate to exactly zero to be graded correctly. Note that answers like `cos(pi/2)` evaluate to approximately `10^(-16)` due to numerical roundoff error. If you want such answers to be graded correctly, make sure to use an absolute tolerance instead of a relative tolerance on such questions.


## Suffixes

Numbers with a `%` at the end will be treated as percentages, and converted to the appropriate decimals. If you desire, you can also enable the use of metric suffixes by setting the appropriate setting as follows.

```pycon
>>> grader = FormulaGrader(
...     answers='2m*a',  # Equivalent to '0.002*a'
...     variables=['a'],
...     metric_suffixes=True
... )

```

The included suffixes are:

* `k`: 1e3
* `M`: 1e6
* `G`: 1e9
* `T`: 1e12
* `m`: 1e-3
* `u`: 1e-6
* `n`: 1e-9
* `p`: 1e-12

We strongly recommend _not_ combining these suffixes with the variables names `k`, `M`, `G`, `T`, `m`, `u`, `n` or `p`, as `2m` and `2*m` will then represent two very different things, which can lead to much student confusion.


## Sibling Variables

When a student submits several mathematical expressions as part of one problem, it is sometimes useful to grade these inputs in comparison to each other. This can be done using *sibling variables*, which are available when `FormulaGrader` is used as a subgrader in **ordered** `ListGrader` problems.

For example:

```pycon
>>> grader = ListGrader(
...     answers=[
...         ('x', '2*x','3*x'),     # first input can be any of these 3 answers
...         'sibling_1^2',          # second input must be first input squared
...         'sibling_2^2'           # third input must be second input squared
...     ],
...     ordered=True,
...     subgraders=FormulaGrader(variables=['x'])
... )

```

Note that in this example, the sequence of inputs `['2*x', 4*x^2, 16*x^4]` is correct, and so is `['3*x', 9*x^2, 81*x^4]`, but `['3*x', 4*x^2, 16*x^4]` receives only two-thirds credit (from the first entry matching a given answer, and the last entry being the square of the second entry).

```pycon
>>> student_inputs = ['2*x','4*x^2', '16*x^4']
>>> result1, result2, result3 = grader(None, student_inputs)['input_list']
>>> result1['ok'], result2['ok'], result3['ok']
(True, True, True)

>>> student_inputs = ['3*x','9*x^2', '81*x^4']
>>> result1, result2, result3 = grader(None, student_inputs)['input_list']
>>> result1['ok'], result2['ok'], result3['ok']
(True, True, True)

>>> student_inputs = ['3*x','4*x^2', '16*x^4']
>>> result1, result2, result3 = grader(None, student_inputs)['input_list']
>>> result1['ok'], result2['ok'], result3['ok']
(True, False, True)

```

Notes:

- Sibling variables are available to `FormulaGrader`, `NumericalGrader`, and `MatrixGrader`, but only in **ordered** `ListGrader` problems.
- The jth student input is referenced as `sibling_j`. (Exception: If nesting `ListGraders` with grouping, `sibling_j` refers to the jth member of any particular group.)
- Students are not able to use `sibling_j` in any of their answers.


## Comparer Functions

Comparer functions allow you to compare the student input to the author's expectation using aspects other than equality, or to use a given scheme to assign partial credit. See [Comparer Functions](comparer_functions.md) for details.


## Other Improvements

We have made a number of other improvements over the edX formula graders, including:

* Square roots and other functions have a wider domain: with edX's default FormulaResponse, authors need to be careful that expressions like `sqrt(x-1)` or `(x-1)^0.5` always pass nonnegative inputs to the square root and power functions. Our square root, power, logarithm, and inverse trigonometric functions accept a wider array of inputs (the entire complex plane, minus poles). For this reason, authors can feel safe using the default sample range in most cases.
* Our parser uses a parsing cache, and hence runs much more efficiently than the edX graders.
* If a student inputs an expression with mismatched parentheses, this generates an intelligible error message that points to the exact issue.
* When students use an unknown variable, the resulting error message highlights that the unknown quantity was interpreted as a variable.
* Similarly, when students use an unknown function, the resulting error message highlights that the unknown quantity was interpreted as a function. If a variable of that name exists, the error message suggests that a multiplication symbol was missing.
* If an unexpected error occurs, students will see a generic "invalid input" message. To see exactly where things went wrong, set the `debug` flag to `True`, and a more technical message will usually be displayed.
* Full sampling details are included when the `debug` flag is set to `True`.
* Enhancements to the AsciiMath renderer (the preview that students see when using `<textline />` inputs) are available using our highly recommended [AsciiMath renderer definitions](renderer.md).

Note that a few of these improvements have been merged into edX by the authors of this library.


## Options Listing

Here is the full list of options specific to a `FormulaGrader`.

```python
grader = FormulaGrader(
    variables=list,  # default []
    numbered_vars=list,  # default []
    sample_from=dict,  # default {}
    samples=int,  # default 5
    user_functions=dict,  # default {}
    user_constants=dict,  # default {}
    failable_evals=int,  # default 0
    instructor_vars=list,  # default []
    blacklist=list,  # default []
    whitelist=list,  # default []
    forbidden_strings=list,  # default []
    forbidden_message=str,  # default 'Invalid Input: This particular answer is forbidden'
    required_functions=list,  # default []
    metric_suffixes=bool,  # default False
    tolerance=(float | percentage),  # default '0.01%'
)
```
