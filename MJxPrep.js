/*
 * MITx Grading Library Javascript Helper
 * https://github.com/mitodl/mitx-grading-library
 *
 * Copyright 2017-2019 Jolyon Bloomfield and Chris Chudzicki
 *
 * Modifies MathJax AsciiMath renderer to accept a variety of new functions
 * Also defines a preprocessor for further beautification
 *
 * Options can be specified at the top of the script
 * Custom replacements can be specified at the bottom of the script
 */

// Make sure that this script only loads once
if (window.MJxPrep) {
} else {
  // Specify options here!
  window.MJxPrepOptions = {
    conj_as_star: false,
    vectors_as_columns: true
  }

  // Define the preprocessor
  window.MJxPrep = function() {
    /*------------------------------------------------------
     * This is the preprocessor, used for translating inputs
     *------------------------------------------------------
     */
    this.fn = function(eqn) {
      try {
        return preProcessEqn(eqn)
      }
      catch (err) {
        return eqn
      }
    };
  };

  function preProcessEqn(eqn) {
    // Note that /pattern/flags is shorthand for a regex parser
    // g is global - makes all changes

    // Strip spaces, which can confuse the regex matching we're about to do
    eqn = eqn.replace(/ /g, '');

    // log10(x) -> log_10(x)
    eqn = eqn.replace(/log10\(/g, "log_10(");
    // log2(x) -> log_2(x)
    eqn = eqn.replace(/log2\(/g, "log_2(");

    // Factorial: We want fact(n) -> n!, but fact(2n) -> (2n)!
    // Replace fact(...) -> with {:...!:}, wrap with parens as needed
    eqn = replaceFunctionCalls(eqn, 'fact', funcToPostfix('!') )
    // Replace factorial(...) -> with {:...!:}, wrap with parens as needed
    eqn = replaceFunctionCalls(eqn, 'factorial', funcToPostfix('!') )

    // Transpose: trans(x) -> x^T
    // Replace trans(...) -> {:(...)^T:}, with parentheses added as necessary
    eqn = replaceFunctionCalls(eqn, 'trans', funcToPostfix('^T') )

    // Adjoint: adj(x) -> x^dagger
    // Replace adj(...) -> {:(...)^dagger:}, with parentheses added as necessary
    eqn = replaceFunctionCalls(eqn, 'adj', funcToPostfix('^dagger') )

    // Complex Transpose: ctrans(x) -> x^dagger
    // Replace ctrans(...) -> {:(...)^dagger:}, with parentheses added as necessary
    eqn = replaceFunctionCalls(eqn, 'ctrans', funcToPostfix('^dagger') )

    // Cross product: cross(a, b) -> a times b
    eqn = replaceFunctionCalls(eqn, 'cross', function(funcName, args) {
      if (args.length !== 2) {return funcToSelf(funcName, args) ;}
      return '{:' + groupExpr(args[0]) + ' times ' + groupExpr(args[1]) + ':}'
    } )

    // Conjugate as star
    // Replace conj(...) -> {:(...)^*:}, with parentheses added as necessary
    if (window.MJxPrepOptions.conj_as_star) {
      eqn = replaceFunctionCalls(eqn, 'conj', funcToPostfix('^**') )
    }

    // Display vectors as columns, if the option is turned on
    if (window.MJxPrepOptions.vectors_as_columns) {
      eqn = columnizeVectors(eqn)
    }

    // Do any custom replacements (see end of script)
    eqn = customReplacements(eqn)

    // This is done last, so that it doesn't mess up subsequent processing
    eqn = wrapVariables(eqn)
    eqn = wrapFuncCalls(eqn)

    // Fix Kronecker deltas now: kronecker(a, b) -> kronecker_{a, b}
    // The wrapping interferes with parsing of delta_{complexthings},
    // due to not satisfying the usual regex forms for a variable or function
    eqn = replaceFunctionCalls(eqn, 'kronecker', function(funcName, args) {
      if (args.length !== 2) {return funcToSelf(funcName, args) ;}
      return 'delta_{' + args[0] + ',' + args[1] + '}'
    })

    // Return the preprocessed equation
    return eqn;
  }

  // Try to update AsciiMath
  function updateMathJax() {
    if (MathJax.InputJax.AsciiMath) {
      // Grab the AsciiMath object
      var AM = MathJax.InputJax.AsciiMath.AM;

      // All of these new symbols are based on those appearing in the AsciiMath definitions
      // See https://github.com/asciimath/asciimathml/blob/master/ASCIIMathML.js
      // Add functions, including some edX functions that don't exist in AsciiMath
      AM.newsymbol({
        input: "arctan2",
        tag: "mi",
        output: "arctan",
        tex: null,
        ttype: AM.TOKEN.UNARY,
        func: true
      });
      AM.newsymbol({
        input: "arcsec",
        tag: "mi",
        output: "arcsec",
        tex: null,
        ttype: AM.TOKEN.UNARY,
        func: true
      });
      AM.newsymbol({
        input: "arccsc",
        tag: "mi",
        output: "arccsc",
        tex: null,
        ttype: AM.TOKEN.UNARY,
        func: true
      });
      AM.newsymbol({
        input: "arccot",
        tag: "mi",
        output: "arccot",
        tex: null,
        ttype: AM.TOKEN.UNARY,
        func: true
      });
      AM.newsymbol({
        input: "arcsinh",
        tag: "mi",
        output: "arcsinh",
        tex: null,
        ttype: AM.TOKEN.UNARY,
        func: true
      });
      AM.newsymbol({
        input: "arccosh",
        tag: "mi",
        output: "arccosh",
        tex: null,
        ttype: AM.TOKEN.UNARY,
        func: true
      });
      AM.newsymbol({
        input: "arctanh",
        tag: "mi",
        output: "arctanh",
        tex: null,
        ttype: AM.TOKEN.UNARY,
        func: true
      });
      AM.newsymbol({
        input: "arcsech",
        tag: "mi",
        output: "arcsech",
        tex: null,
        ttype: AM.TOKEN.UNARY,
        func: true
      });
      AM.newsymbol({
        input: "arccsch",
        tag: "mi",
        output: "arccsch",
        tex: null,
        ttype: AM.TOKEN.UNARY,
        func: true
      });
      AM.newsymbol({
        input: "arccoth",
        tag: "mi",
        output: "arccoth",
        tex: null,
        ttype: AM.TOKEN.UNARY,
        func: true
      });
      AM.newsymbol({
        input: "re",
        tag: "mi",
        output: "Re",
        tex: null,
        ttype: AM.TOKEN.UNARY,
        func: true
      });
      AM.newsymbol({
        input: "im",
        tag: "mi",
        output: "Im",
        tex: null,
        ttype: AM.TOKEN.UNARY,
        func: true
      });
      AM.newsymbol({
        input: "trace",
        tag: "mi",
        output: "Tr",
        tex: null,
        ttype: AM.TOKEN.UNARY,
        func: true
      });
      // This is the dagger symbol, used in the Hermitian conjugate/adjoint
      AM.newsymbol({
        input:"dagger",
        tag:"mi",
        output:"\u2020",
        tex:null,
        ttype:AM.TOKEN.CONST
      });
      // This is hbar, often used in physics
      AM.newsymbol({
        input:"hbar",
        tag:"mo",
        output:"\u210F",
        tex:null,
        ttype:AM.TOKEN.CONST});
      // These next few are taken directly from the AsciiMath repository;
      // the revision is too new for MathJax to incorporate however
      // Here is the github discussion: https://github.com/asciimath/asciimathml/issues/58
      // They simply add some extra bracketing symbols, which sometimes come in handy
      AM.newsymbol({
        input:"|:",
        tag:"mo",
        output:"|",
        tex:null,
        ttype:AM.TOKEN.LEFTBRACKET
      });
      AM.newsymbol({
        input:":|",
        tag:"mo",
        output:"|",
        tex:null,
        ttype:AM.TOKEN.RIGHTBRACKET
      });
      AM.newsymbol({
        input:":|:",
        tag:"mo",
        output:"|",
        tex:null,
        ttype:AM.TOKEN.CONST
      });

      // Add special function: conj
      // If the preprocessor is used and the option conj_as_star is true,
      // conj will be transformed to a star, and this definition won't apply
      AM.newsymbol({
        input: "conj",
        tag: "mover",
        output: "\xAF",
        tex: null,
        ttype: AM.TOKEN.UNARY,
        acc: true
      });


      // Ask MathJax to reprocess all input boxes, as saved answers may have rendered
      // before these definitions went through
      MathJax.Hub.Queue([
        "Reprocess",
        MathJax.Hub,
        "div.equation"
      ]);

      // No need to update again
      clearInterval(checkExist);
      console.log(
        "MITx Grading Library: Updated AsciiMath renderer definitions"
      );
    }
  }

  // Check for the AsciiMath object every 200ms
  var checkExist = setInterval(updateMathJax, 200);

  // set of AsciiMath symbols classified as mover (math-overscript) tags
  // (This should be a Set object, but ie11 doesn't fully support Sets)
  OVERSCRIPT_SYMBOLS = {
    bar: true,
    conj: true,
    ddot: true,
    dot: true,
    hat: true,
    obrace: true,
    overarc: true,
    overbrace: true,
    overline: true,
    overparen: true,
    overset: true,
    stackrel: true,
    tilde: true,
    vec: true
  }

  // callback function for String.prototype.replace
  function wrapIfNotOverscript(match, substr) {
    return OVERSCRIPT_SYMBOLS[substr]
      ? substr
      : '{:' + substr + ':}'
  }

  /**
   * Detect variables, then wrap them in invisible brackets
   * Without wrapping symbols, expressions like x'/x render poorly
   *
   * @param  {string} eqn
   * @return {string}
   */
  function wrapVariables(eqn) {
    // Need a regex to match any possible variable name
    // This regex matches all valid expressions in the python parser
    // If invalid expressions are given, this is less predictable, but the wrapping shouldn't hurt anything
    var var_expr = /(?=([a-zA-Z][a-zA-Z0-9]*(?:(?:_{-?[a-zA-Z0-9]+}(?:\^{-?[a-zA-Z0-9]+})?|\^{-?[a-zA-Z0-9]+})|[\w]*)'*))\1(?![(}])/g
    // Explanation:
    // We really need atomic groups here so that something like 'f0(x)'' doesn't match 'f',
    // but javascript doesn't have them. Hence, we hack them in using the trick from here:
    // http://instanceof.me/post/52245507631/regex-emulate-atomic-grouping-with-lookahead
    /*
       (?=                              # Open lookahead group
         (                              # Open capturing group
           [a-zA-Z]                     # Must start with an alpha character
           [a-zA-Z0-9]*                 # Followed by any number of alphanumeric characters
           (?:                          # Open noncapturing group (subscripts/tensors)
             (?:                        # Open noncapturing group (tensor _^ or ^)
               _{-?[a-zA-Z0-9]+}        # Match a tensor subscript
               (?:\^{-?[a-zA-Z0-9]+})?  # Match an optional tensor superscript
             |                          # Or
               \^{-?[a-zA-Z0-9]+}       # Match a tensor superscript
             )                          # Close group (tensor _^or ^)
           |                            # Or
             [\w]*                      # Match any alphanumeric or _, any number of times
           )                            # Close group (subscripts/tensors)
           '*                           # Match any number of primes
         )                              # Close capturing group
       )                                # Close lookahead group
       \1                               # Require lookahead group to appear here
       (?![(}])                         # Negative lookahead: '(' (function) or '}' (tensor indices)
     */
    // This site is really useful for debugging: https://www.regextester.com/
    eqn = eqn.replace(var_expr, wrapIfNotOverscript);

    return eqn
  }

  /**
   * Detect function calls, then wrap them in invisible brackets
   * Without wrapping function calls, expressions like p(x)/2 render poorly
   * @param  {string} eqn
   * @return {string}
   */
  function wrapFuncCalls(eqn) {

    // Like var_expr in wrapVariables, but requires ending in a parenthesis
    var func_call = /([a-zA-Z][a-zA-Z0-9]*(?:(?:_{-?[a-zA-Z0-9]+}(?:\^{-?[a-zA-Z0-9]+})?|\^{-?[a-zA-Z0-9]+})|[\w]*)'*)\(/g
    var matches = []
    var match = true
    while (match !== null) {
      // func_call.exec will return a match array or null
      // Since func_call is a global-matching regexp (g), subsequent matches
      // start from the last match index.
      var match = func_call.exec(eqn)
      match && matches.push(match)
    }

    // Iterate over matches from end of string to front of string, since
    // replacing match ---> {:match:} lengthens the string and would
    // mess up the indices if we iterated from start to finish.
    for (var j=matches.length - 1; j >= 0; j += -1) {
      var funcStart = matches[j].index

      var bracketOpens = funcStart + (matches[j][0].length - 1)
      var bracketCloses = findClosingBrace(eqn, bracketOpens)
      // If brace does not close, bracketCloses is null. In that case,
      // consider the end of the function to be bracketOpens
      var funcEnd = bracketCloses === null ? bracketOpens : bracketCloses + 1

      var front = eqn.slice(0, funcStart)
      var middle = eqn.slice(funcStart, funcEnd)
      eqn = front + wrapIfNotOverscript(null, middle) + eqn.slice(funcEnd)
    }

    return eqn
  }

  /**
   * get index at which the brace at braceIdx in expr is closed, or null if it
   * does not close.
   *
   * @param  {string} expr
   * @param  {number} openIdx index of opening brace
   * @return {?number}          [description]
   */
  function findClosingBrace(expr, openIdx) {
    var braces = { "[": "]", "<": ">", "(": ")", "{": "}" };

    var openingBrace = expr[openIdx];

    var closingBrace = braces[openingBrace];

    if (closingBrace === undefined) {
      throw Error(
        expr +
          " does not contain an opening brace at position " +
          openIdx +
          "."
      );
    }

    var stack = 1;

    for (var j = openIdx + 1; j < expr.length; j++) {
      if (expr[j] === openingBrace) {
        stack += +1;
      } else if (expr[j] === closingBrace) {
        stack += -1;
      }
      if (stack === 0) {
        return j;
      }
    }

    // stack !== 0
    return null
  }

  /**
   * Splits a stringified list at top level only.
   *
   * "1 + 2, 2*[3, 4], 1" => ["1 + 2", "2*[3, 4]", "1"]
   *
   * @param  {string} str stringified list, WITHOUT opening/closing bracket
   * @return {string[]} array of string arguments
   */
  function shallowListSplit(str) {
    var openers = { '[': true, '(': true }
    var argStartPositions = [0]

    // Scan through str
    var j = 0
    while (j < str.length) {
      if (openers[str[j]]) {
        j = findClosingBrace(str, j)
        if (j === null) { return str } // happens if brace does not close
        continue;
      }
      if (str[j] === ',') {
        // argument starts at j+1, not at j (which is a comma)
        argStartPositions.push(j+1)
      }
      j++ // increment index
    }

    var argsList = []
    argStartPositions.forEach(function(current, index, array) {
      if (index + 1 < array.length) {
        // array[index + 1] is start of next argument, we want to stop at
        // the comma just before it
        var stopAt = array[index + 1] - 1
        argsList.push(str.substring(current, stopAt))
      }
      else {
        argsList.push(str.substring(current))
      }

    } )

    return argsList
  }

  /**
   * Recursively replace each instance of 'funcName(<args>)' that occurs after
   * startingAt in a string with the return value of action(funcName, args)
   *
   * @param  {string} expr expression we're processing
   * @param  {string} funcName name of function we're looking for
   * @param  {function} action a callback with signature
   *                           (funcName: string, args: [str]) => string
   * @param  {?number} startingAt index after which replacements occur, defaults to 0
   * @return {[type]}          [description]
   */
  function replaceFunctionCalls(expr, funcName, action, startingAt) {
    // default value for startingAt
    var startingAt = startingAt ? startingAt : 0

    // Find the first instance of 'funcName(<args>)' we care about
    var funcStart = expr.indexOf(funcName + '(', startingAt);

    // If we found nothing, get out
    if (funcStart < 0) return expr;

    // Make sure the previous character isn't an alpha character
    // (don't match the end of a function name we don't want to match)
    // This will allow us to replace "f(...)" without replacing "diff(...)"
    if( funcStart > 0 && /[a-zA-Z]/.test(expr.substr(funcStart-1, 1)) ) {
      // False positive. Keep on looking!
      return replaceFunctionCalls(expr, funcName, action, funcStart + 1);
    }

    var openCallParens = funcStart + funcName.length
    var closeCallParens = findClosingBrace(expr, openCallParens)
    if (closeCallParens === null) {
      // if opening parens does not close, skip this instance and process the
      // remaining string
      return replaceFunctionCalls(expr, funcName, action, openCallParens + 1)
    }
    var argsString = expr.substring(openCallParens + 1, closeCallParens)

    // replace any function calls that appear inside the arguments
    // this will bail out without further recursion if argsString has no
    // function calls
    var processedArgsString = replaceFunctionCalls(argsString, funcName, action)
    var args = shallowListSplit(processedArgsString)

    // perform the action
    var finished = expr.substring(0, funcStart) + action(funcName, args)
    var unfinished = expr.substring(closeCallParens + 1)

    // Recursively process the unfinished string
    return replaceFunctionCalls(finished + unfinished, funcName, action, finished.length + 1)

  }

  function columnizeVectors(expr, startingAt) {
    var openedAt = expr.indexOf('[', startingAt)
    if (openedAt < 0) { return expr; }
    var closedAt = findClosingBrace(expr, openedAt)
    if (closedAt === null) { return expr } // happens if opening brace is not closed
    // Get the array string, including opening/closing brackets
    var array = expr.substring(openedAt, closedAt + 1)

    var finished = expr.substring(0, openedAt) + columnizeSingleVector(array)
    var unfinished = expr.substring(closedAt + 1)

    return columnizeVectors(finished + unfinished, finished.length + 1)
  }

  function columnizeSingleVector(expr) {
    if (!expr.startsWith('[') || !expr.endsWith(']')) {
      throw Error('Cannot columnize vector ' + expr + ' , it must start and end with square brackets.')
    }
    var content = expr.substring(1, expr.length - 1)
    var items = shallowListSplit(content)
    if (items.length <= 1) {
      return expr
    }

    // make sure items are not already rendering as vectors
    for (var i = 0; i < items.length; i++) {
      var item = items[i]
      if (item.indexOf('[') > 0 || item.indexOf(']') > 0 ) {
        // abort! do not columnize! The items contain arrays, this appears to
        // be a matrix.
        return expr
      }
    }

    return '[[' + items.join('], [') + ']]'

  }

  /**
   * Trim leading/trailing whitespace from expr and wrap expr in parens unless
   * it is already a single group (e.g., already wrapped in parens, or a single
   * character)
   *
   * @param  {string} expr
   * @return {string}
   */
  function groupExpr(expr) {
    expr = expr.trim()
    var atomic = ['alpha', 'beta', 'chi', 'delta', 'Delta', 'epsi', 'varepsilon', 'eta', 'gamma', 'Gamma', 'iota', 'kappa', 'lambda', 'Lambda', 'lamda', 'Lamda', 'mu', 'nu', 'omega', 'Omega', 'phi', 'varphi', 'Phi', 'pi', 'Pi', 'psi', 'Psi', 'rho', 'sigma', 'Sigma', 'tau', 'theta', 'vartheta', 'Theta', 'upsilon', 'xi', 'Xi', 'zeta']
    var temp = expr.startsWith('hat') || expr.startsWith('vec')
      ? expr.substring(3)
      : expr

    if (temp.length == 1 || atomic.includes(temp)) {
      return expr
    }

    // If expression is already wrapped in parens or brackets, don't add extra
    if (expr.startsWith("(") || expr.startsWith("[")) {
      var closedAt = findClosingBrace(expr, 0)
      if (closedAt === null) {return expr} // happens if opening brace is not closed
      if (closedAt === expr.length - 1) {
        return expr
      }
    }
    return "(" + expr + ")"

  }

  function funcToSelf(funcName, args) {
    return funcName + '(' + args + ')';
  }
  function funcToPostfix(postfix){
    return function(funcName, args) {
      if (args.length !== 1) { return funcToSelf(funcName, args) }
      return "{:" + groupExpr(args[0]) + postfix + ":}"
    }
  }

  // Hacky exports for test file since we aren't transpiling
  window.MJxPrepExports = {
    findClosingBrace: findClosingBrace,
    replaceFunctionCalls: replaceFunctionCalls,
    groupExpr: groupExpr,
    shallowListSplit: shallowListSplit,
    preProcessEqn: preProcessEqn,
    wrapVariables: wrapVariables,
    wrapFuncCalls: wrapFuncCalls,
    columnizeVectors: columnizeVectors,
    funcToPostfix: funcToPostfix
  }

  // A function to allow for custom replacements
  function customReplacements(eqn) {
    var working = eqn;

    // Manipulate working however you like here!

    return working;
  }
}
