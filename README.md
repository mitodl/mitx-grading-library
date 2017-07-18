# MITx Graders

A library of graders for EdX Custom Response problems.

# Installation
  
  **Requirements:** An installation of Python 2.7 (since this is what EdX uses). 
  
  To install:
  
  0. (Optional): Create and activate a new python virtual environment called `graders`. *On MacOS, Anaconda Python is convenient for this because it makes managing different versions of Python (e.g. 2.7 or 3.6) easy. See [Create a separate environment](https://conda.io/docs/using/envs.html#create-a-separate-environment) in the Anaconda docs.*
  1. Clone this repository and `cd` into it.
  2. Run `pip install -r requirements.txt` to install the requirements specified in `requirements.txt`.
  3. Run `pytest` to check that tests are passing.
  
# Grading Lists of Items
A common use of customresponse problems is to grade lists of items for individual correctness. The type of items might vary from list to list:

  - a list of simple strings `['cat', 'dog', 'fish']`
  - a list of numbers `[10,-3.5, 40]`
  - a list of mathematical expressions `[a*b^2, c-d^3, (x+y)^2]`
  - a list of intervals on the real line `[(-4,5), (10,20], [30,∞)]`
  - a list of chemical formulas
  
But generally the type of item does not vary within a list.

The `graders` module provides a `ListGrader` class to help grading such lists. The general usage pattern is:

```xml
<script type="text/python">
from graders import ListGrader, StringGrader
grader = ListGrader({
  'expect': ['cat', 'fish', 'horse'] # A list of items to expect
  'item_grader': StringGrader({}) # A grader for grading individual items
  'ordered':False # False is the default
})
</script>
<customresponse cfn="grader.cfn"></customresponse>
```
Above, `item_grader` is the grader responsible for grading individual list items.
  
Comments:

 1. `ListGrader` is fully(?) implemented, but the only currently implemeneted ItemGrader is a `StringGrader`, which Chris has been using as a toy grader.
 2. The `ListGrader`'s `cfn` can accept two forms of input:
   - A list of strings with same length as `expect` (for when `<customresponse>` has multiple input fields)
   - A comma-separated list of items with varying length (for when customresponse has one input field)
 3. By default, `ListGrader` does not care about the list order. In this case, assigning student asnwers to expected answers amounts to solving an [Assignment Problem](https://en.wikipedia.org/wiki/Assignment_problem). 
     - To find the optimal assignment of student answers to expected answers, we use [munkres.py](https://github.com/bmc/munkres)
     - Partial credit is given in proportion to the number of correct answers minus the number of incorrect answers.
  4. `expect` can be either a simple list of expected answers, or a nested list of dictionaries containing feedback messages and partial credit. For an example, see `[test_list_grader](graders/tests/test_list_grader.py)`
 

  