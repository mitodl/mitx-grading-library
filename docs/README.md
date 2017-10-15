Grading
=======

This documentation describes how to use the grading library. In particular, it goes through the syntax required to describe each of the different types of graders.

For information on installation and how to use the library in edX, see [here](../README.md).


**Table of Contents**

- [Overview](#overview)
- [ItemGrader](item_grader.md)
  - [StringGrader](string_grader.md)
  - [NumericalGrader and FormulaGrader](formula_grader.md)
  - [SingleListGrader](single_list_grader.md)
- [ListGrader](list_grader.md)


Overview
--------

The basic idea of this library is that it contains a number of classes that can be used as the check function for an edX custom response problem. Different classes of grader are used for different inputs.

All graders that grade a single input are built on a framework we call an ItemGrader. We recommend understanding how ItemGraders work before diving into more specifics. We provide a number of graders built off ItemGrader. A special type of ItemGrader is SingleListGrader, which lets you grade a delimiter-separated list of inputs in a single response.

If you want a grader to grade multiple inputs, you will need to use ListGrader. There is only one ListGrader. It works by accepting ItemGrader subgraders for the individual inputs.
