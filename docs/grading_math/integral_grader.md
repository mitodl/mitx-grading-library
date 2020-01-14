# IntegralGrader

`IntegralGrader` is a specialized grading class used to grade the construction of integrals. Students can input the limits on the integral, the variable of integration, and the integrand (or some subset thereof), and will be graded correct if their construction is numerically equivalent to the instructor's construction. This method of grading allows for arbitrary variable substitutions and redefinitions.

The grader numerically evaluates the student- and instructor-specified integrals using `scipy.integrate.quad`. This quadrature-based integration technique is efficient and flexible. It handles many integrals with poles in the integrand and can integrate over infinite domains.

However, some integrals may behave badly. These include, but are not limited to,
the following:

- integrals with highly oscillatory integrands
- integrals that evaluate analytically to zero

In some cases, problems might be avoided by using the integrator_options configuration key to provide extra instructions to `scipy.integrate.quad`, as documented below.


## XML Setup

We recommend copying the following XML to set up a problem using `IntegralGrader`:

```XML
<style>
  .xmodule_display.xmodule_CapaModule .problem .capa_inputtype.textline input {
    min-width: 0 !important;
  }
  .xmodule_display.xmodule_CapaModule div.problem section div span.MathJax {
    display: inline-block !important;
  }
  .xmodule_display.xmodule_CapaModule div.problem section div span.MathJax_Preview {
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
            <textline size="5" correct_answer="1"/>
          </td>
        </tr>
        <tr>
          <td>
            <p> \( \displaystyle \huge{ \int }\)</p>
          </td>
          <td>
            <br/>
            <textline inline="1" size="10" correct_answer="e^x" trailing_text="  [mathjaxinline] dx [/mathjaxinline]"/>
          </td>
        </tr>
        <tr>
          <td colspan="2">
            <textline size="5" correct_answer="0"/>
          </td>
        </tr>
      </tbody>
    </table>
  </customresponse>
</span>
```

This sets up an integral where students can input the limits of integration and the integrand (the variable of integration has been fixed to be `x` in this case).

Further examples of formatting integrals are shown in the example course.


## Specifying the Input Format

The grader must be told which input is what, based on the order that the inputs appear in the XML. This is done through the `input_positions` dictionary. If not specified, it is assumed that the following positions are used:

```python
input_positions = {
    'lower': 1,
    'upper': 2,
    'integrand': 3,
    'integration_variable': 4
}
```

This requires students to enter all four parameters in the indicated order.

If the author overrides the default `input_positions` value, any subset of the keys ('lower', 'upper', 'integrand', 'integration_variable') may be specified. Key values should be

- continuous integers starting at 1, or
- (default) None, indicating that the parameter is not entered by student

For example,

```python
input_positions = {
    'lower': 1,
    'upper': 2,
    'integrand': 3
}
```

indicates that the problem has 3 input boxes which represent the lower limit, upper limit, and integrand in that order. The `integration_variable` is NOT entered by student and is instead given by the value specified by author in 'answers'.

Here is a sample grader for the above XML:

```pycon
>>> from mitxgraders import *
>>> grader = IntegralGrader(
...     answers={
...         'lower':'0',
...         'upper':'1',
...         'integrand':'e^x',
...         'integration_variable':'x'
...     },
...     input_positions = {
...         'upper': 1,
...         'integrand': 2,
...         'lower': 3
...     }
... )

```

Note that when students specify their own variable of integration, it must not conflict with a variable already present in the problem.


## Specifying the Answer

The author's answer should be specified as a dictionary with the following keys:

```python
answers = {
    'lower': 'lower_limit',
    'upper': 'upper_limit',
    'integrand': 'integrand',
    'integration_variable': 'variable_of_integration'
}
```

Note that each entry is a string value.

`IntegralGrader` can handle integrals over both finite and infinite domains. A special constant `'infty'` is recognized to cater for the infinite case (and takes on the special value `float('inf')`).


## Other Options

If you wish to allow a student's integrand to be complex-valued at any point in the domain of the integral, set `complex_integrand=True`. If set to False (the default), a student's submission will be graded as incorrect if their integrand becomes complex anywhere in the domain.

You can modify the integration options used by [`scipy.integrate.quad`](https://docs.scipy.org/doc/scipy-0.16.1/reference/generated/scipy.integrate.quad.html) by passing a dictionary of keyword-argument values using the option `integrator_options`.

The following options from `FormulaGrader` are available for use in `IntegralGrader`:

- `user_constants`
- `user_functions`
- `whitelist`
- `blacklist`
- `tolerance`
- `samples` (default: 1)
- `variables`
- `sample_from`
- `failable_evals`

Unless otherwise specified, the defaults are the same as in `FormulaGrader`.


## Option Listing

Here is the full list of options specific to an `IntegralGrader`.

```python
grader = IntegralGrader(
    input_positions=dict,
    answers=dict,
    integrator_options=dict,  # default {'full_output': 1}
    complex_integrand=bool,  # default False
    # The below options are the same as in FormulaGrader
    variables=list,  # default []
    sample_from=dict,  # default {}
    samples=int,  # default 1
    user_functions=dict,  # default {}
    user_constants=dict,  # default {}
    failable_evals=int,  # default 0
    blacklist=list,  # default []
    whitelist=list,  # default []
    tolerance=(float | percentage),  # default '0.01%'
)
```
