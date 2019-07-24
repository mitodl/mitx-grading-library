# SingleListGrader

If you want a response to be a delimiter-separated list of items, you can use a special `ItemGrader` called `SingleListGrader` to perform the grading. You need to specify a subgrader (which must be an `ItemGrader`, and could even be another `SingleListGrader`) to evaluate each individual item. The basic usage is as follows.

```pycon
>>> from mitxgraders import *
>>> grader = SingleListGrader(
...     answers=['cat', 'dog'],
...     subgrader=StringGrader()
... )
>>> grader(None, 'cat, dog') == {'grade_decimal': 1.0, 'msg': '', 'ok': True}
True
>>> grader(None, 'dog, cat') == {'grade_decimal': 1.0, 'msg': '', 'ok': True}
True
>>> grader(None, 'cat, octopus') == {'grade_decimal': 0.5, 'msg': '', 'ok': 'partial'}
True

```

To receive full points for this problem, a student would enter `cat, dog` or `dog, cat` into the input box. Entering `cat, octopus` or just `cat` will receive half points.

The `answers` key follows the usual `ItemGrader` specification, with one change: instead of specifying individual strings or dictionaries, you need to specify lists of strings or dictionaries. Otherwise, the full scope of `ItemGrader` configuration is available to you, such as using tuples to specify multiple lists of answers.

```pycon
>>> grader = SingleListGrader(
...     answers=(
...         [('cat', 'feline'), 'dog'],
...         ['goat', 'vole'],
...     ),
...     subgrader=StringGrader()
... )
>>> grader(None, 'cat, dog') == {'grade_decimal': 1.0, 'msg': '', 'ok': True}
True
>>> grader(None, 'dog, feline') == {'grade_decimal': 1.0, 'msg': '', 'ok': True}
True
>>> grader(None, 'cat, vole') == {'grade_decimal': 0.5, 'msg': '', 'ok': 'partial'}
True

```

Now, `cat, dog` and `goat, vole` will get full grades. But mixes won't: `cat, vole` will score half credit, as `cat` and `dog` are in the same answer list, while `vole` belongs with `goat`.

Below is an example that uses literally all possible answer input styles.

```pycon
>>> grader = SingleListGrader(
...     answers=(
...         [('cat', {'expect': 'feline', 'msg': 'Good enough!'}), 'dog'],
...         {
...             'expect': ['unicorn', 'lumberjack'],
...             'msg': "Well, you just had to do something strange, didn't you?",
...             'grade_decimal': 0.5
...         },
...     ),
...     subgrader=StringGrader()
... )
>>> grader(None, 'feline, unicorn') == {'grade_decimal': 0.5, 'msg': 'Good enough!', 'ok': 'partial'}
True
>>> grader(None, 'hippo, unicorn') == {'grade_decimal': 0.25, 'msg': '', 'ok': 'partial'}
True
>>> grader(None, 'lumberjack, unicorn') == {'grade_decimal': 0.5, 'msg': "Well, you just had to do something strange, didn't you?", 'ok': 'partial'}
True

```

Note that the list of answers can itself occur inside a dictionary that has a grade and message associated with it. In this case, the answers are evaluated as normal, and the overall grade is multiplied by `grade_decimal`. The message is only shown if all of the inputs received credit. So, note that `feline, anything` will get the "Good enough!" message, while the "something strange" message only appears if the student enters both `unicorn` and `lumberjack`.


## Messages

Messages from the individual items are all concatenated together and presented to the student. Overall messages associated with a list are included at the bottom. It is also possible to have a `wrong_msg` on the `SingleListGrader`, which is presented to the student if the score is zero and there are no other messages, just like on an `ItemGrader`.

```pycon
>>> grader = SingleListGrader(
...     answers=['cat', 'dog'],
...     subgrader=StringGrader(),
...     wrong_msg='Try again!'
... )
>>> grader(None, 'wolf, feline') == {'grade_decimal': 0.0, 'msg': 'Try again!', 'ok': False}
True

```


## Ordered Input

By default, a `SingleListGrader` doesn't care which order the input is given in. If you want the answers and the student input to be compared in order, set `ordered=True`.

```pycon
>>> grader = SingleListGrader(
...     answers=['cat', 'dog'],
...     subgrader=StringGrader(),
...     ordered=True
... )
>>> grader(None, 'cat, dog') == {'grade_decimal': 1.0, 'msg': '', 'ok': True}
True
>>> grader(None, 'dog, cat') == {'grade_decimal': 0.0, 'msg': '', 'ok': False}
True

```

Now `cat, dog` will receive full grades, but `dog, cat` will be marked wrong. Note that `cat` will receive half credit, but `dog` will receive zero, as dog is incorrect in the first position. Ordered is `False` by default.


