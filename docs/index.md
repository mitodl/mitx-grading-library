# MITx Grading Library: An Overview

The `mitxgraders` Python library provides a number of configurable Python classes that can be used as graders in edX custom response problems.

## Relevant Links

* A [complete example course](https://edge.edx.org/courses/course-v1:MITx+grading-library+examples/) that demonstrates most of the features of this library is available on edX edge
* [Complete source code](https://github.com/mitodl/mitx-grading-library) for the library and the aforementioned example course is available on github


## Why use MITxGraders

Use MITxGraders because it:

 - has many capabilities beyond the standard edX options
 - is highly configuration but with *sensible defaults*
 - provides useful error messages
      - to students (when submitting answers &mdash; for example, formula parsing errors)
      - to problem authors (when configuring a grader)
 - is reliable (extensively tested)
 - is open source (BSD-3 license, [our Github repo](https://github.com/mitodl/mitx-grading-library))
 - has an [excellent example edX course](https://edge.edx.org/courses/course-v1:MITx+grading-library+examples/)

## Two Typical Examples

Typical usage in an edX course looks like:
```XML
<!-- First Example -->
<problem>
<script type="loncapa/python">
from mitxgraders import FormulaGrader, RandomFunction
grader = FormulaGrader(
    variables=["x"],
    # allows students to use generic functions f and f' in their input
    user_functions={ "f": RandomFunction(), "f'":RandomFunction() }
)
</script>

  <p>Enter the derivative of \(g(x) = e^{f(x^2)} \).</p>
  <!-- answer is provided to the grader when using single inputs -->
  <customresponse cfn="grader" answer="e^(f(x)) * f'(x^2) * 2*x">
    <textline math="true" />
  </customresponse>

</problem>
```
The resulting problem would be similar to an edX `<formularesponse />` problem, but allows students to use additional generic functions `f(x)` and `f'(x)` in their submissions.

The next example grader would grade an unordered list of mathematical expressions.

```XML
<problem>
<script type="loncapa/python">
from mitxgraders import FormulaGrader, ListGrader
grader = FormulaGrader(
    answers=['x-2', 'x+2'],
    ordered=False,
    subgraders=FormulaGrader(variables=['x'])
)
</script>

  <p>What are the linear factors of \((x^2 - 4)\)?</p>
  <customresponse cfn="grader">
    <!-- correct_answer is shown to student when they press [Show Answer].
         Its value is not used for grading purposes -->
    <textline math="true" correct_answer="x - 2" />
    <textline math="true" correct_answer="x + 2" />
  </customresponse>

</problem>
```

## Loading in edX

Download [python_lib.zip](python_lib.zip) and place it in your static folder (XML workflow) or upload it as a file asset (Studio workflow). If you already have a python_lib.zip, you'll need to merge ours with yours and re-zip. If you want to use our AsciiMath renderer definitions, place the [MjxPrep.js](MjxPrep.js) file in your static folder (XML) or upload the file to your course assets (Studio).

The basic idea of this library is that it contains a number of classes that can be used as the check function for an edX custom response problem. Different classes of grader are used for different inputs. We begin by presenting a brief overview on how the grading classes are used in general.

## Grading Classes

Grading classes generally fall into two categories: single-input graders and multi-input graders.

**Single-input graders** grade a single input. All single-input graders are built on a framework we call an `ItemGrader`. We recommend understanding how `ItemGrader`s work before diving into more specifics.

- [ItemGrader](item_grader.md)
    - [StringGrader](string_grader.md) for grading simple strings of text
    - [FormulaGrader](grading_math/formula_grader.md) for grading scalar formulas
    - [NumericalGrader](grading_math/numerical_grader.md) for grading numbers
    - [MatrixGrader](grading_math/matrix_grader/matrix_grader.md) for grading formulas with vectors and matrices
    - [SingleListGrader](grading_lists/single_list_grader.md) for grading a delimiter-separated (default: comma-separated) list of inputs in a single response box

**Multi-input graders** are for grading multiple input boxes at once. They are composed of single-input graders working in concert, handled by the general `ListGrader` class. At this stage, `ListGrader` is the only multi-input grader included in the library, although plugins can be used to construct further examples.

- [ListGrader](grading_lists/list_grader.md) for grading a list of inputs. Examples:
    - grade an ordered list of strings
    - grade an unordered list of mathematical expressions
    - grade a list of eigenvalue-eigenvector pairs

## Using Grading Classes

All grading classes are instantiated by calling them. Options can be provided using keyword arguments as
```python
grader = FakeGradingClass(option_1=value_1, option_2=value2)
# FakeGradingClass is not real! It's just a placeholder
```
or with a configuration dictionary:
```python
config = {'option_1': value_1, 'option_2': value_2}
grader = FakeGradingClass(config)
```
Passing the configuration as a dictionary can be useful if you are using the same configuration for multiple problems. However, you cannot 'mix and match' these two options: if a configuration dictionary is supplied, any keyword arguments are ignored.

Most configuration options are specific to their grading classes. For example, `FormulaGrader` has a `variables` configuration key, but `NumericalGrader` does not.

A few configuration options are accessible to all grading classes.

### Debugging

Every grading class has a debug option. By default, `debug=False`. To receive debug information from a given grader, specify `debug=True`. Some graders will provide more debug information than others. Debug information can be used by authors to check to make sure that the graders are behaving as expected, but shouldn't be made available to students.

```python
grader = GradingClass(debug=True)
```

### Validation

Every grading class has a `suppress_warnings` key.

The options passed to a grading class undergo extensive validation and graders will throw errors if instantiated with invalid options.

A few error messages serve only as warnings. For example, if you attempt to configure a `FormulaGrader` with `pi` as a variable, you will receive a warning:

```pycon
>>> from mitxgraders import FormulaGrader
>>> grader = FormulaGrader(variables=['pi'])
Traceback (most recent call last):
ConfigError: Warning: 'variables' contains entries '['pi']' which will override default values. If you intend to override defaults, you may suppress this warning by adding 'suppress_warnings=True' to the grader configuration.
```

As the warning message says, if you really want to override the default value of `'pi'` (not recommended!) then you can suppress this warning by setting `suppress_warnings=True`.


## Plugins

Any `.py` file stored in the `plugins` folder will be automatically loaded. All variables in the `__all__` list will be made available when doing `from mitxgraders import *`. See `template.py` for an example.

You can define custom grading classes in your plugin. To learn how this works, we recommend copying the code from `stringgrader.py`, renaming the class, and building a simple plugin based on `StringGrader`.

We are happy to include user-contributed plugins in the repository for this library. If you have built a plugin that you would like to see combined into this library, please contact the authors through [github](https://github.com/mitodl/mitx-grading-library). We are also willing to consider incorporating good plugins into the library itself.
