# StringGrader

The `StringGrader` class does a letter-for-letter comparison of the student's answer with the expected answer. It is the simplest grading class, both in code and in usage.

To use a `StringGrader`, simply pass in the set of answers you want to grade, as described in the [ItemGrader documentation](item_grader.md).

```python
grader = StringGrader(
    answers='cat'
)
```

This will accept the answer of `cat`, but not `CAT` or `Cat`, as grading is case-sensitive by default.


## Case Sensitive

To perform case-insensitive grading, pass in the appropriate flag as follows.

```python
grader = StringGrader(
    answers='Cat',
    case_sensitive=False
)
```

This will accept `Cat`, `cat` and `CAT`. By default, `case_sensitive=True`.


## Stripping Input

Leading or trailing spaces in an answer rarely change the meaning of the answer. Hence, by default, we strip all leading and trailing spaces from the student input and author-specified answers before comparison. If you want to keep those spaces around for the comparison, you need to disable strip.

```python
grader = StringGrader(
    answers='cat',
    strip=False
)
```

This will accept `cat`, but will reject answers with leading or trailing spaces. By default, `strip=True`.


## Accepting Anything

Sometimes you may just want to accept anything that a student provides. There are two options that allow you to do this. The first is `accept_any`, which will literally accept anything that is entered into the textbox. The second is `accept_nonempty`, which requires the textbox to contain a non-empty submission (blank spaces are stripped). `accept_any` has priority over `accept_nonempty`.

```python
grader = StringGrader(
    answers={'expect': '', 'grade_decimal': 1, 'msg': 'Your answer has been recorded.'},
    accept_any=True
)
```

Note that when either of these options are set to True, it is meaningless to provide more than one answer to check against, as they will all be graded as correct. Also note that you do not need to provide any answer at all in this situation.


## Option Listing

Here is the full list of options specific to a `StringGrader`.
```python
grader = SingleListGrader(
    case_sensitive=bool (default True),
    strip=bool (default False)
)
```
