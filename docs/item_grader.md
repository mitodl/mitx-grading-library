ItemGrader
==========

When an individual input needs to be graded, it is graded by an item grader. All item graders work by specifying answers and their corresponding points/messages, as well as an optional message for wrong answers. In these examples, we use `StringGrader` as an example of how to use a generic ItemGrader. You cannot use a generic ItemGrader by itself.

```python
grader = StringGrader(
    answers='cat',
    wrong_msg='Try again!'
)
```

The answers entry may be:
* A string: 'cat'
* A dictionary: {'expect':'zebra', 'grade_decimal':1, 'msg':'Yay!'}
* A tuple of strings: ('cat', 'lion', 'tiger')
* A tuple of dictionaries:
```python
(
    {'expect':'zebra', 'grade_decimal':1, 'msg':'Yay!'},
    {'expect':'seahorse', 'grade_decimal':0.5, 'msg':'Almost!'},
    {'expect':'unicorn', 'grade_decimal':0, 'msg':'Really?'},
)
```
Note that even for numerical input, the answers must be input as strings.

Internally, the ItemGrader converts the answers entry into a tuple of dictionaries. When grading, it asks the specific grading class to grade the response against each possible answer, and selects the best outcome for the student.

The wrong_msg is only displayed if the score is zero, and there are no other messages.

You may also specify the configuration as a configuration dictionary. This may be helpful if using the same configuration for multiple problems. As an example, the above configuration can be constructed as follows.

```python
config = {
    'answers': 'cat',
    'wrong_msg': 'Try again!'
}
grader = StringGrader(config)
```

Such configuration dictionaries also work with SingleListGrader and ListGrader.


- [Home](README.md)
