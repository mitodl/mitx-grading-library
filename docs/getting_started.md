# Getting Started

## Usage in edX
Download [python_lib.zip](python_lib.zip) and place it in your static folder (XML workflow) or upload it as a file asset (Studio workflow). If you already have a python_lib.zip, you'll need to merge ours with yours and re-zip. If you want to use our AsciiMath renderer definitions, place the [MjxPrep.js](MjxPrep.js) file in your static folder (XML) or upload the file to your course (Studio).

## MITxGraders: Reusable CustomResponse Check Functions

A custom response problem is defined using the `<customresponse>` tag. It needs to be supplied with a particular type of Python function that edX calls a check function (or "cfn"). The mitxgraders library provides reusable check functions. The basic usage pattern is:

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

The configuration depends on the type of grader that you're using. Note that all answers must be passed through the configuration. In particular, the `expect`  attribute on `<customresponse>` tag is ignored by our graders (but can be used to display an answer string to students).

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
