"""
basic_demo.py

A simple demo of using the grading library
"""
import pprint
from graders import ListGrader, StringGrader

pp = pprint.PrettyPrinter(indent=4)

list_grader = ListGrader(
    answers=['cat', 'dog', 'unicorn'],
    subgrader=StringGrader(),
    length_error=False
)

answers1 = ['cat', 'fish', 'dog']
demo1 = list_grader(None, answers1)
pp.pprint(demo1)

answers2 = "cat, fish, dog, zebra"
demo2 = list_grader(None, answers2)
pp.pprint(demo2)
