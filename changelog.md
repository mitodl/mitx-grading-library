# Change Log

## Version 1.0.5
* improved debugging information for FormulaGrader
* FormulaGrader and IntegralGrader perform whitelist, blacklist, and forbidden_string checks after determining answer correctness. Incorrect answers using forbidden strings / functions are now marked incorrect, while correct answers using forbidden strings / functions raise errors.
* minor improvements to existing unit tests

## Version 1.0.4
* Authors can now specify a custom comparer function for FormulaGrader
* IntegralGrader now handles complex integrands, and gives meaningful error messages
  for complex limits.
* Miscellaneous bug fixes for tensor variable name parsing

## Version 1.0.3

* Added tensor variable names

## Version 1.0.2

* Added error messages for overflow, division-by-zero, and out-of-domain errors in formulas
* Added tests to reach 100% coverage
* Removed redundant code
* Fixed some bugs in unused code

## Version 1.0.1

* Added DependentSampler
* Fixed issue with zip file tests
* Added doctests to test suite
* Fixed bug in FormulaGrader when given an empty string
