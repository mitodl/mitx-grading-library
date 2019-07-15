# NumericalGrader

When grading math expressions without functions or variables, you can use `NumericalGrader` instead of `FormulaGrader`. `NumericalGrader` is a specialized version of `FormulaGrader` whose behavior resembles the edX `<numericalresponse/>` tag.

## Configuration

`NumericalGrader` has all of the same options as `FormulaGrader` except:

* `tolerance`: has a higher default value of `'5%'`
* `failable_evals` is always set to 0
* `samples` is always set to 1
* `variables` is always set to `[]` (no variables allowed)
* `sample_from` is always set to `{}` (no variables allowed)
* `user_functions` can only define specific functions, with no random functions

Note that `NumericalGrader` will still evaluate formulas. If you are grading simple integers (such as 0, 1, 2, -1, etc), you may want to consider using `StringGrader` instead of `NumericalGrader`.
