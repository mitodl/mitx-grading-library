from graders import *
import pprint

pp = pprint.PrettyPrinter(indent=4)

list_grader = ListGrader({
    'answers': ['cat', 'dog', 'unicorn'],
<<<<<<< 5da9d9f08bcb8520478fef6defe9e9b048c91dde
    'item_grader': StringGrader()
=======
    'subgrader': StringGrader()
>>>>>>> Changing item_grader to subgrader in ListGrader
})

answers1 = ['cat', 'fish', 'dog']
demo1 = list_grader(None, answers1)
pp.pprint(demo1)

answers2 = "cat, fish, dog, zebra"
demo2 = list_grader(None, answers2)
pp.pprint(demo2)
