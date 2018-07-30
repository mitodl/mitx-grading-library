# FormulaGrader

FormulaGrader is the grading class used to grade mathematical formulas and closely resembles the behavior of edX's `<formularesponse />` tag, but with much more versatility.

!!! Note
    - All expressions are treated in a case sensitive manner. This means that variables `'m'` and `'M'` are distinct. Case-insensitive FormulaGraders were deprecated in [Version 1.1.0](../changelog.md#version-110)
    - All whitespace is stripped from formulas that are entered. So, `1 + x ^ 2` is equivalent to `1+x^2`.


## Variables and Sampling

FormulaGrader grades a formula by numerical sampling. That is, random values are  assigned to each of the unknown variables and unknown functions, then the numerical value of the student's input expression and author's answer are calculated. The sampling process is repeated, and if the student answer and author answer compare within the desired tolerance enough times, the student input is graded as correct.

Variables are configured by including a list of strings of each variable name as follows.

````python
grader = FormulaGrader(
    answers='1+x^2+y',
    variables=['x', 'y']
)
````

Note that the `answers` parameter follows all of the usual allowances from ItemGrader.

The variables need to have numbers randomly assigned to them. Each is sampled from a [sampling set](sampling.md), which is RealInterval() by default (random numbers from 1 to 5). A variety of different sampling sets are available, including random complex numbers. To specify the sampling set to use for a variable, use the `sample_from` key.

````python
grader = FormulaGrader(
    answers='1+x^2+y+z/2',
    variables=['x', 'y', 'z'],
    sample_from={
        'x': ComplexRectangle(),
        'y': [2, 6],
        'z': (1, 3, 4, 8)
    }
)
````

The `sample_from` key must be a dictionary of 'variable_name': sampling_set pairs. You can specify a sampling set, a real interval, or a discrete set of values to sample from. The above example shows each of these in order.


## Numbered Variables

You can also specify special variables that are numbered. For example, if you specify that `a` is a numbered variable, students can include `a_{0}`, `a_{5}`, `a_{-2}`, etc, using any integer. All entries for a numbered variable will use the sampling set specified by the base name.

````python
grader = FormulaGrader(
    answers='a_{0} + a_{1}*x + 1/2*a_{2}*x^2',
    variables=['x'],
    numbered_vars=['a'],
    sample_from={
        'x': [-5, 5],
        'a': [-10, 10]
    }
)
````

If you have a variable name that would clash with a numbered variable (say, you defined `a_{0}` and also a numbered variable `a`), then the specific variable has precedence.


## Samples and Failable Evaluations

To control the number of samples that are checked to ensure correctness, you can modify the `samples` key.

````python
grader = FormulaGrader(
    answers='1+x^2',
    variables=['x'],
    samples=10
)
````

The default for `samples` is 5.

You may want to allow for a certain number of comparisons to fail before the student is marked incorrect. To do this, set `failable_evals`. This should be used very sparingly!

````python
grader = FormulaGrader(
    answers='1+x^2',
    variables=['x'],
    samples=10,
    failable_evals=1
)
````


## Functions

By default, a large array of mathematical functions are available for use. See the full list [here](function_list.md). Note that functions for manipulating complex variables are available, which allows you to grade complex expressions. In the following example, `z*z` is recognized to be different from `abs(z)^2`.

```python
grader = FormulaGrader(
    answers='abs(z)^2',
    variables=['z'],
    sample_from={
        'z': ComplexRectangle()
    }
)
```

### User Functions

You can make user-defined functions available for students to use in their answers. To add user-defined functions, pass in a dictionary to the `user_functions` key as follows.

```python
grader = FormulaGrader(
    answers='x*x',
    variables=['x'],
    user_functions={'f': lambda x: x*x}
)
```

This defines a function `f(x) = x^2`. User-defined function names must start with a letter, and can use numbers and underscores, such as `my_func2`. They are also allowed to have apostrophes (primes) at the end of the name, such as to indicate derivatives. Eg, `f''`. Be careful about using quotation marks appropriately when using primes in function names!

```python
grader = FormulaGrader(
    answers="f''(x)",
    variables=['x'],
    user_functions={"f''": lambda x: x*x}
)
```

You can also specify random functions by specifying a sampling set for a function. You can provide a list of functions to randomly choose from as follows.

```python
grader = FormulaGrader(
    answers="f(x)",
    variables=['x'],
    user_functions={"f": [np.sin, np.cos]}
)
```

Each time this formula is checked, the function `f` will be sampled from the list of available functions.

You can also specify a random well-behaved function by using the RandomFunction() sampling set.

```python
grader = FormulaGrader(
    answers="f''(x) + omega^2*f(x)",
    variables=['x', 'omega'],
    user_functions={
        "f": RandomFunction(),
        "f''": RandomFunction()
    }
)
```

This allows you to grade mathematical expressions that involve unknown functions, such as the differential equation described in this example.


## Constants

By default, four constants are defined: `e`, `pi`, and `i=j=sqrt(-1)`. You can define new constants by passing in a dictionary to `user_constants` as follows.

```python
grader = FormulaGrader(
    answers='1/sqrt(1-v^2/c^2)',
    variables=['v'],
    user_constants={
        'c': 3e8
    }
)
```

Constants are like variables that only ever have one value.

## Overriding Default Functions and Constants
You can override default functions and constants if you really want, although this is discouraged and requires suppressing warnings with `suppress_warnings=True`. The grader

```python
grader = FormulaGrader(
    answers='x^2',
    variables=['x'],
    user_functions={'sin': lambda x: x*x},
)
```
will raise an error

> ConfigError: Warning: 'user_functions' contains entries '['sin']' which will override default values. If you intend to override to override defaults, you may suppress this warning by adding 'suppress_warnings=True' to the grader configuration.

The error can be suppressed by setting `suppress_warnings=True`.

## Restricting Student Input

For some questions, you will want to restrict the sorts of input that are marked correct. For example, if you want students to expand `sin(2*theta)`, then you don't want students to be able to just write `sin(2*theta)` and be graded correct.

FormulaGrader offers a few ways to restrict what sort of answers will be marked correct.

### Forbidden Strings

You can forbid students from entering certain strings using the `forbidden_strings` key:

```python
grader = FormulaGrader(
    answers='2*sin(theta)*cos(theta)',
    variables=['theta'],
    forbidden_strings=['*theta', 'theta*', 'theta/', '+theta', 'theta+', '-theta', 'theta-'],
    forbidden_message="Your answer should only use trigonometric functions acting on theta, not multiples of theta"
)
```

If a student tries to use one of these strings, then they receive the `forbidden_message`, without giving away what the forbidden string is. We recommend using this sparingly, as students will find it confusing. The default `forbidden_message` is "Invalid Input: This particular answer is forbidden".

Forbidden strings and student answers are stripped of whitespace before being compared. Thus, if `x + y` is forbidden, then answers containing `x+y` or `x   +   y` will be rejected.

### Blacklists and Whitelists

You can disallow specific functions by adding them to the blacklist of functions as a list of disallowed function names. In the following example, `sin` is disallowed in correct answers.

```python
grader = FormulaGrader(
    answers='sqrt(1 - cos(x)^2)',
    variables=['x'],
    sample_from={'x': [0, np.pi]},
    blacklist=['sin']
)
```

If you want to exclude everything except for a specific set of functions, instead use a whitelist. In the following example, the only allowed functions in correct answers are sin and cos.

```python
grader = FormulaGrader(
    answers='sin(x)/cos(x)',
    variables=['x'],
    whitelist=['sin', 'cos']
)
```

If you want to exclude all functions, use `whitelist=[None]`:

```python
grader = FormulaGrader(
    answers='pi/2-x',
    variables=['x'],
    whitelist=[None] # no functions are allowed
)
```

You cannot use a whitelist and a blacklist at the same time.

### Required Functions

You can specifically require certain functions to appear in the solution. Any solution that does not include all of these functions will generate an error message. To do this, specify a list of strings of function names that are required.

```python
grader = FormulaGrader(
    answers='2*sin(theta)*cos(theta)',
    variables=['theta'],
    required_functions=['sin', 'cos']
)
```

## Tolerance

Student inputs are compared to answers with a numerical tolerance. You can set this as an absolute number (eg, `0.1`) or a percentage (eg, `"0.01%"`, which is the default tolerance).  Tolerances must be nonnegative numbers or percentages.

```python
grader = FormulaGrader(
    answers='2*sin(theta)*cos(theta)',
    variables=['theta'],
    tolerance=0.00001
)
```

Tolerances are necessary because of numerical roundoff error that lead to small differences in evaluations of algebraically equivalent expressions. Zero tolerance should be used sparingly, perhaps only with integer sampling and answers.


## Suffixes

Numbers with a % at the end will be treated as percentages, and converted to the appropriate decimals.

edX also defines a number of metric suffixes (k, M, G, T, m, u, n, and p) that modify a number appropriately. However, in our experience, these metric suffixes lead to more confusion than use. For example, `2M`, which one would expect should be rejected as an error when `2*M` was intended, is accepted by edX, interpreted as `2*10^6`, marked incorrect, and eats a student's attempt. Similarly for all of the other metric suffixes.

We have therefore made the decision to disable metric suffixes by default. If you want to enable them, you can do so using the following.

```python
grader = FormulaGrader(
    answers='2*m',
    variables=['m'],
    metric_suffixes=True
)
```

We strongly recommend _not_ doing this when using the following variable names: k, M, G, T, m, u, n, and p.

## Comparer Functions
By default, FormulaGrader compares the numerically sampled author formula and student formula for equality (within bounds specified by tolerance). Occasionally, it can be useful to compare author and student formulas in some other way. For example, if grading angles in degrees, it may be useful to compare formulas modulo 360.

To use an alternate comparer, specify the `answers` key as a dictionary with keys `comparer` and `comparer_params` rather than a single string. For example, to compare formulas modulo 360:

```python
def is_coterminal(comparer_params_evals, student_eval, utils):
    answer = comparer_params_evals[0]
    reduced = student_eval % (360)
    return utils.within_tolerance(answer, reduced)

grader = FormulaGrader(
    answers={
        'comparer': is_coterminal,
        'comparer_params': ['b^2/a'],
    },
    variables=['a', 'b'],
    tolerance='1%'
)
```

This grader would accept `'b^2/a'` as well as `'b^2/a + 360'`, `'b^2/a + 720'`, etc.

In the grader configuration, `comparer_params` is a list of strings that are numerically evaluated and passed to the comparer function. The `comparer` function is a user-specified function with signature `comparer(comparer_params_evals, student_eval, utils)`. When `FormulaGrader` calls the comparer function, `comparer` the argument values are:
- `comparer_params_evals`: The `comparer_params` list, numerically evaluated according to variable and function sampling.
- `student_eval`: The student's input, numerically evaluated according to variable and function sampling
- `utils`: A convenience object that may be helpful when writing custom comparer functions. Has properties:
  - `utils.tolerance`: The tolerance specified in grader configuration, `0.01%` by default
  - `utils.within_tolerance:` A function with signature `within_tolerance(x, y)` which checks that `y` is within specified tolerance of `x`. Can handle scalars, vectors, and matrices. If tolerance was specified as a percentage, then checks that `|x-y| < tolerance * x`.

## Other Improvements

We have made a number of other improvements over the edX formula graders, including:

* Square roots and other functions have a wider domain: with edX's default FormulaResponse, authors need to be careful that expressions like `sqrt(x-1)` or `(x-1)^0.5` always pass nonnegative inputs to the square root and power functions. Our square root, power, logarithm, and inverse trigonometric functions accept a wider array of inputs (the entire complex plane, minus poles). For this reason, authors can feel safe using the default sample range in most cases.
* Our parser uses a parsing cache, and hence runs much more efficiently than the edX graders.
* If students input an expression with mismatched parentheses, this generates an intelligible error message that points to the exact issue.
* When students use an unknown variable, the resulting error message highlights that the unknown quantity was interpreted as a variable.
* Similarly, when students use an unknown function, the resulting error message highlights that the unknown quantity was interpreted as a function. If a variable of that name exists, the error message suggests that a multiplication symbol was missing.
* If an unexpected error occurs, students will see a generic "invalid input" message. To see exactly where things went wrong, set the `debug` flag to True, and a more technical message will usually be displayed.
* Full sampling details are included when the `debug` flag is set to True.
* Enhancements to the AsciiMath renderer (the preview that students see when using `<textline>` inputs) are available using our [AsciiMath renderer definitions](renderer.md).
