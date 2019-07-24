# MITx Grading Library: An Overview

The `mitxgraders` Python library provides a number of configurable Python classes that can be used as graders in edX custom response problems.

## Relevant Links

* A [complete example course](https://edge.edx.org/courses/course-v1:MITx+grading-library+examples/) that demonstrates most of the features of this library is available on edX edge
* [Complete source code](https://github.com/mitodl/mitx-grading-library) for the library and the aforementioned example course is available on github


## Why use MITxGraders

Use MITxGraders because it:

- has many capabilities beyond the standard edX options
- is highly configurable but with *sensible defaults*
- provides useful error messages
    - to students (when submitting answers &mdash; for example, formula parsing errors)
    - to problem authors (when configuring a grader)
- is reliable (extensively tested)
- is open source (BSD-3 license, [our Github repo](https://github.com/mitodl/mitx-grading-library))
- has an [excellent example edX course](https://edge.edx.org/courses/course-v1:MITx+grading-library+examples/)
- is ready for the future of edX by being compatible with python 2 and 3
- is actively maintained


## Two Typical Examples

Typical usage in an edX course looks like:
```XML
<problem>
<script type="text/python">
from mitxgraders import *
grader = FormulaGrader(
    variables=["x"],
    # allows students to use generic functions f and f' in their input
    user_functions={"f": RandomFunction(), "f'": RandomFunction()}
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
<script type="text/python">
from mitxgraders import *
grader = ListGrader(
    answers=['x-2', 'x+2'],
    subgraders=FormulaGrader(variables=['x'])
)
</script>

  <p>What are the linear factors of \((x^2 - 4)\)? Enter your answers in any order.</p>
  <customresponse cfn="grader">
    <!-- correct_answer is shown to student when they press [Show Answer].
         Its value is not used for grading purposes -->
    <textline math="true" correct_answer="x - 2" />
    <textline math="true" correct_answer="x + 2" />
  </customresponse>

</problem>
```

## Loading in edX

Download [python_lib.zip](https://github.com/mitodl/mitx-grading-library/raw/master/python_lib.zip) and place it in your static folder (XML workflow) or upload it as a file asset (Studio workflow). If you already have a python_lib.zip, you'll need to merge ours with yours and re-zip. If you want to use our AsciiMath renderer definitions (if you have math problems, you'll really want this!), place the [MJxPrep.js](https://raw.githubusercontent.com/mitodl/mitx-grading-library/master/MJxPrep.js) file in your static folder (XML) or upload the file to your course assets (Studio).

The basic idea of this library is that it contains a number of classes that can be used as the check function for an edX custom response problem. Different classes of grader are used for different inputs. We begin by presenting a brief overview on how the grading classes are used in general.


## Grading Classes

Grading classes generally fall into two categories: single-input graders and multi-input graders.

**Single-input graders** grade a single input. All single-input graders are built on a framework we call an `ItemGrader`. We recommend understanding how `ItemGrader`s work before diving into more specifics.

- [ItemGrader](item_grader.md)
    - [StringGrader](string_grader.md) for grading text input (includes pattern matching)
    - [FormulaGrader](grading_math/formula_grader.md) for grading general formulas
    - [NumericalGrader](grading_math/numerical_grader.md) for grading numbers
    - [MatrixGrader](grading_math/matrix_grader/matrix_grader.md) for grading formulas with vectors and matrices
    - [SingleListGrader](grading_lists/single_list_grader.md) for grading a delimited (default: comma-separated) list of inputs in a single response box

**Multi-input graders** are for grading multiple input boxes at once. They are composed of single-input graders working in concert, handled by the general `ListGrader` class. `ListGrader` is the only multi-input grader included in the library, but is incredibly general.

- [ListGrader](grading_lists/list_grader.md) for grading a list of inputs. Examples:
    - grade an ordered list of text inputs
    - grade an unordered list of mathematical expressions
    - grade a list of eigenvalue-eigenvector pairs

**Specialized graders** are used to grade very specific situations. The only specialized grader we presently have is `IntegralGrader`, although plugins can be used to construct further examples.

- [IntegralGrader](grading_math/integral_grader.md) for grading the construction of integrals.


## Questions? Bugs? Issues? Suggestions?

Please contact us by making an issue on [github](https://github.com/mitodl/mitx-grading-library).


## What should I read next?

- If you haven't already done so, we recommend looking at our [example course](https://edge.edx.org/courses/course-v1:MITx+grading-library+examples/) to get an idea of the type of things that the library is capable of.
- It's probably a good idea to start by looking at how to [invoke the grading library in edX](edx.md).
- Next, we recommend looking at the [Introduction to Graders](graders.md) and the overview of [ItemGraders](item_grader.md).
- After that, choose a grader that you're interested in, look at [source code for examples for that grader](https://github.com/mitodl/mitx-grading-library/tree/master/course/problem), and read up on the relevant documentation.

Enjoy!
