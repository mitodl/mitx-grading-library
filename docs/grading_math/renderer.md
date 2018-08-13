# AsciiMath Renderer Definitions

When math input is expected from students, edX offers a math preview that attempts to show their expression in normal mathematical notation. There are two ways to provide this preview:

```XML
<formulaequationinput/>
or
<textline math="1"/>
```

The `formulaequationinput` tag uses server-side parsing and rendering to display the preview to the student. By and large, the preview from `formulaequationinput` is better than that of `textline`, as it treats functions correctly, and displays a number of LaTeX symbols natively. The downsides to `formulaequationinput` are that it doesn't recognize vectors such as `vecx` or `hatx`, the factorial and conjugation functions just apply as `fact(x)` and `conj(x)`, and because the processing is done server-side, we are unable to enhance the display at all.

The `textline` tag treats the student input as AsciiMath for the purpose of generating a preview, using MathJax to render it. While the preview does a reasonably good job, there are many situations where it falls down, even for standard edX functions (for example, try typing in `1/arctanh(x)` in a textline box!). Because this is done client-side through javascript, it's possible to supplement the AsciiMath definitions to handle new situations. We have constructed a series of renderer definitions to supplement the standard AsciiMath definitions in order to provide better previews.

This article describes how to use our new AsciiMath renderer definitions with a `<textline>` tag.


## How it works

The renderer definitions are located in a javascript file, `MJxPrep.js`, which should be uploaded to the static assets folder for your course. This javascript file loads two components: symbol definitions and a preprocessor.

The symbol definitions are used to teach AsciiMath how to display various functions properly, such as `re`, `im`, `arctanh` etc. To load the symbol definitions in a problem, place the following HTML code somewhere in the problem.

```XML
<script type="text/javascript" src="/static/MJxPrep.js"></script>
```

Some functions are too complex for a symbol definition, and need the student's input to be preprocessed into AsciiMath before rendering. These functions are `log10`, `log2`, `fact`/`factorial`, `trans`, `adj`/`ctrans` and `cross`.

It is quite common to have a variable name begin with `delta` or `Delta`, such as `Deltax`. Unfortunately, AsciiMath treats such variables as two separate entries, and can sometimes split them inopportunely, such as for the expression `1/Deltax`. The preprocessor detects such variable names and ensures that AsciiMath displays them correctly.

To use these features, you need to add `preprocessorClassName` and `preprocessorSrc` properties to any `<textline/>` tags that use the preprocessor.

```XML
<customresponse cfn="grader">
    <textline correct_answer="1/fact(5)" math="1" preprocessorClassName="MJxPrep" preprocessorSrc="/static/MJxPrep.js"/>
</customresponse>
```

If you use the preprocessor in your problem, you get the symbol definitions as well (you don't need to load them separately).


### Options

There are a few configurable options for the preprocessor in `MJxPrep.js`.

By default, `conj()` displays as a bar over the argument to the function. However, you may wish for complex conjugates to be displayed as a superscript star. If so, you can set `conj_as_star: true` at the start of the file.

By default, vectors `[1, 2, 3]` display as a column vector when the preprocessor is loaded (without the preprocessor, it will display as a row). If you would instead like them to display as a row vector, you can set the option `vectors_as_columns: false` at the start of the file.


## Notes

* Note that you don't need to use the grading library to take advantage of the symbol definitions and/or the preprocessor; they work just as well for the normal edX `formularesponse` problems!

* The javascript is constructed to only load its definitions once, no matter how many times the file is loaded. It's safe to use the preprocessor in as many `textline` boxes as you like.

* If you have a display issue with AsciiMath, it's likely that you can extend the symbol definitions and preprocessor to make your expressions display nicely for students.

* The [mathematical functions](functions.md) article provides the complete list of functions that are corrected by the new AsciiMath renderer definitions.
