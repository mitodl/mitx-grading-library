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
* A string/number: 'cat'
* A dictionary: {'expect':'zebra', 'grade_decimal':1, 'msg':'Yay!'}
* A list of strings/numbers: ['cat', 'lion', 'tiger']
* A list of dictionaries:
```python
[
    {'expect':'zebra', 'grade_decimal':1, 'msg':'Yay!'},
    {'expect':'seahorse', 'grade_decimal':0.5, 'msg':'Almost!'},
    {'expect':'unicorn', 'grade_decimal':0, 'msg':'Really?'},
]
```

Internally, the ItemGrader base class converts the answers entry into a list of dictionaries, and then asks the specific grading class to grade the response against each possible answer.


List Graders
------------

When there are multiple items to be graded, a list grader handles the grading. List graders work by farming out individual items to item graders, and then collecting the results and working out the optimal farming scheme. There are four possible keys for a list grader's grading scheme.

```python
grader = ListGrader({
    'answers': answerslist,
    'item_grader': graders,
    'ordered': True/False,
    'pairing': pairinglist
})
```

Lists of input can be read from multiple student inputs, or a single student input with appropriate delimiter.


### Basic usage

Each input is checked against the corresponding answer, using the item grader MyGrader.

```python
grader = ListGrader({
    'answers': ['cat', 'dog'],
    'item_grader': MyGrader()
})
```

Each element of answers is set as an answer that is passed as the answers key into the item grader. In this case, the item grader just sees a single string as an input. You can do more complicated things though, like the following.

```python
answer1 = [
        {'expect':'zebra', 'grade_decimal':1},
        {'expect':'horse', 'grade_decimal':0.45},
        {'expect':'unicorn', 'grade_decimal':0, 'msg': 'Unicorn? Really?'}
    ]
answer2 = [
        {'expect':'cat', 'grade_decimal':1},
        {'expect':'feline', 'grade_decimal':0.5}
    ]
grader = ListGrader({
    'answers': [answer1, answer2],
    'item_grader': MyGrader()
})
```


### Unordered entry

By setting ordered to false, students can enter "cat", "dog" or "dog", "cat" for this problem. The list grader finds the optimal assignment of student entries to answers.

```python
grader = ListGrader({
    'answers': ['cat', 'dog'],
    'item_grader': MyGrader(),
    'ordered': False
})
```


### Multiple graders

If you have inhomogeneous inputs, you can grade them using different graders. Simply give a list of item graders, and the data will be passed into the graders in that order. Note that the length of answers must be the same as the number of graders in this case. Further note that you cannot set ordered to False when using a list of graders.

```python
grader = ListGrader({
    'answers': ['cat', 'x^2+1'],
    'item_grader': [MyGrader1(), MyGrader2()]
})
```

Multiple graders are not allowed for problems where the student has a single inputbox.


### Paired inputs

Sometimes you will have inputs that needed to be graded together. A simple example would be to ask for the name and number of each animal in a picture. Each name/number pair needs to be graded together. Here is an example of such a question.

```python
grader = ListGrader({
    'answers': [
        ['cat', 1],
        ['dog', 2],
        ['tiger', 3]
    ],
    'item_grader': ListGrader({
        'item_grader': [StringGrader(), NumericalGrader()]
    }),
    'ordered': False,
    'pairing': [1, 1, 2, 2, 3, 3]
})
```

The pairing key specifies which group each entry belongs to. In this case, answers 1 and 2 will be combined into a list, as will 3 and 4, and 5 and 6. The item grader (itself a list grader) will then receive a list of two answers, and each of the items in the answers. Because this is an unordered list, the list grader will try every possible combination and choose the optimal one.

In this case, the next level of grader is receiving multiple inputs, and so itself needs to be a ListGrader. As ordered is false, this same grader will be used to grade everything. We'll see an example below where this is not the case. When initializing this ListGrader, the answers key does not need to be specified, as the answers will be passed in automatically. Only the item_grader key needs to be specified.

You cannot use a paired grading scheme with a single inputbox problem.

With ordered equal to false, the pairings must each have the same number of elements.

Here is another example. In this case, we have ordered entry, so we can specify a list of item graders. We have three items in the first pairing and one item in the second, so we use a ListGrader for the first pairing, and a MyGrader for the second. Note that the first entry in answers is a list that is passed directly into the ListGrader, while the second entry is just a string. This second-level ListGrader is now unordered.

```python
grader = ListGrader({
    'answers': [
        ['bat', 'ghost', 'pumpkin'],
        'Halloween'
    ],
    'item_grader': [
        ListGrader({
            'item_grader': StringGrader(),
            'ordered': False
        }),
        StringGrader()
    ]
    'pairing': [1, 1, 1, 2]
})
```

Our last example is for a math class, where we have a matrix that has two eigenvalues, and each eigenvalue has a corresponding eigenvector. We start by pairing the eigenvalue and eigenvector boxes together, and then grade the pairs in an unordered fashion.

```python
grader = ListGrader({
    'answers': [
        [1, [1, 0]],
        [-1, [0, 1]],
    ],
    'item_grader': ListGrader({
        'item_grader': [
            NumericalGrader(),
            ListGrader({
                'item_grader': NumericalGrader()
            })
        ]
    })
    'ordered': False,
    'pairing': [1, 1, 2, 2]
})
```

This example needs either 6 input boxes (one for each eigenvalue, three for each eigenvector), or 4 input boxes (one for each eigenvalue, and then a single input box for the eigenvector). If you want a challenge exercise, modify this to allow the eigenvectors to be either the ones presented here, or their negative!
