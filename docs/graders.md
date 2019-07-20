# Introduction to Graders

Graders are implemented as python classes. All grading classes are instantiated by calling them. Options can be provided using keyword arguments as
```python
grader = FakeGradingClass(option_1=value_1, option_2=value2)
# FakeGradingClass is not real! It's just a placeholder.
```
or with a configuration dictionary:
```python
config = {'option_1': value_1, 'option_2': value_2}
grader = FakeGradingClass(config)
```
Passing the configuration as a dictionary can be useful if you are using the same configuration for multiple problems. However, you cannot 'mix and match' these two options: if a configuration dictionary is supplied, any keyword arguments are ignored.

Most configuration options are specific to their grading classes. For example, `FormulaGrader` has a `variables` configuration key, but `NumericalGrader` does not.

A few configuration options are available to all grading classes.

## Debugging

Every grading class has a debug option. By default, `debug=False`. To receive debug information from a given grader, specify `debug=True`. Some graders will provide more debug information than others. Debug information can be used by authors to check to make sure that the graders are behaving as expected, but shouldn't be made available to students.

```python
grader = FakeGradingClass(debug=True)
```

## Validation

Every grading class has a `suppress_warnings` key.

The options passed to a grading class undergo extensive validation and graders will giver error messages if instantiated with invalid options.

A few error messages serve only as warnings. For example, if you attempt to configure a `FormulaGrader` with `pi` as a variable, you will receive a warning:

```pycon
>>> from mitxgraders import *
>>> try:
...     grader = FormulaGrader(variables=['pi'])
... except ConfigError as error:
...     print(error)
Warning: 'variables' contains entries 'pi' which will override default values. If you intend to override defaults, you may suppress this warning by adding 'suppress_warnings=True' to the grader configuration.

```

As the warning message says, if you really want to override the default value of `pi` (not recommended!) then you can suppress this warning by setting `suppress_warnings=True`.

```pycon
>>> from mitxgraders import *
>>> grader = FormulaGrader(variables=['pi'], suppress_warnings=True)

```

## Attempt-Based Partial Credit

It is possible to pass a student's attempt number to a grader by explicitly requesting that edX do so in a `customresponse` tag as follows.

```XML
<customresponse cfn="grader" expect="answer" cfn_extra_args="attempt">
```

Once this is done, you can enable attempt-based partial credit for your graders. The syntax is as follows.

```python
grader = FakeGradingClass(
    attempt_based_credit=(None | function),  # default None
    attempt_based_credit_msg=True  # default True
)
```

Attempt-based partial credit is turned on by specifying a function to convert an attempt number into an amount of credit. We provide three functions to do this, but you can of course write your own.

If a student's credit has been decreased from the maximum by attempt-based partial credit, the student can be provided with a message informing them of the maximum possible credit at that attempt number. This is controlled by the `attempt_based_credit_msg` setting. We recommend that this setting be left on, as it will likely lead to confusion otherwise.

When using nested graders, the `attempt_based_credit` setting need only be applied to the grader that is provided to edX in the `cfn` key.

Note that if attempt-based partial credit is turned on but the `cfn_extra_args="attempt"` entry is missing from the `customresponse` tag, an error message results.

Attempt-based partial credit can be set on a course-wide basis through the use of [plugins](plugins.md).


### ReciprocalCredit

This function simply awards credit based on the reciprocal of the attempt number. There are no options to set.

```pycon
>>> grader = StringGrader(attempt_based_credit=ReciprocalCredit())
>>> grader('cat', 'cat', attempt=1) == {'grade_decimal': 1, 'msg': '', 'ok': True}
True
>>> grader('cat', 'cat', attempt=2) == {'grade_decimal': 0.5, 'msg': 'Maximum credit for attempt #2 is 50%.', 'ok': 'partial'}
True
>>> grader('cat', 'cat', attempt=3) == {'grade_decimal': 0.3333, 'msg': 'Maximum credit for attempt #3 is 33.3%.', 'ok': 'partial'}
True
>>> grader('cat', 'cat', attempt=4) == {'grade_decimal': 0.25, 'msg': 'Maximum credit for attempt #4 is 25%.', 'ok': 'partial'}
True

```


### GeometricCredit

This function decreases the possible credit by a factor for each attempt, forming a geometric progression. You may choose the factor, which defaults to 0.5.

```pycon
>>> grader = StringGrader(attempt_based_credit=GeometricCredit(factor=0.5))
>>> grader('cat', 'cat', attempt=1) == {'grade_decimal': 1, 'msg': '', 'ok': True}
True
>>> grader('cat', 'cat', attempt=2) == {'grade_decimal': 0.5, 'msg': 'Maximum credit for attempt #2 is 50%.', 'ok': 'partial'}
True
>>> grader('cat', 'cat', attempt=3) == {'grade_decimal': 0.25, 'msg': 'Maximum credit for attempt #3 is 25%.', 'ok': 'partial'}
True
>>> grader('cat', 'cat', attempt=4) == {'grade_decimal': 0.125, 'msg': 'Maximum credit for attempt #4 is 12.5%.', 'ok': 'partial'}
True

```


### LinearCredit

This function allows the first few attempts to have maximum credit, then linearly decreases credit until a minimum threshold is reached.

- The maximum score begins to decrease after the attempt specified in `decrease_credit_after`. By default, all attempts after the first will have decreasing credit.

- The credit decreases linearly to `minimum_credit`.

- The number of attempts the credit decreases for is specified in `decrease_credit_steps`. So, using the defaults, attempts 1, 2, 3, 4, 5, and 6 are eligible for maximum credits of 1, 0.8, 0.6, 0.4, 0.2 and 0.2, respectively.

The following example demonstrates the default settings.

```pycon
>>> creditor = LinearCredit(
...     decrease_credit_after=1,  # First attempt receives full credit
...     minimum_credit=0.2,       # Minimum credit
...     decrease_credit_steps=4   # Number of attempts on the linear slope
... )
>>> creditor == LinearCredit()
True
>>> grader = StringGrader(attempt_based_credit=creditor)
>>> grader('cat', 'cat', attempt=1) == {'grade_decimal': 1, 'msg': '', 'ok': True}
True
>>> grader('cat', 'cat', attempt=2) == {'grade_decimal': 0.8, 'msg': 'Maximum credit for attempt #2 is 80%.', 'ok': 'partial'}
True
>>> grader('cat', 'cat', attempt=3) == {'grade_decimal': 0.6, 'msg': 'Maximum credit for attempt #3 is 60%.', 'ok': 'partial'}
True
>>> grader('cat', 'cat', attempt=4) == {'grade_decimal': 0.4, 'msg': 'Maximum credit for attempt #4 is 40%.', 'ok': 'partial'}
True
>>> grader('cat', 'cat', attempt=5) == {'grade_decimal': 0.2, 'msg': 'Maximum credit for attempt #5 is 20%.', 'ok': 'partial'}
True
>>> grader('cat', 'cat', attempt=6) == {'grade_decimal': 0.2, 'msg': 'Maximum credit for attempt #6 is 20%.', 'ok': 'partial'}
True

```


## Option Listing

Here is the full list of options specific to all graders.
```python
grader = AbstractGrader(
    debug=bool,  # default False
    wrong_msg=str,  # default ''
    attempt_based_credit=(None | function),  # default None
    attempt_based_credit_msg=bool,  # default True
)
```
