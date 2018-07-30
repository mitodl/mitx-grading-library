# MITx Grading Library Documentation

This documentation describes how to use the grading library. In particular, it goes through the syntax required to construct each of the different types of graders.

For information on installation and how to use the library in edX, see [Getting Started](getting_started.md).

## Overview

The basic idea of this library is that it contains a number of classes that can be used as the check function for an edX custom response problem. Different classes of grader are used for different inputs. We begin by presenting a brief overview on how the grading classes are used in general.


## Using Grading Classes

All grading classes are instantiated by calling them. Here, `GradingClass` is a generic grading class (`GradingClass` does not actually exist).

````python
grader = GradingClass(options)
````

The options provided to a grading class may be passed in directly, as

````python
grader = GradingClass(name='value')
````

You can also pass in a configuration dictionary. This may be helpful if using the same configuration for multiple problems.

````python
options = {'name': 'value'}
grader = GradingClass(options)
````

You cannot 'mix and match' these two options. If a configuration dictionary is supplied, any keyword arguments are ignored.


## Options

The options passed to a grading class undergo extensive validation and graders will throw
errors if instantiated with invalid options.

A few error messages serve only as warnings (e.g., that you are attempting to override a default constant like `pi`). These warning errors can be suppressed by setting

````python
grader = GradingClass(suppress_warnings=True)
````

Every grading class also has a debug option. By default, `debug=False`. To receive debug information from a given grader, specify `debug=True`. Some graders will provide more debug information than others.

````python
grader = GradingClass(debug=True)
````

All other options are specific to the grading class in question.


## Grading Classes

Grading classes generally fall into two categories: single-input graders and multi-input graders.

All graders that grade a single input are built on a framework we call an ItemGrader. We recommend understanding how ItemGraders work before diving into more specifics. We provide a number of graders built off ItemGrader. A special type of ItemGrader is SingleListGrader, which lets you grade a delimiter-separated list of inputs in a single response.

Multi-input graders that are just composed of single-input graders working in concert can be handled by the general ListGrader class. At this stage, ListGrader is the only multi-input grader included in the library, although plugins can be used to construct further examples.

- [ItemGrader](item_grader.md)
  - [StringGrader](string_grader.md)
  - [FormulaGrader](grading_math/formula_grader.md)
  - [NumericalGrader](grading_math/numerical_grader.md)
  - [SingleListGrader](grading_lists/single_list_grader.md)
- [ListGrader](grading_lists/list_grader.md)


## Plugins

Any .py file stored in the `plugins` folder will be automatically loaded. All variables in the __all__ list will be made available when doing `from mitxgraders import *`. See `template.py` for an example.

You can define custom grading classes in your plugin. To learn how this works, we recommend copying the code from `stringgrader.py`, renaming the class, and building a simple plugin based on `StringGrader`.

We are happy to include user-contributed plugins in the repository for this library. If you have built a plugin that you would like to see combined into this library, please contact the authors through [github](https://github.com/mitodl/mitx-grading-library). We are also willing to consider incorporating good plugins into the library itself.
