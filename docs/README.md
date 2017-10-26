MITx Grading Library Documentation
==================================

This documentation describes how to use the grading library. In particular, it goes through the syntax required to construct each of the different types of graders.

For information on installation and how to use the library in edX, see [here](../README.md).

**Table of Contents**

- [Overview](#overview)
- [Using Grading Classes](#using-grading-classes)
- [Options](#options)
- [Grading Classes](#grading-classes)
- [Plugins](#plugins)

Grading Classes:

- [ItemGrader](item_grader.md)
  - [StringGrader](string_grader.md)
  - [FormulaGrader and NumericalGrader](formula_grader.md)
  - [SingleListGrader](single_list_grader.md)
- [ListGrader](list_grader.md)


Overview
--------

The basic idea of this library is that it contains a number of classes that can be used as the check function for an edX custom response problem. Different classes of grader are used for different inputs. We begin by presenting a brief overview on how the grading classes are used in general.


Using Grading Classes
---------------------

All grading classes are instantiated by calling them. Here, `GradingClass` is a generic grading class (`GradingClass` does not actually exist).

````python
grader = GradingClass(options)
````

The options passed to a grading class may be passed using a configuration dictionary, as

````python
options = {'name': 'value'}
grader = GradingClass(options)
````

or by directly passing them in, as follows.

````python
grader = GradingClass(name='value')
````

You cannot 'mix and match' these two options. If a configuration dictionary is supplied, any keyword arguments are ignored.


Options
-------

Every grading class has a debug option. By default, `debug=False`. To receive debug information from a given grader, specify `debug=True`. Some graders will provide more debug information than others.

````python
grader = GradingClass(debug=True)
````

All other options are specific to the grading class in question.


Grading Classes
---------------

Grading classes generally fall into two categories: single-input graders and multi-input graders.

All graders that grade a single input are built on a framework we call an ItemGrader. We recommend understanding how ItemGraders work before diving into more specifics. We provide a number of graders built off ItemGrader. A special type of ItemGrader is SingleListGrader, which lets you grade a delimiter-separated list of inputs in a single response.

Multi-input graders that are just composed of single-input graders working in concert can be handled by the general ListGrader class. At this stage, ListGrader is the only multi-input grader included in the library, although plugins can be used to construct further examples.

- [ItemGrader](item_grader.md)
  - [StringGrader](string_grader.md)
  - [FormulaGrader and NumericalGrader](formula_grader.md)
  - [SingleListGrader](single_list_grader.md)
- [ListGrader](list_grader.md)


Plugins
-------

Any .py file stored in the `plugins` folder will be automatically loaded. All variables in the __all__ list will be made available when doing `from graders import *`. See `template.py` for an example.

You can define custom grading classes in your plugin. We recommend copying the code from `stringgrader.py`, renaming the class, and building a simple plugin based on `StringGrader` to familiarize yourself with building a plugin.

If you have built a plugin that you would like to see combined into this library, please contact the authors through [github](https://github.com/mitodl/mitx-grading-library).
