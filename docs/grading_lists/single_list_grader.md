# SingleListGrader

If you want a response to be a delimiter-separated list of items, you can use a special ItemGrader called `SingleListGrader` to perform the grading. You need to specify a subgrader (which must be an ItemGrader, and could even be another SingleListGrader) to evaluate each individual item. The basic usage is as follows.

```python
grader = SingleListGrader(
    answers=['cat', 'dog'],
    subgrader=StringGrader()
)
```

To receive full points for this problem, a student would enter `cat, dog` or `dog, cat` into the input box. Entering `cat, octopus` or just `cat` will receive half points. The `answers` key is a python list of the individual answers you wish to use.

You can use a tuple of lists to specify multiple lists of answers, just like normal ItemGraders.

```python
grader = SingleListGrader(
    answers=(
        [('cat', 'feline'), 'dog'],
        ['goat', 'vole'],
    ),
    subgrader=StringGrader()
)
```

Now, `cat, dog` and `goat, vole` will get full grades. But mixes won't: `cat, vole` will score half credit.


## Ordered Input

By default a SingleListGrader doesn't care which order the input is given in. If you want the answers and the student input to be compared in order, set `ordered=True`.

```python
grader = SingleListGrader(
    answers=['cat', 'dog'],
    subgrader=StringGrader(),
    ordered=True
)
```

Now `cat, dog` will receive full grades, but `dog, cat` will be marked wrong. Note that `cat` will receive half credit, but `dog` will receive zero, as dog is incorrect in the first position. Ordered is false by default.


## Length Checking

If students are asked to enter a list of three items but only enter two, should this use up an attempt, or present an error message? If you want to present an error message, turn on length checking.

```python
grader = SingleListGrader(
    answers=['cat', 'dog'],
    subgrader=StringGrader(),
    length_error=True
)
```

If you give this `cat`, it will tell you that you've got the wrong length, and won't use up an attempt.

Length_error is false by default. If you set length_error to True, then all answers in a tuple of lists (rather than a single answer list) must have the same length.


## Choosing Delimiters

You can use whatever delimiter you like. The default is a comma (`,`). The following uses a semicolon as a delimiter. We recommend not using multi-character delimiters, but do not disallow it.

```python
grader = SingleListGrader(
    answers=['cat', 'dog'],
    subgrader=StringGrader(),
    delimiter=';'
)
```

By using different delimiters, it is possible to nest SingleListGraders:

```python
grader = SingleListGrader(
    answers=[['a', 'b'], ['c', 'd']],
    subgrader=SingleListGrader(
        subgrader=StringGrader()
    ),
    delimiter=';'
)
```

Here the expected student input is `a, b; c, d`. It will also take `b, a; d, c` or `c, d; a, b` due to the unordered nature of both lists. However, `a, c; d, b` is only worth half points.


## Turning Partial Credit Off

By default, partial credit is awarded to partially correct answers. Answers that have insufficient items lose points, as do answers that have too many items. To turn off partial credit, set partial_credit to False. It is True by default.

```python
grader = SingleListGrader(
    answers=['cat', 'dog'],
    subgrader=StringGrader(),
    partial_credit=False
)
```

Now `cat, octopus` will receive a grade of zero.


## Messages

Messages from the individual items are all concatenated together and presented to the student. It is also possible to have a `wrong_msg` on the `SingleListGrader`, which is presented to the student if the score is zero and there are no other messages, just like on an `ItemGrader`.

```python
grader = SingleListGrader(
    answers=['cat', 'dog'],
    subgrader=StringGrader(),
    wrong_msg='Try again!'
)
```


## Option Listing

Here is the full list of options specific to a `SingleListGrader`.
```python
grader = SingleListGrader(
    answers=list or tuple of lists,
    subgrader=ItemGrader(),
    partial_credit=bool (default True),
    ordered=bool (default False),
    length_error=bool (default False),
    delimiter=string (default ',')
)
```
