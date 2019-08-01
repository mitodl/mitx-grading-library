# Change Log

# Version 2

This is a major new version with many new features added. We have been very careful to preserve backwards compatibility of the outward-facing API of the library while adding new features. The biggest change (and the reason for the major version number) is that we are now fully compatible with python versions 2.7, 3.6 and 3.7. All typical applications of version 1.2 should be compatible with version 2.0. However, we do warn that we broke internal backwards compatibility in a number of locations in order to accommodate python 3. If you previously wrote custom plugins for version 1.2, we cannot guarantee that they will continue to work in version 2.0.

## Version 2.0

### Version 2.0.2
* Fix a bug with custom AsciiMath preprocessor where lonely square roots (e.g., `x + sqrt + y`) rendered badly.

### Version 2.0.1

* Fixed a bug in StringGrader regex validation that only required the start of student input to match the pattern.

### Version 2.0.0

Feature updates:

* Graders can now be constructed in-line in a customresponse, rather than in a python code block.
* Credit awarded can now be dependent upon the attempt number.
* Introduced a new plug-in to set course-wide defaults that differ from library defaults.
* `StringGrader` received a major overhaul, and can now require minimum character or word lengths, and also pattern match to regular expressions. Further options to treat whitespace were introduced.
* The structure of `SingleListGrader` answers now uses and extends that used by `ItemGrader` answers, leading to more general ways of expressing answers and providing feedback to students.
* Answers to `SingleListGrader` problems can now be inferred from the `expect` keyword.
* `SingleListGrader` can now warn students that they have missing entries.
* Partial credit can now be turned off in `ListGrader` problems.
* Partial credit can now be awarded in matrix entry problems, with messages explaining which entries are correct.
* Implemented `LinearComparer`, which can assign partial/full credit to formula responses that are linearly related to answers.
* Comparers for math problems can now be set much more straightforwardly.
* `floor`, `ceil`, `min` and `max` functions were added to the math library.
* In math problems, introduced an option to apply a transforming function to the answer and student input before comparing.
* Completely overhauled matrix sampling to allow most typical matrix types to be sampled.
* Introduced instructor variables for math problems, which authors can use in constructing the problem, but students may not use in their responses.
* `DependentSampler` now has access to constants and user functions, and no longer needs the `depends` key.
* `DiscreteSet` will now work with arrays.
* All comparers are now imported when using `from mitxgraders import *`.

Under the hood:

* Ensured that the entire library (including tests) is compatible with python 2.7 and python 3.6/3.7, in preparation for edX's upcoming transition to python 3. (The change to having internal unicode literals is the biggest internal backward-compatability-breaking issue from version 1.2.)
* Introduced `CorrelatedComparer`s, which compare multiple samples at once.
* `IntegralGrader` has been promoted from a plug-in to a core component of the library.
* `SpecifyDomain` has been expanded to allow for functions with any number of arguments.
* Javascript preprocessor was tidied up, and further options for customization were included.
* All documentation examples are now run as doctests.
* Upgraded voluptuous to version 0.11.5.
* Upgraded testing infrastructure.

Bug fixes:

* Fixed a bug in assigning partial credit in `ListGrader`s when multiple lists of answers were included.


# Version 1

## Version 1.2

### Version 1.2.3

* Added new custom comparers `vector_span_comparer` and `vector_phase_comparer`.
* Updated AsciiMath preprocessor to handle lonely `mover` (math-over) entries.

### Version 1.2.2

* Added `accept_any` and `accept_nonempty` options to `StringGrader`.
* If only a single text input is present, the `answers` key is inferred from the `expect` attribute of the `customresponse` tag (does not work for `SingleListInput` however).
* Updated AsciiMath preprocessor to handle variable names and user-defined functions properly.
* Various small bug fixes.

### Version 1.2.1

* Added `arctan2(x, y)` function that returns angle between +x axis and the point (x, y); available by default for students to use in FormulaGrader problems.
* Rewrote the expression parser and evaluator. Among other things, new parser provides better error messages when explicit multiplication is forgotten in expressions like `'5x + 3'`. Also validates curly brace balancing, which may be used in tensor variable names.

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


## Version 1.1

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


## Version 1.0

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

### Version 1.0.0

* First release!
