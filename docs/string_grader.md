# StringGrader

The StringGrader class does a letter-for-letter comparison of the student's answer with the expected answer. It is the simplest grading class, both in code and in usage.

To use a StringGrader, simply pass in the set of answers you want to grade, as described in the [ItemGrader documentation](item_grader.md).

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


## Option Listing

Here is the full list of options specific to a `StringGrader`.
```python
grader = SingleListGrader(
    case_sensitive=bool (default True),
    strip=bool (default False)
)
```


- [Home](README.md)
