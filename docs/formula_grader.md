# FormulaGrader and NumericalGrader

FormulaGrader and NumericalGrader are the grading classes that are used to grade numbers and formulas. They closely resemble the edX formularesponse and numericalresponse tags, but with much more versatility.

We begin by introducing FormulaGrader. NumericalGrader is a special version of FormulaGrader, described towards the end of this document.

All whitespace is stripped from formulas that are entered. So, `1 + x ^ 2` is equivalent to `1+x^2`.


## Variables and Sampling

FormulaGrader grades a formula by randomly assigning values to each of the unknown variables, and computing numerical values for both the solution and the student input. If they compare within the desired tolerance enough times, the student input is graded as correct.

Variables are configured by including a list of strings of each variable name as follows.

````python
grader = FormulaGrader(
    answers='1+x^2+y',
    variables=['x', 'y']
)
````

Note that the `answers` parameter follows all of the usual allowances from ItemGrader.

The variables need to have numbers randomly assigned to them. Each is sampled from a [sampling set](sampling.md), which is RealInterval() by default (random numbers from 1 to 3). A variety of different sampling sets are available, including random complex numbers. To specify the sampling set to use for a variable, use the `sample_from` key.

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

By default, a large array of mathematical functions are available for use. See the full list [here](function_list.md). Note that functions for manipulating complex variables are available. This allows you to grade complex expressions. In the following example, `z*z` is recognized to be different from `abs(z)^2`.

```python
grader = FormulaGrader(
    answers='abs(z)^2',
    variables=['z'],
    sample_from={
        'z': ComplexRectangle()
    }
)
```

### Blacklists and Whitelists

You can disallow specific functions by adding them to the blacklist of functions as a list of disallowed function names. In the following example, `sin` is disallowed.

```python
grader = FormulaGrader(
    answers='sqrt(1 - cos(x)^2)',
    variables=['x'],
    sample_from={'x': [0, np.pi]},
    blacklist=['sin']
)
```

If you want to exclude everything except for a specific set of functions, instead use a whitelist. In the following example, the only allowed functions are sin and cos.

```python
grader = FormulaGrader(
    answers='sin(x)/cos(x)',
    variables=['x'],
    whitelist=['sin', 'cos']
)
```

If you want to exclude all functions, use the following whitelist.

```python
grader = FormulaGrader(
    answers='pi/2-x',
    variables=['x'],
    whitelist=[None]
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

If desired, you can override default functions.

```python
grader = FormulaGrader(
    answers="x^2",
    variables=['x'],
    user_functions={"sin": lambda x: x*x}
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

By default, four constants are defined: `e`, `pi`, and `i`/`j`. You can define new constants by passing in a dictionary to `user_constants` as follows.

```python
grader = FormulaGrader(
    answers='1/sqrt(1-v^2/c^2)',
    variables=['v'],
    user_constants={
        'c': 3e8
    }
)
```

Constants are like variables that only ever have one value. You can overwrite constants if you like by passing in new definitions in user_constants, but we recommend against this. We also recommend ensuring that your constants and variables all have unique names. Variables will overwrite any constants that have the same name.

Note that by default, edX defines the constants `k`, `c` and `T`. In our experience, these constants lead to confusion when answers that should produce invalid variable errors instead simply eat a student's attempt. You can reintroduce them as necessary.


## Forbidden Strings

For some questions, you will want to forbid some specific strings from the answer. For example, if you want students to expand `sin(2*theta)`, then you don't want students to be able to just write `sin(2*theta)` and be graded correct. You can deal with this by forbidding certain strings, as in the following example.

```python
grader = FormulaGrader(
    answers='2*sin(theta)*cos(theta)',
    variables=['theta'],
    forbidden_strings=['*theta', 'theta*', 'theta/', '+theta', 'theta+', '-theta', 'theta-'],
    forbidden_message="Your answer should only use trigonometric functions acting on theta, not multiples of theta"
)
```

If a student tries to use one of these strings, then they receive the `forbidden_message`, without giving away what the forbidden string is. We recommend using this sparingly, as students will find it confusing. The default `forbidden_message` is "Invalid Input: This particular answer is forbidden".


## Tolerance

Student inputs are compared to answers with a numerical tolerance. You can set this as an absolute number (eg, `0.1`) or a percentage (eg, `"0.01%"`, which is the default tolerance).  Tolerances must be positive numbers or percentages.

```python
grader = FormulaGrader(
    answers='2*sin(theta)*cos(theta)',
    variables=['theta'],
    tolerance=0.00001
)
```

Tolerances are necessary because of numerical roundoff error that lead to small differences in evaluations of algebraically equivalent expressions.


## Case Sensitive Input

By default, expressions are treated in a case sensitive manner. This means that variables `m` and `M` are distinct variables. If you want to grade answers in a case-insensitive manner, you can use the following.

```python
grader = FormulaGrader(
    answers='2*sin(theta)*cos(theta)',
    variables=['theta'],
    case_sensitive=False
)
```

This will allow students to use `SIN` and `COS` as well as `sin` and `cos`.


## Suffixes

Numbers with a % at the end will be treated as percentages, and converted to the appropriate decimals.

edX also defines a number of metric suffixes (k, M, G, T, m, u, n, and p) that modify a number appropriately. However, in our experience, these metric suffixes lead to more confusion than use. For example, `2M`, which one would expect should be rejected as an error when `2*M` was intended, is graded incorrectly and eats a student's attempt. Similarly for all of the other metric suffixes.

We have therefore made the decision to disable metric suffixes by default. If you want to enable them, you can do so using the following.

```python
grader = FormulaGrader(
    answers='2*m',
    variables=['m'],
    metric_suffixes=True
)
```

We strongly recommend _not_ doing this when using the following variable names: k, M, G, T, m, u, n, and p.


## NumericalGrader

When you do not have any random functions or variables, you can use NumericalGrader instead of FormulaGrader. NumericalGrader is a specialized version of FormulaGrader with a different default tolerance (`'5%'`). All of the FormulaGrader options are available, with the following exceptions.

* `failable_evals` is always set to 0
* `samples` is always set to 1
* `variables` is always set to `[]` (no variables allowed)
* `sample_from` is always set to `{}` (no variables allowed)
* `user_functions` can only define specific functions, with no random functions

If you are grading simple integers (such as 0, 1, 2, -1, etc), you may want to consider using StringGrader instead of NumericalGrader.


## Other Improvements

We have made a number of other improvements over the edX formula graders. Here are some of the improvements:

* Our parser uses a parsing cache, and hence runs much more efficiently than the edX graders.
* If students input an expression with mismatched parentheses, this generates an intelligible error message that points to the exact issue.
* When students use an unknown variable, the resulting error message highlights that the unknown quantity was interpreted as a variable.
* Similarly, when students use an unknown function, the resulting error message highlights that the unknown quantity was interpreted as a function. If a variable of that name exists, the error message suggests that a multiplication symbol was missing.
* If an unexpected error occurs, students will see a generic "invalid input" message. To see exactly where things went wrong, set the `debug` flag to True, and a more technical message will usually be displayed.


- [Home](README.md)
