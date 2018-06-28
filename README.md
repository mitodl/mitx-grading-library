# MITx Grading Library

[![Build Status](https://travis-ci.org/mitodl/mitx-grading-library.svg?branch=master)](https://travis-ci.org/mitodl/mitx-grading-library)
[![Coverage Status](https://coveralls.io/repos/github/mitodl/mitx-grading-library/badge.svg?branch=master)](https://coveralls.io/github/mitodl/mitx-grading-library?branch=master)

A library of graders for edX Custom Response problems.

Version 1.0.4 ([changelog](changelog.md))

Copyright 2017 Jolyon Bloomfield and Chris Chudzicki

We thank the MIT Office of Digital Learning for their support.

**Table of Contents**

- [Demo Course](#demo-course)
- [Local Installation](#local-installation)
- [Usage in edX](#usage-in-edx)
- [Grader Documentation](#grader-documentation)


## Demo Course

A demonstration course for the MITx Grading Library can be viewed [here](https://edge.edx.org/courses/course-v1:MITx+grading-library+examples/). The source code for this course is contained in this repository.


## Local Installation

To install:

This is useful for testing configurations in python, rather than in edX. However, this is not necessary.

**Requirements:** An installation of Python 2.7 (since this is what edX uses).

0. (Optional) Create and activate a new python virtual environment.
1. Clone this repository and `cd` into it.
2. Run `pip install -r requirements.txt` to install the requirements specified in `requirements.txt`.
3. Run `pytest` to check that tests are passing.


## Usage in edX
Download [python_lib.zip](python_lib.zip) and place it in your static folder (XML workflow) or upload it as a file asset (Studio workflow). If you already have a python_lib.zip, you'll need to merge ours with yours and re-zip.

A custom response problem is defined using the `<customresponse>` tag. It needs to be supplied a check function (cfn), which must be a grader that you have defined in the problem. The mitxgraders library provides reusable check functions. The basic usage pattern is:

```xml
<script type="text/python" system_path="python_lib">
from mitxgraders import *
grader = GraderType(
    [configuration]
)
</script>

<customresponse cfn="grader">
    <textline/>
</customresponse>
```

The configuration depends on the type of grader that you're using. Note that all answers must be passed through the configuration. In particular, the `expect`  attribute on `<customresponse>` tag is ignored by our graders.

Here is an example where we use a StringGrader with answer `cat`.

```xml
<script type="text/python" system_path="python_lib">
from mitxgraders import *
grader = StringGrader(
    answers='cat'
)
</script>

<customresponse cfn="grader">
    <textline correct_answer="cat"/>
</customresponse>
```

The `expect` keyword is ignored by the grader, but is shown when students click on "Show Answer". This works only for single-input problems.

Here is another example where we use a ListGrader to grade two numbers in an unordered fashion.

```xml
<script type="text/python" system_path="python_lib">
from mitxgraders import *
grader = ListGrader(
    answers=['1', '2'],
    subgraders=FormulaGrader()
)
</script>

<customresponse cfn="grader">
    <textline correct_answer="1"/>
    <textline correct_answer="2"/>
</customresponse>
```

Here, the `correct_answer` entries are shown to students when they click "Show Answer". These values are not provided to the grader. The `correct_answer` attributes can also be used for single-input problems.


## Grader Documentation

[Extensive documentation](docs/README.md) has been compiled for the configuration of the different graders in the library.


## FAQs

* After installing a virtual environment and doing `pip install`, `pytest` returns a number of errors for `no module named error`.

We're not sure why this happens, but if you deactivate your virtual environment and reactivate it again, the issue seems to go away. We've only seen this happen on a completely fresh install.
