# MITx Grading Library

[![Build Status](https://travis-ci.org/mitodl/mitx-grading-library.svg?branch=master)](https://travis-ci.org/mitodl/mitx-grading-library) ![Coverage Status](https://codecov.io/gh/mitodl/mitx-grading-library/branch/master/graphs/badge.svg)

A library of graders for edX Custom Response problems.

Version 1.2.3 ([changelog](docs/changelog.md))

Copyright 2017-2019 Jolyon Bloomfield and Chris Chudzicki

Licensed under the [BSD-3 License](LICENSE).

We thank the MIT Office of Open Learning for their support.

**Table of Contents**

- [Demo Course](#demo-course)
- [Grader Documentation](#documentation-for-edx-course-authors)
- [Local Installation](#local-installation)
- [FAQ](#faq)


## Demo Course

A demonstration course for the MITx Grading Library can be viewed [here](https://edge.edx.org/courses/course-v1:MITx+grading-library+examples/). The source code for this course is contained in this repository [here](course/).


## Documentation for edX Course Authors
[Extensive documentation](https://mitodl.github.io/mitx-grading-library/) has been compiled for the configuration of the different graders in the library.


## Local Installation

This is not required but can be useful for testing configurations in python, rather than in edX.

To install:

**Requirements:** An installation of Python 2.7 (since this is what edX uses).

0. (Optional) Create and activate a new python virtual environment.
1. Clone this repository and `cd` into it.
2. Run `pip install -r requirements.txt` to install the requirements specified in `requirements.txt`.
3. Run `pytest` to check that tests are passing. (To invoke tests of just the documentation, you can run the following command: `python -m pytest --no-cov --disable-warnings docs/*`)


## FAQ

* What's this `voluptuous` thing?

[Voluptuous](https://github.com/alecthomas/voluptuous) is a library that handles configuration validation, while giving (hopefully) meaningful error messages. We use it to automate the checking of the configurations passed into the `mitxgraders` library. They need to be packaged together in the `python_lib.zip` file.
