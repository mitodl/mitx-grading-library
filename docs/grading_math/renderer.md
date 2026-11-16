# AsciiMath Renderer Definitions

When math input is expected from students, edX offers a math preview that attempts to show their expression in normal mathematical notation. There are two ways to provide this preview:

```XML
<formulaequationinput/>
or
<textline math="1"/>
```

The `formulaequationinput` tag uses server-side parsing and rendering to display the preview to the student. By and large, the preview from `formulaequationinput` is better than that of `textline`, as it treats functions correctly, and displays a number of LaTeX symbols natively. The downsides to `formulaequationinput` are that it doesn't recognize vectors such as `vecx` or `hatx`, the factorial and conjugation functions just apply as `fact(x)` and `conj(x)`, and because the processing is done server-side, we are unable to enhance the display at all.

Open edX versions that load MathJax 4 (after [openedx/edx-platform#33555](https://github.com/openedx/edx-platform/pull/33555)) render the `formulaequationinput` preview in the browser through AsciiMath instead, the same way as `textline`. There, the symbol definitions in `MJxPrep.js` (such as `arctanh` and `hbar`) apply to `formulaequationinput` previews too, as long as `MJxPrep.js` is loaded on the page (e.g. by the `<script>` tag described below). The preprocessor doesn't, since `formulaequationinput` has no `preprocessorClassName`.

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


## Customizing for a Course

Don't edit `MJxPrep.js` itself. Put your course's options and extensions in a separate file, e.g. `MJxPrepCustom.js`, and upload it to your static assets alongside `MJxPrep.js`. That way you can replace `MJxPrep.js` with a new release as is, and keep your changes.

Load your file in each problem that uses the preprocessor, next to the `<textline>`:

```XML
<script type="text/javascript" src="/static/MJxPrepCustom.js"></script>
```

`MJxPrep.js` reads your settings each time it needs them, so the two files can load in either order.

### Options

Set `window.MJxPrepOptions` to change how the preprocessor displays some functions. Any option you leave out keeps its default.

```javascript
window.MJxPrepOptions = {
  conj_as_star: true,
  vectors_as_columns: false
};
```

By default, `conj()` displays as a bar over the argument to the function. Set `conj_as_star: true` to display complex conjugates as a superscript star instead.

By default, vectors `[1, 2, 3]` display as a column vector when the preprocessor is loaded (without the preprocessor, it will display as a row). Set `vectors_as_columns: false` to display them as a row vector instead.

### Extending definitions

If you're building a course that uses math extensively, you probably want some symbols that can't be written as an edX variable. Set `window.MJxPrepCustom` to extend the preprocessor and the AsciiMath symbols:

```javascript
window.MJxPrepCustom = {
  // Called before our preprocessing (after spaces are stripped)
  pre: function(eqn, mjx) {
    // Double factorial: ffact(n) -> n!!
    return mjx.replaceFunctionCalls(eqn, 'ffact', mjx.funcToPostfix('!!'));
  },
  // Called after our preprocessing
  post: function(eqn, mjx) {
    // Variables are already wrapped in {: :} by this point
    return eqn.replace(/dphidx/g, '{:(partial phi)/(partial x):}');
  },
  // New AsciiMath symbols
  symbols: [
    {input: "ell", tag: "mo", output: "\u2113", tex: null, ttype: "CONST"},
    {input: "erf", tag: "mo", output: "erf", tex: null, ttype: "UNARY", func: true}
  ]
};
```

`pre` and `post` take the student's input as a string and return the replacement. We suggest trying `post` first, and using `pre` only if necessary. The second argument holds helper functions from `MJxPrep.js`, such as `replaceFunctionCalls`, `funcToPostfix` and `funcToSelf`, which detect function calls and perform replacements.

Each entry in `symbols` is passed to AsciiMath's `AM.newsymbol`, with `ttype` given as the name of the token type (`"CONST"`, `"UNARY"`, `"BINARY"`, `"LEFTBRACKET"`, `"RIGHTBRACKET"` etc.) rather than `AM.TOKEN.CONST`, since AsciiMath may not have loaded when your file runs. See [ASCIIMathML.js](https://github.com/asciimath/asciimathml/blob/master/ASCIIMathML.js) for the symbol format and examples.


## Notes

* You can take advantage of the symbol definitions and preprocessor even if you're not using the grading library at all. Just load it up in any `textline` tags you're using. (We find the preprocessor so good that we use if for every math display problem in our courses!)

* The javascript is constructed to only load its definitions once, no matter how many times the file is loaded. It's safe to use the preprocessor in as many `textline` boxes as you like.

* The [mathematical functions](functions_and_constants.md) article provides the complete list of functions that are corrected by the new AsciiMath renderer definitions.
