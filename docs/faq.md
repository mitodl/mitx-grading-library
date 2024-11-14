# Frequently Asked Questions (FAQs)

- Does the grading library work with multiple choice/checkbox/dropdown lists?

Unfortunately, no. Those problem types cannot be used in a `customresponse` problem, so we can't grade them with a python grader.

- Does the grader work with python 2 or python 3?

It works with both! Older versions of edX ran python graders in python 2.7; newer versions use python 3.8. The library works seamlessly with both. No changes to any code are required to switch between versions. Some functionality requires python 3.5 however.
