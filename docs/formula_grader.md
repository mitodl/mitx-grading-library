NumericalGrader and FormulaGrader
=================================

TODO: The below documentation is all old, and should be updated once these classes have been overhauled!

## FormulaGrader
Grades mathematical expressions.

Similar to EdX formularesponse but more flexible. Allows author to specify functions in addition to variables.

### Usage

Grade a formula containing variables and functions:
```python
grader = FormulaGrader(
    answers='a*b + f(c-b) + f(g(a))',
    variables=['a', 'b','c'],
    functions=['f', 'g']
)
```

The learner's input is compared to expected answer using numerical evaluations. By default, 5 evaluations are used with variables sampled on the interval [1,3]. The defaults can be overidden:

```python
grader = FormulaGrader(
    answers='b^2 - f(g(a))/4',
    variables=['a', 'b'],
    functions=['f', 'g'],
    samples=3,
    sample_from={
        'a': [-4,1]
    },
    tolerance=0.1
)
```
You can also provide specific values to use for any variable or function:
```python
def square(x):
    return x**2
grader = FormulaGrader(
    answers='4*f(a)+b',
    variables=['a','b'],
    functions=['f'],
    sample_from={
        'f': UniqueValue(square)
    }
)
```
Grade complex-valued expressions:
```python
grader = FormulaGrader(
    answers='abs(z)^2',
    variables=['z'],
    sample_from={
        'z': ComplexRectangle()
    }
)
```

### Configuration Dictionary Keys

 - answers (list): answers, each specified as a string or dictionary.
 - variables (list of str): variable names, default `[]`
 - functions (list of str): function names, default `[]`
 - samples (int): Positive number of samples to use, default `5`
 - sample_from: A dictionary mapping synbol (variable or function name) to sampling sets. Default sampling sets are:
      for variables, `RealInterval([1,3])`
      for functions, `NiceFunctions({dims=[1,1]})`
 - tolerance (int or PercentageString): A positive tolerance with which to compare numerical evaluations. Default `'0.1%'`
 - case_sensitive (bool): whether symbol names are case senstive. Default `True`
 - failable_evals (int): The nonnegative maximum number of evaluation comparisons that can fail with grader still passing. Default `0`


- [Home](README.md)
