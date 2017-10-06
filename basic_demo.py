"""
basic_demo.py

A simple demo of using the grading library
"""
import pprint
from graders import *

pp = pprint.PrettyPrinter(indent=4)

list_grader = SingleListGrader(
    answers=['cat', 'dog', 'unicorn'],
    subgrader=StringGrader()
)

answers = "unicorn, cat, dog, fish"
demo = list_grader(None, answers)
pp.pprint(demo)
