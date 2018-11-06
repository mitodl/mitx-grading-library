# edX Syntax

To create an edX problem using the MITx Grading Library, you need to create a "Blank Advanced Problem", which allows you to construct the problem description via XML. The library is used in `customresponse` problems, which means that there are two parts to setting up the problem: defining the input that the student sees, and defining the grader that will grade the result. Here is an example.

```XML
<problem>

<!-- Define the grader -->
<script type="loncapa/python">
from mitxgraders import *
grader = FormulaGrader(variables=["x"])
</script>

  <!-- Ask the question -->
  <p>Enter the derivative of \(x^2\).</p>

  <!-- Define the problem -->
  <customresponse cfn="grader" answer="2*x">
    <textline math="true" />
  </customresponse>

  <!-- Ask another question -->
  <p>Enter the derivative of \(5x^2\).</p>

  <!-- Define the problem. Note that the grader is reused -->
  <customresponse cfn="grader" answer="10*x">
    <textline math="true" />
  </customresponse>

</problem>
```

Note that the `customresponse` tag contains the answer that is passed to the grader. You can also use `expect="2*x"` instead of `answer="2*x"`; edX treats these parameters indistinguishably (although we strongly suggest not using both!). Also note that a grader can be reused if desired.

If you provide an `answers` key to the grader, it will ignore whatever is specified in the `customresponse` tag. Here is an example.

```XML
<problem>

<script type="loncapa/python">
from mitxgraders import *
grader = FormulaGrader(
    answers={'expect': '2*x', 'ok': True, 'grade_decimal': 1, 'msg': 'Good job!'},
    variables=['x']
)
</script>

  <p>Enter the derivative of \(x^2\).</p>

  <customresponse cfn="grader" answer="2*x">
    <textline math="true" />
  </customresponse>

</problem>
```

Even though the `answers` key is provided to the grader explicitly, the `answer` parameter in the `customresponse` tag is still important, as it is what the students see when they click on "Show Answer".

If you are using multiple inputs (such as when using a `ListGrader`), you must provide the `answers` key to the grader explicitly, as the `expect` or `answer` parameters in the `customresponse` tag are ignored. When using multiple inputs, it's recommended to provide a `correct_answer` parameter on the `textline` tags, which is what is used to show students the correct answer. Here is an example.

```XML
<problem>
<script type="loncapa/python">
from mitxgraders import *
grader = FormulaGrader(
    answers=['x-2', 'x+2'],
    ordered=False,
    subgraders=FormulaGrader(variables=['x'])
)
</script>

  <p>What are the linear factors of \((x^2 - 4)\)?</p>

  <!-- Note there is no 'expect' or 'answer' parameter in the customresponse tag -->
  <customresponse cfn="grader">
    <!-- correct_answer is shown to student when they press [Show Answer].
         Its value is not used for grading purposes -->
    <textline math="true" correct_answer="x - 2" />
    <textline math="true" correct_answer="x + 2" />
  </customresponse>

</problem>
```

Note that the `correct_answer` parameters are never sent to the grader, which is why you must provide them independently.

Because the `cfn` parameter of the `customresponse` tag is executed as python code, it is possible to skip the definition of the grader altogether, as the following example shows.

```XML
<problem>

<!-- Make sure to remember to import the library! -->
<script type="loncapa/python">
from mitxgraders import *
</script>

  <p>Enter the derivative of \(x^2\).</p>

  <customresponse cfn="FormulaGrader(variables=['x'])" answer="2*x">
    <textline math="true" />
  </customresponse>

</problem>
```

One must be careful to make sure that quotation marks are properly escaped if using this method.
