# StringGrader

The `StringGrader` class is an `ItemGrader` that grades text inputs. It can perform comparisons to expected answers or patterns, and can also accept arbitrary input. It is the simplest grading class, both in code and in usage.

To use a `StringGrader` in its simplest form, simply pass in the set of answers you want to grade, as described in the [ItemGrader documentation](item_grader.md).

```pycon
>>> from mitxgraders import *
>>> grader = StringGrader(
...     answers='cat'
... )
>>> grader(None, 'cat') == {'grade_decimal': 1, 'msg': '', 'ok': True}
True
>>> grader(None, 'CAT') == {'grade_decimal': 0, 'msg': '', 'ok': False}
True
>>> grader(None, 'Cat') == {'grade_decimal': 0, 'msg': '', 'ok': False}
True

```

This example will accept the answer of `cat`, but not `CAT` or `Cat`, as grading is case-sensitive by default.


## Cleaning Input

Leading or trailing spaces in an answer rarely change the meaning of the answer. Hence, by default, we strip all leading and trailing spaces from the student input and author-specified answers before comparison. If you want to keep those spaces around for the comparison, you need to disable strip.

```pycon
>>> grader = StringGrader(
...     answers='cat',
...     strip=False
... )
>>> grader(None, 'cat') == {'grade_decimal': 1, 'msg': '', 'ok': True}
True
>>> grader(None, ' cat') == {'grade_decimal': 0, 'msg': '', 'ok': False}
True

```

This will accept `cat`, but will reject answers with leading or trailing spaces. By default, `strip=True`.

Similarly, if a student uses two (or more) spaces instead of one, that rarely changes the meaning. By default, we convert consecutive spaces into a single space before comparison (this applies to both the instructor-provided answer and the student-provided response). If you want to disable this behavior, you can set `clean_spaces=False` as follows.

```pycon
>>> grader = StringGrader(
...     answers='two  spaces',
...     clean_spaces=False
... )
>>> grader(None, 'two  spaces') == {'grade_decimal': 1, 'msg': '', 'ok': True}
True
>>> grader(None, 'two spaces') == {'grade_decimal': 0, 'msg': '', 'ok': False}
True

```

Here, the answer is `two  spaces`, complete with two spaces (which may not render on a webpage). A student's answer of `two spaces` (with a single space) would be graded incorrect.

Finally, you may have a situation where spaces are completely irrelevant (e.g., when grading a mathematical expression). To instruct the grader to completely ignore all spaces, set `strip_all=True`.

```pycon
>>> grader = StringGrader(
...     answers='(12)(34)',
...     strip_all=True
... )
>>> grader(None, '(1 2) (3 4)') == {'grade_decimal': 1, 'msg': '', 'ok': True}
True

```

This grader will accept `(1 2) (3 4)`, ignoring all spaces in the provided answer.


## Case Sensitive

To perform case-insensitive grading, pass in the appropriate flag as follows.

```pycon
>>> grader = StringGrader(
...     answers='Cat',
...     case_sensitive=False
... )
>>> grader(None, 'Cat') == {'grade_decimal': 1, 'msg': '', 'ok': True}
True
>>> grader(None, 'cat') == {'grade_decimal': 1, 'msg': '', 'ok': True}
True
>>> grader(None, 'CAT') == {'grade_decimal': 1, 'msg': '', 'ok': True}
True

```

This will accept `Cat`, `cat` and `CAT`. By default, `case_sensitive=True`.


## Accepting Anything

Sometimes you may just want to accept anything that a student provides (possibly subject to conditions). This can be useful, for example, when asking for a free response to a prompt, and can be used in conjunction with validation (see below) to accept a variety of answers that satisfy a given pattern. To do this, set the `accept_any` flag, which will cause the grader to literally accept anything that is entered into the textbox.

```pycon
>>> grader = StringGrader(
...     answers={'expect': '', 'grade_decimal': 1, 'msg': 'Your answer has been recorded.'},
...     accept_any=True
... )
>>> grader(None, 'cat') == {'grade_decimal': 1, 'msg': 'Your answer has been recorded.', 'ok': True}
True
>>> grader(None, 'dog') == {'grade_decimal': 1, 'msg': 'Your answer has been recorded.', 'ok': True}
True
>>> grader(None, '') == {'grade_decimal': 1, 'msg': 'Your answer has been recorded.', 'ok': True}
True

```

Note that this will even accept a blank (empty) response. To reject empty responses, you can instead use the `accept_nonempty` flag, which requires at least one character to be submitted (after input cleaning).

```pycon
>>> grader = StringGrader(
...     answers={'expect': '', 'grade_decimal': 1, 'msg': 'Your answer has been recorded.'},
...     accept_nonempty=True,
...     explain_minimums=None
... )
>>> grader(None, 'dog') == {'grade_decimal': 1,
...                         'msg': 'Your answer has been recorded.',
...                         'ok': True}
True
>>> grader(None, '') == {'grade_decimal': 0, 'msg': '', 'ok': False}
True

```

Note that when either `accept_any` or `accept_nonempty` are set to True, you do not need to provide any answer to check against.

You may want students to have to write a certain amount of characters or words in order to get credit. Two flags are available to facilitate this: `min_length` and `min_words`, which set a minimum number of characters and words to be awarded credit, respectively (both default to zero). You can use both of these options together if desired.

