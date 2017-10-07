"""
Development testing of the grading library
"""
import pprint
from graders import *

pp = pprint.PrettyPrinter(indent=4)

list_grader = SingleListGrader(
    answers=(['cat', 'dog'], ['goat', 'vole']),
    subgrader=StringGrader(),
    length_error=False,
    ordered=False
)

answers = "cat, vole"
demo = list_grader(None, answers)
pp.pprint(demo)
