# MathJax Renderer Definitions

When math input is expected from students, edX offers a math preview that attempts to show their expression in normal mathematical notation. This preview is rendered by MathJax via AsciiMath. While the preview does a reasonably good job, there are many situations where it falls down, even for standard edX functions (for example, try typing in `1/arctanh(x)` in an edX input box!). We have constructed a series of renderer definitions to supplement the standard AsciiMath definitions in order to provide better previews.

## How it works

The renderer definitions are located in a javascript file, `MJxPrep.js`, which should be uploaded to the static assets folder for your course. This javascript file loads two components: symbol definitions and a preprocessor.

The symbol definitions are used to teach AsciiMath how to display various functions properly, such as `re`, `im`, `arctanh` etc. To load the symbol definitions in a problem, place the following HTML code somewhere in the problem.

```XML
<script type="text/javascript" src="/static/MJxPrep.js"></script>
```

Some functions are too complex for a symbol definition, and need the student's input to be preprocessed into AsciiMath before rendering. These functions are `log10`, `log2`, `fact` and `factorial`. To use these, you need to add `preprocessorClassName` and `preprocessorSrc` properties to any textline tags that use the preprocessor.

```XML
<customresponse cfn="grader">
    <textline correct_answer="1/fact(5)" math="1" preprocessorClassName="MJxPrep" preprocessorSrc="/static/MJxPrep.js"/>
</customresponse>
```

If you use the preprocessor in your problem, you get the symbol definitions as well (you don't need to load them separately).


## Notes

* Note that you don't need to use the grading library to take advantage of the symbol definitions and/or the preprocessor; they work just as well for the normal edX `formularesponse` problems!

* The javascript is constructed to only load its definitions once, no matter how many times the file is loaded. It's safe to use the preprocessor in as many textline boxes as you like.

* If you have a display issue with AsciiMath, it's likely that you can extend the symbol definitions and preprocessor to make your expressions display nicely for students.