```pycon
>>> grader = StringGrader(
...     answers={'expect': '', 'grade_decimal': 1, 'msg': 'Your answer has been recorded.'},
...     accept_any=True,
...     min_length=10,  # Require at least 10 characters (after cleaning input)
...     min_words=3,    # Require at least 3 words
...     explain_minimums='msg'
... )
>>> grader(None, 'This is a long answer') == {'grade_decimal': 1,
...                                           'msg': 'Your answer has been recorded.',
...                                           'ok': True}
True
>>> grader(None, 'too short') == {'grade_decimal': 0,
...                               'msg': 'Your response is too short (2/3 words)',
...                               'ok': False}
True
>>> grader(None, '  a  b  c  d  ') == {'grade_decimal': 0,
...                                    'msg': 'Your response is too short (7/10 characters)',
...                                    'ok': False}
True

```

Note that punctuation doesn't break a word for the purpose of word counting, so `isn't word-counting fun?` will only count as three words. If `accept_nonempty` and `min_length` are both used, the longer requirement is the one that is used.

When a student's answer is rejected because it doesn't meet the minimum requirements, there are three types of feedback that you can provide, controlled by the `explain_minimums` flag:

* The student receives an error message describing how many words/characters they have, compared to how many are required. This does not consume an attempt (`explain_minimums='err'`, default).
* The student is graded incorrect, but a message is provided describing how many words/characters they have, compared to how many are required. This consumes an attempt (`explain_minimums='msg'`).
* The student is graded incorrect, and no explanation is given. This consumes an attempt (`explain_minimums=None`).

The settings `min_length`, `min_words` and `explain_minimums` are all ignored if not using `accept_any` or `accept_nonempty`.


## Validating Input

Sometimes, you may want to validate student input against a pattern. This can be useful if the student response simply needs to follow a given pattern, or if you want to reject student responses that don't conform to the required format. Validation can be used both when comparing against an expected response, or when using `accept_any` (and variants).

Validation is performed by constructing a python regular expressions (regex) pattern, stored in the `validation_pattern` flag (if you are unfamiliar with regular expressions, there are many excellent tutorials available online to get you started!). After input cleaning, the student input is checked against the pattern for a match. If no match is found, the desired response is returned. Expected answers are also checked against the pattern; if a possible answer does not conform to the pattern, then a configuration error results.

When a response doesn't satisfy the given pattern, there are three types of feedback that you can provide, controlled by the `explain_validation` flag:

* The student receives an error message. This does not consume an attempt (`explain_validation='err'`, default).
* The student is graded incorrect, but receives a message. This consumes an attempt (`explain_validation='msg'`).
* The student is graded incorrect, and no explanation is given. This consumes an attempt (`explain_validation=None`).

In the first two cases, the message provided is given by the `invalid_msg` setting, which defaults to `Your input is not in the expected format`.

Here is an example of using a validation pattern to accept inputs that look like chemical formulae for organic molecules. Note that anything that matches the pattern will be graded correct.

```pycon
>>> grader = StringGrader(
...     validation_pattern=r'([CNOH](_[0-9])?)+',
...     explain_validation='msg',
...     invalid_msg='Write a chemical formula containing hydrogen, oxygen, carbon and/or nitrogen',
...     strip_all=True,   # Removes all spaces from the input
...     accept_any=True
... )
>>> grader(None, 'NH_3') == {'grade_decimal': 1,
...                          'msg': '',
...                          'ok': True}
True
>>> grader(None, 'KCl') == {'grade_decimal': 0,
...                          'msg': 'Write a chemical formula containing hydrogen, oxygen, carbon and/or nitrogen',
...                          'ok': False}
True

```

Below, we use validation to ensure that the student input matches the desired format before comparing to the answer, and give the student an error message if their input doesn't match the specification.

```pycon
>>> grader = StringGrader(
...     answers='(1)(2)',
...     validation_pattern=r'\([0-9]\)\([0-9]\)',
...     explain_validation='err',
...     strip_all=True   # Removes all spaces from the input
... )
>>> grader(None, '(1)(2)') == {'grade_decimal': 1, 'msg': '', 'ok': True}
True
>>> grader(None, '(2)(1)') == {'grade_decimal': 0, 'msg': '', 'ok': False}
True
>>> try:
...     grader(None, '(a)(2)')
... except InvalidInput as error:
...     print(error)
Your input is not in the expected format
>>> try:
...     grader(None, '[1)(2)')
... except InvalidInput as error:
...     print(error)
Your input is not in the expected format

```


## Option Listing

Here is the full list of options specific to a `StringGrader`.
```python
grader = SingleListGrader(
    case_sensitive=bool,  # default True
    strip=bool,  # default True
    clean_spaces=bool,  # default True
    strip_all=bool,  # default False
    accept_any=bool,  # default False
    accept_nonempty=bool,  # default False
    min_words=int >= 0,  # default 0
    min_length=int >= 0,  # default 0
    explain_minimums=('err', 'msg', None),  # default 'err'
    validation_pattern=str,  # default None
    explain_validation=('err', 'msg', None),  # default 'err'
    invalid_msg=str,  # default 'Your input is not in the expected format'
)
```