## Length Checking

If students are asked to enter a list of three items but only enter two, should this use up an attempt, or present an error message? If you want to present an error message, turn on length checking.

```pycon
>>> grader = SingleListGrader(
...     answers=['cat', 'dog'],
...     subgrader=StringGrader(),
... )
>>> grader(None, 'cat, dog, unicorn') == {'grade_decimal': 0.5, 'msg': '', 'ok': 'partial'}
True
>>> grader = SingleListGrader(
...     answers=['cat', 'dog'],
...     subgrader=StringGrader(),
...     length_error=True
... )
>>> try:
...     grader(None, 'cat')
... except MissingInput as error:
...     print(error)
List length error: Expected 2 terms in the list, but received 1. Separate items with character ","

```

If you give this `cat`, it will tell you that you've got the wrong length, and won't use up an attempt.

By default, `length_error` is set to `False`. If you set `length_error` to `True`, then all answers in a tuple of lists (rather than a single answer list) must have the same length.


## Empty Entries

In order to protect students from typos, the grader returns an error if a student's response has an empty entry (or an entry that just contains spaces). If you want students to be able to enter a list with an empty entry, you need to disable this behavior by setting `missing_error=False`.

```pycon
>>> grader = SingleListGrader(
...     answers=['cat', 'dog'],
...     subgrader=StringGrader()
... )
>>> try:
...     grader(None, 'cat, dog,')
... except MissingInput as error:
...     print(error)
List error: Empty entry detected in position 3
>>> grader = SingleListGrader(
...     answers=['cat', 'dog'],
...     subgrader=StringGrader(),
...     missing_error=False
... )
>>> grader(None, 'cat, dog,') == {'grade_decimal': 0.5, 'msg': '', 'ok': 'partial'}
True

```


## Choosing Delimiters

You can use whatever delimiter you like. The default is a comma (`,`). The following uses a semicolon as a delimiter. We recommend not using multi-character delimiters, but do not disallow it.

```pycon
>>> grader = SingleListGrader(
...     answers=['cat', 'dog'],
...     subgrader=StringGrader(),
...     delimiter=';'
... )
>>> grader(None, 'cat; dog') == {'grade_decimal': 1.0, 'msg': '', 'ok': True}
True

```

By using different delimiters, it is possible to nest `SingleListGrader`s:

```pycon
>>> grader = SingleListGrader(
...     answers=[['a', 'b'], ['c', 'd']],
...     subgrader=SingleListGrader(
...         subgrader=StringGrader()
...     ),
...     delimiter=';'
... )
>>> grader(None, 'd, c; a, b') == {'grade_decimal': 1.0, 'msg': '', 'ok': True}
True
>>> grader(None, 'a, c; d, b') == {'grade_decimal': 0.5, 'msg': '', 'ok': 'partial'}
True

```

Here the expected student input is `a, b; c, d`. It will also take `b, a; d, c` or `c, d; a, b` due to the unordered nature of both lists. However, `a, c; d, b` is only worth half points.


## Partial Credit

By default, partial credit is awarded to partially correct answers. Answers that have insufficient items lose points, as do answers that have too many items. To turn off partial credit, set `partial_credit=False`. It is `True` by default.

```pycon
>>> grader = SingleListGrader(
...     answers=['cat', 'dog'],
...     subgrader=StringGrader(),
...     partial_credit=False
... )
>>> grader(None, 'cat, octopus') == {'grade_decimal': 0.0, 'msg': '', 'ok': False}
True

```

Now `cat, octopus` will receive a grade of zero.


## Inferred Answers

Just as for normal `ItemGrader`s, the `answers` key can be inferred from the `expect` or `answer` parameter in a `customresponse` tag. Here is an example.

```XML
<problem>

<script type="text/python">
from mitxgraders import *
</script>

<!-- Define the problem -->
<customresponse cfn="SingleListGrader(subgrader=StringGrader())" expect="a, b, c, d">
  <textline />
</customresponse>

</problem>
```

Here, the grader is a `SingleListGrader` using `StringGrader` as a subgrader, and uses default values for all other options. The `answers` key is missing, so it is inferred to be `['a', 'b', 'c', 'd']` from the `expect` parameter of the `customresponse` tag. Answer inference will even work with nested `SingleListGrader`s.


## Option Listing

Here is the full list of options specific to a `SingleListGrader`.
```python
grader = SingleListGrader(
    answers=(list, {'expect': list}, (list, {'expect': list}, )),
    subgrader=ItemGrader(),
    partial_credit=bool,  # default True
    ordered=bool,  # default False
    length_error=bool,  # default False
    missing_error=bool,  # default True
    delimiter=str,  # default ','
)
```
