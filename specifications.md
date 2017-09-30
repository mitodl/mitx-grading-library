Grading
=======

Item Graders
------------

When an individual item needs to be graded, it is graded by an item grader. All item graders work by specifying answers and their corresponding points/messages, as well as an optional message for wrong answers.

```python
grader = MyGrader({
    'answers': 'cat',
    'wrong_msg': 'Try again!'
})
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

Internally, the ItemGrader base class converts the answers entry into a tuple of dictionaries, and then asks the specific grading class to grade the response against each possible answer.


List Graders
------------

When there are multiple items to be graded, a list grader handles the grading. List graders work by farming out individual items to subgraders, and then collecting the results and working out the optimal farming scheme. Here are the possible keys for a list grader's grading scheme:

```python
grader = ListGrader({
    'answers': answerslist,
    'subgrader': grader,
    'ordered': True/False (default False),
    'grouping': groupinglist,
    'delimiter': delimiter (default ','),
    'length_error': True/False (default True)
})
```

Lists of input can be read from multiple student inputs, or a single student input with appropriate delimiter.


### Basic usage

Each input is checked against the corresponding answer, using the grader MyGrader.

```python
grader = ListGrader({
    'answers': ['cat', 'dog'],
    'subgrader': MyGrader()
})
```

Each element of answers is set as an answer that is passed as the answers key into the subgrader. This could be set up as two input boxes that the student types in, or as a single input box that the student should enter 'cat, dog' in. Either will work. If you wish to use a different delimiter for a single input box, then use something like the following.

```python
grader = ListGrader({
    'answers': ['cat', 'dog'],
    'subgrader': MyGrader(),
    'delimiter': ';'
})
```

In this case, the student should enter 'cat; dog' as the answer if presented with a single input box. The delimiter key is ignored when multiple input boxes are used.

If students enter their answer in a single input box, then if they provide the wrong number of entries, the grader can either return an error, or prorate the grade. If you ask for a 3D vector in a box, then it makes sense to return an error. If you want the prime numbers beneath 10, then it makes sense to just give partial credit. The following will give partial credit for answers of "cat" and "cat,dog,fish".

```python
grader = ListGrader({
    'answers': ['cat', 'dog'],
    'subgrader': MyGrader(),
    'length_error': False
})
```

In the above cases, the item grader just sees single strings as the answer. You can do more complicated things though, like the following.

```python
answer1 = (
        {'expect':'zebra', 'grade_decimal':1},
        {'expect':'horse', 'grade_decimal':0.45},
        {'expect':'unicorn', 'grade_decimal':0, 'msg': 'Unicorn? Really?'}
    )
answer2 = (
        {'expect':'cat', 'grade_decimal':1},
        {'expect':'feline', 'grade_decimal':0.5}
    )
