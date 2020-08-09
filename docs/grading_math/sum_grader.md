# SumGrader

`SumGrader` is a specialized grading class used to grade the construction of summations. Students can input the limits on the sum, the variable of summation, and the summand (or some subset thereof), and will be graded correct if their construction is numerically equivalent to the instructor's construction. This method of grading allows for arbitrary variable redefinitions.

The grader numerically evaluates the student- and instructor-specified summations by evaluating the sums. Care must be taken to ensure rapid convergence with infinite summations, of which only finitely many terms can be numerically summed.


## XML Setup

We recommend copying the following XML to set up a problem using `SumGrader`:

```XML
<style>
  .xmodule_display.xmodule_ProblemBlock .problem .capa_inputtype.textline input {
    min-width: 0 !important;
  }
  .xmodule_display.xmodule_ProblemBlock div.problem section div span.MathJax {
    display: inline-block !important;
  }
  .xmodule_display.xmodule_ProblemBlock div.problem section div span.MathJax_Preview {
    display: inline-block !important;
  }
</style>

<span>
  <customresponse cfn="grader">
    <table>
      <col style="width:10%"/>
      <col style="width:90%"/>
      <tbody>
        <tr>
          <td colspan="2">
            <textline size="5" correct_answer="10"/>
          </td>
        </tr>
        <tr>
          <td>
            <p> \( \displaystyle \huge{ \sum }\)</p>
          </td>
          <td>
            <br/>
            <textline inline="1" size="10" correct_answer="n" math="1" preprocessorClassName="MJxPrep" preprocessorSrc="/static/MJxPrep.js"/>
          </td>
        </tr>
        <tr>
          <td colspan="2">
              <p style="display: inline;">[mathjaxinline]n = [/mathjaxinline] </p><textline size="5" correct_answer="0" inline="1"/>
          </td>
        </tr>
      </tbody>
    </table>
  </customresponse>
</span>
```

This sets up a summation where students can input the limits of summation and the summand (the variable of summation has been fixed to be `n` in this case).

Further examples of formatting summations are shown in the example course.


## Specifying the Input Format

The grader must be told which input is what, based on the order that the inputs appear in the XML. This is done through the `input_positions` dictionary. If not specified, it is assumed that the following positions are used:

```python
input_positions = {
    'lower': 1,
    'upper': 2,
    'summand': 3,
    'summation_variable': 4
}
```

This requires students to enter all four parameters in the indicated order.

If the author overrides the default `input_positions` value, any subset of the keys ('lower', 'upper', 'summand', 'summation_variable') may be specified. Key values should be

- continuous integers starting at 1, or
- (default) None, indicating that the parameter is not entered by student

For example,

```python
input_positions = {
    'lower': 1,
    'upper': 2,
    'summand': 3
}
```

indicates that the problem has 3 input boxes which represent the lower limit, upper limit, and summand in that order. The `summation_variable` is NOT entered by student and is instead given by the value specified by author in 'answers'.

Here is a sample grader for the above XML:

```pycon
>>> from mitxgraders import *
>>> grader = SumGrader(
...     answers={
...         'lower':'0',
...         'upper':'10',
...         'summand':'n*(n+1)',
...         'summation_variable':'n'
...     },
...     input_positions = {
...         'upper': 1,
...         'summand': 2,
...         'lower': 3
...     }
... )

```

Note that when students specify their own variable of summation, it must not conflict with a variable already present in the problem. Note that this means that `i` and `j` are not available as variables of summation (as they are used to indicate the imaginary unit).


## Specifying the Answer

The author's answer should be specified as a dictionary with the following keys:

```python
answers = {
    'lower': 'lower_limit',
    'upper': 'upper_limit',
    'summand': 'summand',
    'summation_variable': 'variable_of_summation'
}
```

Note that each entry is a string value. `SumGrader` can handle numerical, complex, vector and even matrix summands. However, it cannot handle numbered variables where the index of the numbered variable is given by the summation variable. This is due to a limitation in the way that numbered variables are sampled.

Unlike integrals, the order of the limits is unimportant.


