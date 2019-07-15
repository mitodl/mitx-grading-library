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


## How it Works

The renderer definitions are located in a javascript file, `MJxPrep.js`, which should be uploaded to the static assets folder for your course. This javascript file has two components: symbol definitions and a preprocessor.

The symbol definitions are used to teach AsciiMath how to display various functions properly, such as `re`, `im`, `arctanh` etc. To load the symbol definitions in a problem, place the following HTML code somewhere in the problem.

```XML
<script type="text/javascript" src="/static/MJxPrep.js"></script>
```

Some functions are too complex for a symbol definition, and need the student's input to be preprocessed into AsciiMath before rendering. These functions include `log10`, `log2`, `fact`/`factorial`, `trans`, `adj`/`ctrans` and `cross`.

It is quite common to have a variable name begin with `delta` or `Delta`, such as `Deltax`. Unfortunately, AsciiMath treats such variables as two separate entries, and can sometimes split them inopportunely, such as for the expression `1/Deltax`. The preprocessor detects such variable names and ensures that AsciiMath displays them correctly.

To use these features, you need to add `preprocessorClassName` and `preprocessorSrc` properties to any `<textline/>` tags that use the preprocessor, such as in the following example.

```XML
<customresponse cfn="grader">
    <textline correct_answer="1/fact(5)" math="1" preprocessorClassName="MJxPrep" preprocessorSrc="/static/MJxPrep.js"/>
</customresponse>
```

If you use the preprocessor in your problem, you get the symbol definitions as well (you don't need to load them separately using a script tag).


## Options

There are a few configurable options for the preprocessor in `MJxPrep.js`.

By default, `conj()` displays as a bar over the argument to the function. However, you may wish for complex conjugates to be displayed as a superscript star. If so, you can set `conj_as_star: true` at the start of the file.

By default, vectors `[1, 2, 3]` display as a column vector when the preprocessor is loaded (without the preprocessor, it will display as a row). If you would instead like them to display as a row vector, you can set the option `vectors_as_columns: false` at the start of the file.


## Extending Definitions

If you're building a course that uses math extensively, it's likely that you want to use some sort of symbol that can't be written in the form of an edX variable. In this situation, we have provided two functions to extend the preprocessor. At the bottom of `MJxPrep.js`, you will find the functions `customPreReplacements` and `customPostReplacements`, which are called before and after our preprocessing functions occur, respectively. You can perform whatever manipulations you desire in these functions. As an example of a pre-replacement, consider the following line which implements the double factorial:

```javascript
working = replaceFunctionCalls(working, 'ffact', funcToPostfix('!!') )
```

This leverages our `replaceFunctionCalls` and `funcToPostfix` functions which detect function calls and perform replacements, respectively (a number of other useful functions are included in the javascript file).

As an example of a post-replacement, the following line simply replaces a variable name with something that actually looks like a derivative:

```javascript
working = working.replace(/dphidx/g, '{:(partial phi)/(partial x):}');
```

This is a trivial example of using regex to make a replacement; of course, more complicated replacements are also possible.

Finally, if you want to introduce new symbols to AsciiMath using unicode, it's simple to do so. Here's an example of how we introduce hbar to the system:

```javascript
// This is hbar, often used in physics
AM.newsymbol({
  input:"hbar",
  tag:"mo",
  output:"\u210F",
  tex:null,
  ttype:AM.TOKEN.CONST});
```


## Notes

* You can take advantage of the symbol definitions and preprocessor even if you're not using the grading library at all. Just load it up in any `textline` tags you're using. (We find the preprocessor so good that we use if for every math display problem in our courses!)

* The javascript is constructed to only load its definitions once, no matter how many times the file is loaded. It's safe to use the preprocessor in as many `textline` boxes as you like.

* The [mathematical functions](functions_and_constants.md) article provides the complete list of functions that are corrected by the new AsciiMath renderer definitions.
