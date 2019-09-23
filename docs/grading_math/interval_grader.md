# IntervalGrader

`IntervalGrader` grades pairs of numbers enclosed in appropriate brackets. It is intended for use in grading intervals, but can be used to grade other pairs of numbers/formulas with enclosing characters. The following are examples of possible entries:

* `[1, 2)`
* `[0, 1 + pi]`

Both the enclosing brackets and the numbers are graded, and a variety of options for partial credit are available.

`IntervalGrader` is an `ItemGrader`, and so can be used in lists as desired.


!!! Warning
    - If using `MJxPrep.js` to format answers nicely, you will probably want to turn
    off column vectors. Otherwise, `[1, 2]` will display as a vector rather than as an interval.

    - If your expressions use a comma in any way, you should change the delimiter from a comma to
    something else.


## Basic Usage

To use an `IntervalGrader`, you can simply call invoke it like a typical grader:

```pycon
>>> from mitxgraders import *
>>> grader = IntervalGrader(answers='[0, 1]')
>>> grader(None, '[0, 1]') == {'ok': True, 'grade_decimal': 1, 'msg': ''}
True

```

Answers may be specified by supplying the relevant answer as a string, as in the above example, either through the `answers` key or through the `expect` keyword of the `customresponse` tag. You can also break out the answer into four constituent parts in a list as follows:

```pycon
>>> from mitxgraders import *
>>> grader = IntervalGrader(answers=['[', '0', '1', ']'])
>>> grader(None, '[0, 1]') == {'ok': True, 'grade_decimal': 1, 'msg': ''}
True

```

Each individual answer component conforms to the `ItemGrader` answers specification, so you can do things like the following:

```pycon
>>> grader = IntervalGrader(
...     answers=[
...         ('[', {'expect': '(', 'msg': 'Your opening bracket is wrong.', 'grade_decimal': 0.5}),
...         '0',
...         '1',
...         (']', {'expect': ')', 'msg': 'Your closing bracket is wrong.', 'grade_decimal': 0.5}),
...     ]
... )
>>> grader(None, '[0, 1)') == {'ok': 'partial', 'grade_decimal': 0.75, 'msg': 'Your closing bracket is wrong.'}
True

```


## Brackets

You can specify the opening and closing brackets that students may use. Specify each separately as a list of acceptable characters. Entries that do not use these brackets will receive an error message.

```pycon
>>> grader = IntervalGrader(
...     answers='[0,1]',
...     opening_brackets='([{',
...     closing_brackets=')]}'
... )

```

The default for `opening_brackets` is `'[('`, while the default for `closing_brackets` is `'])'`.


## Subgrader

Grading of the two math expressions is performed by a subgrader. The default subgrader is `NumericalGrader(tolerance=1e-13, allow_inf=True)`, which allows `infty` as an entry, and otherwise sets a tight absolute tolerance on the answers. If this default doesn't suit your requirements, you may specify your own `FormulaGrader` or `NumericalGrader` as the subgrader for the expressions. This is particularly useful if you want variables to be allowed to appear in the expressions.

```pycon
>>> grader = IntervalGrader(
...     answers='[a,b^2]',
...     subgrader=FormulaGrader(variables=['a', 'b'])
... )

```


## Delimiter

The default delimiter is a comma. However, due to the way expressions are parsed, if your expressions include commas in any location, the answer will not parse correctly. We suggest changing the delimiter to another character, as follows.

```pycon
>>> grader = IntervalGrader(
...     answers='[0:1]',
...     delimiter=':'
... )

```


## Partial Credit (and how credit is assigned in general)

Grading works by first using the subgrader to obtain the decimal grade for each expression the student submitted. For each correct expression, the bracket is then inspected. If the bracket is correct, then the score for that expression is kept (or if `grade_decimal` is set for the bracket, then the score for the expression is multiplied by that entry). If the bracket is incorrect, zero is awarded for that expression. The two resulting scores are then combined to obtain the overall score. If `partial_credit` is set to `False`, then the overall score must be 1 for any credit to be awarded. By default, `partial_credit` is `True`. When partial credit is turned on, each half of the interval is worth 50% of the overall credit. Note that no credit is awarded for getting the entries backwards.

To allow for partial credit when incorrect brackets are used, set up alternative answers using the `ItemGrader` answers specification, as demonstrated in an example above.


## Options Listing

Here is the full list of options specific to an `IntervalGrader`.

```python
grader = IntervalGrader(
    opening_brackets=str,  # defaykt '[('
    closing_brackets=str,  # default '])'
    delimiter=str,  # default ',', must be one character
    partial_credit=bool  # default True
)
```
