# Frequently Asked Questions (FAQs)

- Does the grading library work with multiple choice/checkbox/dropdown lists?

Unfortunately, no. Those problem types cannot be used in a `customresponse` problem, so we can't grade them with a python grader.

- Does the grader work with Python 2 or Python 3?

The library only supports Python 3, as support for Python 2 was dropped in Version 3. It is tested against the numpy, scipy and pyparsing versions in the Open edX Ulmo (Python 3.11) and Verawood (Python 3.12) codejail sandboxes and edx-platform master (Python 3.12), and against the latest releases of those packages on Python 3.13 through 3.15. For more information, see the [CHANGELOG](https://mitodl.github.io/mitx-grading-library/changelog/). If you need to use older versions of this package, you can download `python_lib.zip` from the Assets section of the [GitHub releases](https://github.com/mitodl/mitx-grading-library/releases).