## Infinite Sums

`SumGrader` can handle sums over both finite and infinite ranges. A special constant `'infty'` is recognized to cater for the infinite case (and takes on the special value `float('inf')`).

When an infinite range is specified, the grader substitutes `infty` for a large but finite number. This value can be set using the `inft_val` option, which defaults to `1000` (`1e3`). If the grader detects the presence of the factorial function in the summand, it instead uses the value specified by the `infty_val_fact`, which defaults to 80. Note that `(2*80)! = 160! ~ 10^284` is just below the limit of values that can be handled numerically by double precision. This ensures that typical expressions involving factorials will not lead to overflow errors, and also leaves sufficient terms to ensure convergence.

Because infinite sums can be rewritten in a myriad of ways, it is important to ensure that after sufficiently many terms are computed, the summation has converged to within numerical precision. This often means that extra variables must be specified in a small range. E.g., if `x` is included in the summand as `x^n`, we recommend setting `x` in the range `[0,0.5]` or so. Note that `0.5^80 ~ 10^-25`, which should be sufficiently small compared to the leading order terms.

To aid in grading infinite sums, the default tolerance on a `SumGrader` has been set to an absolute value of `1e-12`. This may be important when the answer provided by the instructor includes twice or half as many terms as the answer provided by the student, even though both sums are equivalent when taken to infinity.

So long as infinite summations converge sufficiently rapidly, `SumGrader` does a good job at evaluating them. As examples, we have tested that Taylor series expansions for `exp`, `sin` and `cos` converge to numerical precision for small arguments. We advise against using `SumGrader` for slowly-converging series, such as the typical expansion for `tan^-1(1)`.

Note that if you are using vectors or matrices in your sums, we strongly suggest that you use a small value for both `infty_val` and `infty_val_fact`, probably in the 15-20 range. Otherwise, you may see timeout errors from the python grader on edX.


## Even and Odd Sums

`SumGrader` can be told to sum only over even or odd integers through the `even_odd` option. The default value is 0, which indicates to sum over all integers. Setting it to 1 indicates to sum over odd integers, and 2 indicates to sum over even integers. Instructors must specify this option at construction; students are unable to set this option themselves.

Here is a sample grader that implements the Taylor expansion for sine using odd integers only:

```pycon
>>> from mitxgraders import *
>>> grader = SumGrader(
...     answers={
...         'lower':'1',
...         'upper':'infty',
...         'summand':'(-1)^((n-1)/2)*x^n/fact(n)',
...         'summation_variable':'n'
...     },
...     input_positions={
...         'upper': 1,
...         'summand': 2,
...         'lower': 3
...     },
...     even_odd=1
... )

```


## Other Options

The following options from `FormulaGrader` are available for use in `SumGrader`:

- `user_constants`
- `user_functions`
- `whitelist`
- `blacklist`
- `tolerance`
- `samples` (default: 2)
- `variables`
- `sample_from`
- `failable_evals`
- `numbered_vars`
- `instructor_vars`
- `forbidden_strings`
- `forbidden_message`
- `required_functions`
- `metric_suffixes`

Unless otherwise specified, the defaults are the same as in `FormulaGrader`.


## Option Listing

Here is the full list of options specific to an `SumGrader`.

```python
grader = SumGrader(
    input_positions=dict,
    answers=dict,
    even_odd=int,  # default 0
    infty_val=int,  # default 1000
    inftY_val_fact=int,  # default 80
    # The below options are the same as in FormulaGrader
    variables=list,  # default []
    sample_from=dict,  # default {}
    samples=int,  # default 1
    user_functions=dict,  # default {}
    user_constants=dict,  # default {}
    failable_evals=int,  # default 0
    blacklist=list,  # default []
    whitelist=list,  # default []
    tolerance=(float | percentage),  # default 1e-12
    numbered_vars=list,  # default []
    instructor_vars=list,  # default []
    forbidden_strings=list,  # default []
    forbidden_message=str,  # default 'Invalid Input: This particular answer is forbidden'
    required_functions=list,  # default []
    metric_suffixes=bool,  # default False
)
```
