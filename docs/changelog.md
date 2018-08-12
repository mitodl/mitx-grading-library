# Change Log

## Version 1.2

### Version 1.2.0

This version includes a number of new features and documentation updates.

* A new [documentation website](https://mitodl.github.io/mitx-grading-library/)
* Math parser now supports multivariable functions and array input (vector, matrix, etc).
* Many improvements to our mathjax preprocessor
* Improvements to balanced bracket validator.
* Added new class `MatrixGrader` (see [MatrixGrader documentation](grading_math/matrix_grader/matrix_grader.md)) along with supporting sampling classes `RealMatrices` and `RealVectors`
* When `FormulaGrader` (and its subclasses) are used inside an ordered `ListGrader`, authors can now grade multiple student inputs in comparison to each other by specifying answers in terms of [sibling variables](grading_math/formula_grader.md/#sibling-variables)
* `FormulaGrader` (and its subclasses) now support [comparer functions](grading_math/comparer_functions.md) that can be used to grade student input more flexibly. For example, rather than checking checking that the student input and author input are equal, check that they are equal modulo a certain number. Built-in comparers:
    * equality_comparer
    * congruence_comparer
    * between_comparer
    * eigenvector_comparer


## Version 1.1.x

### Version 1.1.2
* This version includes an internal change to the way that errors are handled during check.
  * If you only use builtin graders (FormulaGrader, ListGrader...) or public plugins (IntegralGrader) you should not notice any difference.
  * If you have previously written your own grading class, this change could affect what errors messages are displayed to students. In particular, only exceptions inheriting from `MITxError` will display their messages to students; other errors will be replaced with a generic error message.


### Version 1.1.1
* Added AsciiMath renderer definitions
* We now check for naming collisions in your configuration
* Cleaned up voluptuous incorporation
* Extend domain of factorial function to all complex, except negative integers
* Removed .pyc files from the zip file
* Minor bug fixes

### Version 1.1.0
* Added numbered variables to FormulaGrader
* Removed case-insensitive comparisons from FormulaGrader and IntegralGrader.

    !!! warning
        This is a departure from edX and is a breaking change for authors who used case-insensitive FormulaGraders. However:

        - Case-sensitive has always been the default for FormulaGrader and we are not aware of authors using case-insensitive FormulaGraders.
        - Pedagogically, we believe that students should think of `M` and `m` are different variables.
        - Removing case-insensitive comparison fixes a number of ambiguous situations.



## Version 1.0.x

### Version 1.0.5
* Improved debugging information for FormulaGrader
* FormulaGrader and IntegralGrader perform whitelist, blacklist, and forbidden_string checks after determining answer correctness. Incorrect answers using forbidden strings / functions are now marked incorrect, while correct answers using forbidden strings / functions raise errors.
* Minor improvements to existing unit tests

### Version 1.0.4
* Authors can now specify a custom comparer function for FormulaGrader
* IntegralGrader now handles complex integrands, and gives meaningful error messages
  for complex limits.
* Miscellaneous bug fixes for tensor variable name parsing

### Version 1.0.3

* Added tensor variable names

### Version 1.0.2

* Added error messages for overflow, division-by-zero, and out-of-domain errors in formulas
* Added tests to reach 100% coverage
* Removed redundant code
* Fixed some bugs in unused code

### Version 1.0.1

* Added DependentSampler
* Fixed issue with zip file tests
* Added doctests to test suite
* Fixed bug in FormulaGrader when given an empty string
