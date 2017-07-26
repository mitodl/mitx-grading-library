<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [MITx Graders](#mitx-graders)
- [Installation](#installation)
- [Documentation](#documentation)
  - [FormulaGrader](#formulagrader)
    - [Usage](#usage)
    - [Configuration Dictionary Keys](#configuration-dictionary-keys)
  - [ListGrader](#listgrader)
    - [How learners enter lists in customresponse](#how-learners-enter-lists-in-customresponse)
    - [Basic Usage](#basic-usage)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# MITx Graders

A library of graders for EdX Custom Response problems.

# Installation
  
  **Requirements:** An installation of Python 2.7 (since this is what EdX uses). 
  
  To install:
  
  0. (Optional): Create and activate a new python virtual environment called `graders`. *On MacOS, Anaconda Python is convenient for this because it makes managing different versions of Python (e.g. 2.7 or 3.6) easy. See [Create a separate environment](https://conda.io/docs/using/envs.html#create-a-separate-environment) in the Anaconda docs.*
  1. Clone this repository and `cd` into it.
  2. Run `pip install -r requirements.txt` to install the requirements specified in `requirements.txt`.
  3. Run `pytest` to check that tests are passing.
  
# Documentation
Documentation is a work in progress. Currently just some formatted docstrings.


## FormulaGrader
Grades mathematical expressions.
    
Similar to EdX formularesponse but more flexible. Allows author to specify functions in addition to variables.

### Usage

Grade a formula containing variables and functions:
```python
>>> grader = FormulaGrader({
...     'answers':['a*b + f(c-b) + f(g(a))'],
...     'variables':['a', 'b','c'],
...     'functions':['f', 'g']
... })
>>> theinput0 = 'f(g(a)) + a*b + f(-b+c)'
>>> grader.cfn(None, theinput0)['ok']
True
>>> theinput1 = 'f(g(b)) + 2*a*b + f(b-c)'
>>> grader.cfn(None, theinput1)['ok']
False
```

The learner's input is compared to expected answer using numerical evaluations. By default, 5 evaluations are used with variables sampled on the interval [1,3]. The defaults can be overidden:

```python
>>> grader = FormulaGrader({
...     'answers': ['b^2 - f(g(a))/4'],
...     'variables': ['a', 'b'],
...     'functions': ['f', 'g'],
...     'samples': 3,
...     'sample_from': {
...         'a': [-4,1]
...     },
...     'tolerance': 0.1
... })
>>> theinput = "b*b - 0.25*f(g(a))"
>>> grader.cfn(None, theinput)['ok']
True
```
You can also provide specific values to use for any variable or function:
```python
>>> def square(x):
...     return x**2
>>> grader = FormulaGrader({
...     'answers': ['4*f(a)+b'],
...     'variables': ['a','b'],
...     'functions': ['f'],
...     'sample_from': {
...         'f': UniqueValue(square)
...     }
... })
>>> theinput = 'f(2*a)+b'               # f(2*a) = 4*f(a) for f = sq uare
>>> grader.cfn(None, theinput)['ok']
True
```
Grade complex-valued expressions:
>>> grader = FormulaGrader({
...     'answers': ['abs(z)^2'],
...     'variables': ['z'],
...     'sample_from': {
...         'z': ComplexRectangle()
...     }
... })
>>> theinput = 're(z)^2+im(z)^2'
>>> grader.cfn(None, theinput)['ok']
True

### Configuration Dictionary Keys

 - answers (list): answers, each specified as a string or dictionary.
 - variables (list of str): variable names, default `[]`
 - functions (list of str): function names, default `[]`
 - samples (int): Positive number of samples to use, default `5`
 - sample_from: A dictionary mapping synbol (variable or function name) to        sampling sets. Default sampling sets are:
      for variables, `RealInterval([1,3])`
      for functions,` NiceFunctions({dims=[1,1]})`
 - tolerance (int or PercentageString): A positive tolerance with which to compare numerical evaluations. Default `'0.1%'`
 - case_sensitive (bool): whether symbol names are case senstive. Default `True`
 - failable_evals (int): The nonnegative maximum number of evaluation comparisons that can fail with grader still passing. Default `0`
 
## ListGrader
Grades Lists of items according to a specific ItemGrader, unordered by default.

ListGrader can be used to grade a list of answers according to the  supplied ItemGrader. Works with either multi-input customresponse or single-input customresponse.

### How learners enter lists in customresponse
**Multi-input customresponse:**
```xml
<customresmse cfn="grader.cfn">
    <textline/> <!-- learner enters cat -->
    <textline/> <!-- learner enters dog -->
    <textline/> <!-- learner leaves blank -->
</customresmse>
```
Notes:

  - grader.cfn receives a list: ['cat', 'dog', None]
  - list will always contain exactly as many items as input tags
    
**Single-input customresponse:**
```xml
<customresmse cfn="grader.cfn">
   <textline/> <!-- learner enters 'cat, dog, fish, rabbit' -->
</customresmse>
```
Notes:

 - learner is responsible for entering item separator (here: ',')
 - grader.cfn receives a string: 'cat, dog, fish, rabbit'
 - learner might enter fewer or more items than author expects
    
### Basic Usage
For more advanced usage, see exmaples in `graders/tests/test_list_grader.py`.

Grade a list of strings (multi-input)
```python
>>> grader = ListGrader({
...     'answers_list':[['cat'], ['dog'], ['fish']],
...     'item_grader': StringGrader()
... })
>>> result = grader.cfn(None, ['fish', 'cat', 'moose'])
>>> expected = {'input_list':[
...     {'ok': True, 'grade_decimal':1, 'msg':''},
...     {'ok': True, 'grade_decimal':1, 'msg':''},
...     {'ok': False, 'grade_decimal':0, 'msg':''}
... ], 'overall_message':''}
>>> result == expected
True
```

Grade a string of comma-separated items through the same API:
```python
>>> result = grader.cfn(None, "cat, fish, moose")
>>> expected = {'ok':'partial', 'grade_decimal':2/3, 'msg': '' }
>>> result == expected
True
```

Extra items reduce score:
```python
>>> result = grader.cfn(None, "cat, fish, moose, rabbit")
>>> expected = {'ok':'partial', 'grade_decimal':1/3, 'msg': '' }
>>> result == expected
True
```
but not below zero:
```
>>> result = grader.cfn(None, "cat, fish, moose, rabbit, bear, lion")
>>> expected = {'ok':False, 'grade_decimal':0, 'msg': '' }
>>> result == expected
True
```
Optionally, make order matter:
```python
>>> ordered_grader = ListGrader({
...     'ordered': True,
...     'answers_list':[['cat'], ['dog'], ['fish']],
...     'item_grader': StringGrader()
... })
>>> result = ordered_grader.cfn(None, "cat, fish, moose")
>>> expected = {'ok':'partial', 'grade_decimal':1/3, 'msg': '' }
>>> result == expected
True
```
Optionally, change the separator for single-input:
```python
>>> semicolon_grader = ListGrader({
...     'separator': ';',
...     'answers_list':[['cat'], ['dog'], ['fish']],
...     'item_grader': StringGrader()
... })
>>> result = semicolon_grader.cfn(None, "cat; fish; moose")
>>> expected = {'ok':'partial', 'grade_decimal':2/3, 'msg': '' }
>>> result == expected
True
```