grader = ListGrader({
    'answers': [answer1, answer2],
    'subgrader': MyGrader()
})
```


### Unordered entry

By setting ordered to false, students can enter "cat", "dog" or "dog", "cat" for this problem. The list grader finds the optimal assignment of student entries to answers.

```python
grader = ListGrader({
    'answers': ['cat', 'dog'],
    'subgrader': MyGrader(),
    'ordered': False
})
```


### Multiple graders

If you have inhomogeneous inputs, you can grade them using different graders. Simply give a list of subgraders, and the data will be passed into the graders in that order. Note that the length of answers must be the same as the number of subgraders in this case. Further note that you cannot set ordered to False when using a list of subgraders.

```python
grader = ListGrader({
    'answers': ['cat', 'x^2+1'],
    'subgrader': [MyGrader1(), MyGrader2()]
})
```

Multiple graders are not allowed for problems where the student has a single inputbox, as the number of inputs a student gives is variable.


### Nested list graders

Some questions will require nested list graders. As an example, consider two input boxes, where the first should be a comma-separated list of even numbers beneath 5, and the second should be a comma-separated list of odd numbers beneath 5. The order of the boxes is important, but within each box, the order becomes unimportant. Here's how you can encode this type of problem.

```python
grader = ListGrader({
    'answers': [
        ['2', '4'],
        ['1', '3']
    ],
    'subgrader': ListGrader({
        'subgrader': NumericalGrader(),
        'ordered': False
    })
})
```

The nested list grader will be used to grade the first input box against an unordered answer of 2 and 4, and then the second input box against an unordered answer of 1 and 3.


### Grouped inputs

Sometimes you will have inputs that needed to be graded together. A simple example would be to ask for the name and number of each animal in a picture. Each name/number group needs to be graded together. Here is an example of such a question.

```python
grader = ListGrader({
    'answers': [
        ['cat', 1],
        ['dog', 2],
        ['tiger', 3]
    ],
    'subgrader': ListGrader({
        'subgrader': [StringGrader(), NumericalGrader()]
    }),
    'ordered': False,
    'grouping': [1, 1, 2, 2, 3, 3]
})
```

The grouping key specifies which group each entry belongs to. In this case, answers 1 and 2 will be combined into a list, as will 3 and 4, and 5 and 6. The item grader (itself a list grader) will then receive a list of two answers, and each of the items in the answers. Because this is an unordered list, the list grader will try every possible combination and choose the optimal one.

In this case, the next level of grader is receiving multiple inputs, and so itself needs to be a ListGrader. As ordered is false, this same grader will be used to grade everything. We'll see an example below where this is not the case. When initializing this ListGrader, the answers key does not need to be specified, as the answers will be passed in automatically. Only the subgrader key needs to be specified.

You cannot use a grouped grading scheme with a single inputbox problem.

With ordered equal to false, the groupings must each have the same number of elements.

The values used in the grouping list can be integers or strings.

Here is another example. In this case, we have ordered entry, so we can specify a list of item graders. We have three items in the first grouping and one item in the second, so we use a ListGrader for the first grouping, and a MyGrader for the second. Note that the first entry in answers is a list that is passed directly into the ListGrader, while the second entry is just a string. This second-level ListGrader is now unordered.

```python
grader = ListGrader({
    'answers': [
        ['bat', 'ghost', 'pumpkin'],
        'Halloween'
    ],
    'subgrader': [
        ListGrader({
            'subgrader': StringGrader(),
            'ordered': False
        }),
        StringGrader()
    ]
    'grouping': [1, 1, 1, 2]
})
```

Our last pair of examples are for a math class, where we have a matrix that has two eigenvalues, and each eigenvalue has a corresponding eigenvector. We start by grouping the eigenvalue and eigenvector boxes together, and then grade the groups in an unordered fashion. The eigenvectors are normalized, but have a sign ambiguity. A tuple contains both possible answers, and the grader will accept either of them.

```python
grader = ListGrader({
    'answers': [
        [1, ([1, 0], [-1, 0])],
        [-1, ([0, 1], [0, -1])],
    ],
    'subgrader': ListGrader({
        'subgrader': [
            NumericalGrader(),
            ListGrader({
                'subgrader': NumericalGrader()
            })
        ]
    })
    'ordered': False,
    'grouping': [1, 1, 2, 2]
})
```

Because the grouping has exactly 4 items in it, this example requires 4 input boxes: eigenvalue1, eigenvector1 (single input box list), eigenvalue2, eigenvector2 (single input box list).

It is possible to specify a grouping on a nested ListGrader. The outer ListGrader must also have a grouping specified if doing so. Here is the same grader as above, where instead of taking the eigenvectors in a single input box list, there are three boxes to input the vector components.

```python
grader = ListGrader({
    'answers': [
        [1, ([1, 0], [-1, 0])],
        [-1, ([0, 1], [0, -1])],
    ],
    'subgrader': ListGrader({
        'subgrader': [
            NumericalGrader(),
            ListGrader({
                'subgrader': NumericalGrader()
            })
        ],
        'grouping': [1, 2, 2, 2]
    })
    'ordered': False,
    'grouping': [1, 1, 1, 1, 2, 2, 2, 2]
})
```
