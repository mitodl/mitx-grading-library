/*
 * MITx Grading Library Javascript Helper
 * https://github.com/mitodl/mitx-grading-library
 *
 * Copyright 2017-2018 Jolyon Bloomfield and Chris Chudzicki
 *
 * Modifies MathJax AsciiMath renderer to accept a variety of new functions
 * Also defines a preprocessor for further beautification
 *
 */

// Make sure that this script only loads once
if (window.MJxPrep) {
} else {
  // Specify options
  window.MJxPrepOptions = {
    conj_as_star: true,
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
    // log10(x) -> log_10(x)
    eqn = eqn.replace(/log10\(/g, "log_10(");
    // log2(x) -> log_2(x)
    eqn = eqn.replace(/log2\(/g, "log_2(");

    // Match Deltaxyz and deltaxyz and wrap in invisible brackets for display
    // So, DeltaE -> {:DeltaE:}, deltasomething -> {:deltasomething:}
    eqn = eqn.replace(/([Dd]elta)([a-zA-Z]+)/g, "{:$1$2:}");

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

    /*
     * If you want to do any custom preprocessing, here is the place to do it
     */



    // Return the preprocessed equation
    return eqn;
  }

  // Try to update AsciiMath
  function updateMathJax() {
    if (MathJax.InputJax.AsciiMath) {
      // Grab the AsciiMath object
      AM = MathJax.InputJax.AsciiMath.AM;

      // All of these new symbols are based on those appearing in the AsciiMath definitions
      // See https://github.com/asciimath/asciimathml/blob/master/ASCIIMathML.js
      // Add functions, including some edX functions that don't exist in AsciiMath
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
    columnizeVectors: columnizeVectors,
    funcToPostfix: funcToPostfix
  }
}
