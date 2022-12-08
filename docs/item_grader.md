# ItemGrader

When an individual input needs to be graded, it is graded by an `ItemGrader`. All `ItemGrader`s work by specifying answers and their corresponding points/messages, as well as an optional message for wrong answers. In these examples, we use `StringGrader` as an example of how to use a generic `ItemGrader`. You cannot use a generic `ItemGrader` by itself.

```pycon
>>> from mitxgraders import *
>>> grader = StringGrader(
...     answers='cat',
...     wrong_msg='Try again!'
... )

```

The grader is set up to grade an answer of `cat` as correct, and includes a message that is presented to students if they get the answer wrong. One could pass `grader` in as the `cfn` key for a `customresponse` tag. The following code demonstrates what happens when the grader is called using python (for example, inside a python console). Note that this is only for demonstrating the behavior of the grader, and is not required in order to use the library in edX.

```pycon
>>> grader(None, 'cat') == {'grade_decimal': 1, 'msg': '', 'ok': True}
True
>>> grader(None, 'dog') == {'grade_decimal': 0, 'msg': 'Try again!', 'ok': False}
True

```

You will often see this type of demonstration in this documentation. It serves both to demonstrate how the grader works and to ensure that our examples are always syntactically correct, as these code blocks form part of our documentation testing.

Note that `grader` accepts two arguments. This is because edX passes two arguments to all graders. The first argument is the `expect` or `answer` value associated with the `customresponse` tag. Here, we supply `None`, as the grader already has its answer specified. The second argument is the student input. If the `customresponse` problem has multiple inputs, the second argument is a list of the student inputs.


## Specifying Answers

For all `ItemGrader`s, the `answers` key can be used to specify correct answers, specific feedback messages, and to assign partial credit. It accepts a few formats:

- A single dictionary can be used to specify an answer, feedback, correctness, and partial credit. The dictionary keys are:

    - `'expect'` (required): compared against student answer. Most `ItemGrader`s use strings to specify the `'expect'` value. You may also specify a tuple of values like `('option1', 'option2')` if you want the same grade and message applied to all these inputs.
    - `'grade_decimal'` (optional, a number between `0` and `1` inclusive): The credit associated with this answer (default `1`).
    - `'msg'` (optional, string): An optional feedback message associated with this answer (default `''`).

```pycon
>>> grader = StringGrader(
...     answers={'expect': 'zebra', 'grade_decimal': 1, 'msg': 'Yay!'},
...     wrong_msg='Try again!'
... )
>>> grader(None, 'zebra') == {'grade_decimal': 1, 'msg': 'Yay!', 'ok': True}
True
>>> grader(None, 'cat') == {'grade_decimal': 0, 'msg': 'Try again!', 'ok': False}
True

```

- A single `'expect'` value: can be used to specify the correct answer. For example,

```pycon
>>> grader = StringGrader(
...     answers='zebra',
...     # Equivalent to:
...     # answers={'expect': 'zebra', 'msg': '', 'grade_decimal': 1}
...     wrong_msg='Try again!'
... )
>>> grader(None, 'zebra') == {'grade_decimal': 1, 'msg': '', 'ok': True}
True
>>> grader(None, 'cat') == {'grade_decimal': 0, 'msg': 'Try again!', 'ok': False}
True

```

  Again, most `ItemGrader`s use strings to store `'expect'` values.

- A tuple of the afore-mentioned dictionaries/strings, which specifies multiple possible answers:

```pycon
>>> grader = StringGrader(
...     answers=(
...         # the correct answer
...         'wolf',
...         # an alternative correct answer
...         'canis lupus',
...         # a partially correct answer
...         {'expect': 'dog', 'grade_decimal': 0.5, 'msg': 'No, not dog!'},
...         # a wrong answer with specific feedback
...         {'expect': 'unicorn', 'grade_decimal': 0, 'msg': 'No, not unicorn!'},
...         # multiple wrong answers with specific feedback
...         {'expect': ('werewolf', 'vampire'), 'grade_decimal': 0, 'msg': 'Wrong universe!'}
...     ),
...     wrong_msg='Try again!'
... )
>>> grader(None, 'wolf') == {'grade_decimal': 1, 'msg': '', 'ok': True}
True
>>> grader(None, 'canis lupus') == {'grade_decimal': 1, 'msg': '', 'ok': True}
True
>>> grader(None, 'dog') == {'grade_decimal': 0.5, 'msg': 'No, not dog!', 'ok': 'partial'}
True
>>> grader(None, 'unicorn') == {'grade_decimal': 0, 'msg': 'No, not unicorn!', 'ok': False}
True
>>> grader(None, 'werewolf') == {'grade_decimal': 0, 'msg': 'Wrong universe!', 'ok': False}
True
>>> grader(None, 'vampire') == {'grade_decimal': 0, 'msg': 'Wrong universe!', 'ok': False}
True
>>> grader(None, 'cat') == {'grade_decimal': 0, 'msg': 'Try again!', 'ok': False}
True

```

Internally, the `ItemGrader` converts the answers entry into a tuple of dictionaries. When grading, it asks the specific grading class to grade the response against each possible answer, and selects the best outcome for the student.

The `wrong_msg` is only displayed if the score is zero and there are no other messages.

If no `answers` key is provided, the grader reads from the `expect` or `answer` parameter of the `customresponse` tag (see [edX Syntax](edx.md)). Note that when using a `ListGrader`, the `answers` key is required.


## Option Listing

Here is the full list of options specific to `ItemGrader`s.
```python
grader = ItemGrader(
    answers=(str, dict, (str, dict)),
    wrong_msg=str,  # default ''
)
```
