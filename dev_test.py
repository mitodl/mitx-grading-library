"""
Development testing of the grading library
"""
import pprint
from graders import *

pp = pprint.PrettyPrinter(indent=4)

grader = StringGrader(
    answers=('cat', 'dog'),
    wrong_msg='nope!'
)

demo = grader(None, 'horse')
pp.pprint(demo)
