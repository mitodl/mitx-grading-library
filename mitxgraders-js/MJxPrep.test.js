// Hacky imports since we aren't transpiling
require("./MJxPrep.js")
const {
  findClosingBrace,
  replaceFunctionCalls,
  groupExpr
} = window.MJxPrepExports

describe('findClosingBrace', () => {
  it('finds the closing brace', () => {
    //                  01234567890123456789012345678901234567890123456789
    const expression = '4 + ( sin( 3^(1) - 7^2 ) + 5 ) + exp(8 - (4*3) )'
    const startIdx = 4
    expect(findClosingBrace(expression, startIdx)).toBe(29)
  } )

  it('throws an error if no opening brace at specified location', () => {
    //                  0123456789
    const expression = '4 + sin(x)'
    const startIdx = 2
    const badfunc = () => findClosingBrace(expression, startIdx)
    expect(badfunc).toThrow(
      `${expression} does not contain an opening brace at position ${startIdx}.`
    )
  } )

  it('throws an error if brace opens but does not close', () => {
    //                  012345678901234
    const expression = '4 + sin( e^(2t)'
    const startIdx = 7
    const badfunc = () => findClosingBrace(expression, startIdx)
    expect(badfunc).toThrow(
      `${expression} has a brace that opens at position ${startIdx} but does not close.`
    )
  } )

} )

describe('replaceFunctionCalls', () => {
  it('detects arguments', () => {
    const expr = "1 + cat(2, 3 + cat(1) +1 ) + 4*cat(2,3,4)"

    const action = (funcName, args) => `${funcName.toUpperCase()}(${args})`
    const result = replaceFunctionCalls(expr, 'cat', action)
    expect(result).toBe('1 + CAT(2, 3 + CAT(1) +1 ) + 4*CAT(2,3,4)')
  } )
} )
