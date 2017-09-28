from graders import *
import pprint

pp = pprint.PrettyPrinter(indent=4)

list_grader = ListGrader({
    'answers': [['cat'], ['dog'], ['unicorn']],
    'item_grader': StringGrader()
})

answers1 = ['cat', 'fish', 'dog']
demo1 = list_grader(None, answers1)
pp.pprint(demo1)

answers2 = "cat, fish, dog, zebra"
demo2 = list_grader(None, answers2)
pp.pprint(demo2)
