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
    // Do nothing!
}
else {
    // Define the preprocessor
    window.MJxPrep = function() {
        /*-----------------------------------------------------
         *This is the preprocessor, used for translating inputs
         *-----------------------------------------------------
         */
        this.fn = function(eqn) {
            // Note that /pattern/flags is shorthand for a regex parser
            // g is global - makes all changes

            // log10(x) -> log_10(x)
            eqn = eqn.replace(/log10\(/g, 'log_10(');
            // log2(x) -> log_2(x)
            eqn = eqn.replace(/log2\(/g, 'log_2(');

            // Note that fact(x) renders as x!, while fact(n-1) renders as n-1! (not good!)
            // To make it look right, we need to use fact((n-1))
            // This means that fact(10) renders as (10)!, but that's pretty benign
            // Same applies to factorial
            var replace_fact = function(match, substr1, substr2) {
                if (substr2.length == 1)
                    return substr1 + '(' + substr2 + ')';
                else
                    return substr1 + '((' + substr2 + '))';
            };
            eqn = eqn.replace(/(fact|factorial)\((.+?)\)/g, replace_fact);

            return eqn;
        };
    }

    // Try to update AsciiMath
    var checkExist = setInterval(function() {
        if (MathJax.InputJax.AsciiMath) {
            // Grab the AsciiMath object
            AM = MathJax.InputJax.AsciiMath.AM;

            // Add functions, including some edX functions that don't exist in asciimath
            AM.newsymbol({input:"arcsec", tag:"mi", output:"arcsec", tex:null, ttype:AM.TOKEN.UNARY, func:true});
            AM.newsymbol({input:"arccsc", tag:"mi", output:"arccsc", tex:null, ttype:AM.TOKEN.UNARY, func:true});
            AM.newsymbol({input:"arccot", tag:"mi", output:"arccot", tex:null, ttype:AM.TOKEN.UNARY, func:true});
            AM.newsymbol({input:"arcsinh", tag:"mi", output:"arcsinh", tex:null, ttype:AM.TOKEN.UNARY, func:true});
            AM.newsymbol({input:"arccosh", tag:"mi", output:"arccosh", tex:null, ttype:AM.TOKEN.UNARY, func:true});
            AM.newsymbol({input:"arctanh", tag:"mi", output:"arctanh", tex:null, ttype:AM.TOKEN.UNARY, func:true});
            AM.newsymbol({input:"arcsech", tag:"mi", output:"arcsech", tex:null, ttype:AM.TOKEN.UNARY, func:true});
            AM.newsymbol({input:"arccsch", tag:"mi", output:"arccsch", tex:null, ttype:AM.TOKEN.UNARY, func:true});
            AM.newsymbol({input:"arccoth", tag:"mi", output:"arccoth", tex:null, ttype:AM.TOKEN.UNARY, func:true});
            AM.newsymbol({input:"re", tag:"mi", output:"Re", tex:null, ttype:AM.TOKEN.UNARY, func:true});
            AM.newsymbol({input:"im", tag:"mi", output:"Im", tex:null, ttype:AM.TOKEN.UNARY, func:true});
            AM.newsymbol({input:"conj", tag:"mi", output:"conj", tex:null, ttype:AM.TOKEN.UNARY, func:true});

            // Add special functions: fact and factorial
            AM.newsymbol({input:"fact", tag:"mo", output:"fact", tex:null, ttype:AM.TOKEN.UNARY, rewriteleftright:["","!"]});
            AM.newsymbol({input:"factorial", tag:"mo", output:"factorial", tex:null, ttype:AM.TOKEN.UNARY, rewriteleftright:["","!"]});

            // Ask MathJax to reprocess all input boxes, as saved answers may have rendered
            // before these definitions went through
            MathJax.Hub.Queue(["Reprocess", MathJax.Hub]);

            // No need to update again
            clearInterval(checkExist);
            console.log("MITx Grading Library: Updated MathJax AsciiMath definitions");
        }
    }, 200); // Check for the AsciiMath object every 200ms
}
