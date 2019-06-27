"""
Tests for StringGrader
"""
from pytest import raises
from mitxgraders import StringGrader
from mitxgraders.exceptions import ConfigError, InvalidInput

def test_strip():
    """Tests that strip is working correctly"""
    grader = StringGrader(answers="cat")
    assert grader(None, "cat")['ok']
    assert grader(None, "   cat   ")['ok']
    assert not grader(None, "c at")['ok']
    assert not grader(None, "  dog  ")['ok']

    grader = StringGrader(answers="         cat")
    assert grader(None, "cat")['ok']
    assert grader(None, "   cat   ")['ok']
    assert not grader(None, "c at")['ok']
    assert not grader(None, "  dog  ")['ok']

    grader = StringGrader(answers="cat", strip=False)
    assert grader(None, "cat")['ok']
    assert not grader(None, " cat")['ok']
    assert not grader(None, " cat ")['ok']
    assert not grader(None, "cat ")['ok']

    grader = StringGrader(answers=" cat", strip=False)
    assert not grader(None, "cat")['ok']
    assert grader(None, " cat")['ok']
    assert not grader(None, " cat ")['ok']
    assert not grader(None, "cat ")['ok']

    grader = StringGrader(answers=" cat", strip=True)
    assert grader(None, "cat")['ok']
    assert grader(None, " cat")['ok']
    assert grader(None, " cat ")['ok']
    assert grader(None, "cat ")['ok']

def test_case():
    """Tests that case is working correctly"""
    grader = StringGrader(answers="cat", case_sensitive=True)
    assert grader(None, "cat")['ok']
    assert not grader(None, "Cat")['ok']
    assert not grader(None, "CAT")['ok']

    grader = StringGrader(answers="Cat", case_sensitive=True)
    assert not grader(None, "cat")['ok']
    assert grader(None, "Cat")['ok']
    assert not grader(None, "CAT")['ok']

    grader = StringGrader(answers="CAT", case_sensitive=True)
    assert not grader(None, "cat")['ok']
    assert not grader(None, "Cat")['ok']
    assert grader(None, "CAT")['ok']

def test_any():
    """Tests that accept_any is working correctly"""
    grader = StringGrader(accept_any=True)
    assert grader(None, "cat")['ok']
    assert grader(None, "dog")['ok']
    assert grader(None, "")['ok']
    assert grader(None, " ")['ok']

def test_nonempty():
    """Tests that accept_nonempty is working correctly"""
    grader = StringGrader(accept_nonempty=True, explain_minimums='msg')
    assert grader(None, "cat")['ok']
    assert grader(None, "dog")['ok']
    assert not grader(None, "")['ok']
    assert not grader(None, " ")['ok']

def test_docs():
    """Test that the documentation examples work as intended"""
    # Opening example
    grader = StringGrader(
        answers='cat'
    )
    assert grader(None, 'cat')['ok']
    assert not grader(None, 'Cat')['ok']
    assert not grader(None, 'CAT')['ok']

    # Case sensitive
    grader = StringGrader(
        answers='Cat',
        case_sensitive=False
    )
    assert grader(None, 'cat')['ok']
    assert grader(None, 'Cat')['ok']
    assert grader(None, 'CAT')['ok']

    # Strip
    grader = StringGrader(
        answers=' cat',
        strip=False
    )
    assert not grader(None, 'cat')['ok']
    assert grader(None, ' cat')['ok']
    assert not grader(None, ' cat ')['ok']
    assert not grader(None, 'cat ')['ok']

def test_clean():
    """Test that StringGrader.clean_input works as intended"""
    teststring = "  Hello  there! "

    grader = StringGrader(case_sensitive=True,
                          strip=False,
                          strip_all=False,
                          clean_spaces=False)
    assert grader.clean_input(teststring) == teststring

    grader = StringGrader(case_sensitive=False,
                          strip=False,
                          strip_all=False,
                          clean_spaces=False)
    assert grader.clean_input(teststring) == teststring.lower()

    grader = StringGrader(case_sensitive=True,
                          strip=True,
                          strip_all=False,
                          clean_spaces=False)
    assert grader.clean_input(teststring) == teststring.strip()

    grader = StringGrader(case_sensitive=True,
                          strip=False,
                          strip_all=True,
                          clean_spaces=False)
    assert grader.clean_input(teststring) == "Hellothere!"

    grader = StringGrader(case_sensitive=True,
                          strip=False,
                          strip_all=False,
                          clean_spaces=True)
    assert grader.clean_input(teststring) == " Hello there! "

    grader = StringGrader(case_sensitive=True,
                          strip=True,
                          strip_all=False,
                          clean_spaces=True)
    assert grader.clean_input(teststring) == "Hello there!"

def test_min_length():
    """Make sure that minimum lengths are graded correctly"""
    grader = StringGrader(accept_any=True, min_length=2, explain_minimums='err')
    assert grader(None, 'cat')['ok']
    msg = r'Your response is too short \(1/2 characters\)'
    with raises(InvalidInput, match=msg):
        grader(None, 'c')

    grader = StringGrader(accept_any=True, min_length=2, explain_minimums='msg')
    assert grader(None, 'cat')['ok']
    assert grader(None, 'c') == {'ok': False,
                                 'grade_decimal': 0,
                                 'msg': 'Your response is too short (1/2 characters)'}

    grader = StringGrader(accept_any=True, min_length=2, explain_minimums=None)
    assert grader(None, 'c') == {'ok': False, 'grade_decimal': 0, 'msg': ''}

def test_min_words():
    """Make sure that minimum wordcounts are graded correctly"""
    grader = StringGrader(accept_any=True, min_words=3, explain_minimums='err')
    assert grader(None, 'cat in the hat')['ok']
    msg = r'Your response is too short \(2/3 words\)'
    with raises(InvalidInput, match=msg):
        grader(None, 'A cat')

    grader = StringGrader(accept_any=True, min_words=3, explain_minimums='msg')
    assert grader(None, 'cat in the hat')['ok']
    assert grader(None, 'A cat') == {'ok': False,
                                     'grade_decimal': 0,
                                     'msg': 'Your response is too short (2/3 words)'}

    grader = StringGrader(accept_any=True, min_words=3, explain_minimums=None)
    assert grader(None, 'A cat') == {'ok': False, 'grade_decimal': 0, 'msg': ''}

def test_validation():
    """Make sure that validation works correctly"""
    grader = StringGrader(accept_any=True,
                          validation_pattern=r"\([0-9]+\)",
                          explain_validation=None,
                          debug=False)
    assert grader(None, '1') == {'ok': False, 'grade_decimal': 0, 'msg': ''}
    assert grader(None, '(1234566542)')['ok']

    grader = StringGrader(accept_any=True,
                          validation_pattern=r"\([0-9]+\)",
                          explain_validation=None,
                          debug=True)
    assert not grader(None, '1')['ok']
    assert 'Your input is not in the expected format' in grader(None, '1')['msg']
    assert grader(None, '(1234566542)')['ok']

    grader = StringGrader(accept_any=True,
                          validation_pattern=r"\([0-9]+\)",
                          explain_validation='msg',
                          debug=False)
    assert grader(None, '1') == {'ok': False, 'grade_decimal': 0, 'msg': 'Your input is not in the expected format'}
    assert grader(None, '(1234566542)')['ok']

    grader = StringGrader(accept_any=True,
                          validation_pattern=r"\([0-9]+\)",
                          explain_validation='err')
    expect = 'Your input is not in the expected format'
    with raises(InvalidInput, match=expect):
        grader(None, '1')
    assert grader(None, '(1234566542)')['ok']

    expect = 'Look! An elephant!'
    grader = StringGrader(accept_any=True,
                          validation_pattern=r"\([0-9]+\)",
                          explain_validation='err',
                          invalid_msg=expect)
    with raises(InvalidInput, match=expect):
        grader(None, '1')
    assert grader(None, '(1234566542)')['ok']

    grader = StringGrader(answers="(10)",
                          validation_pattern=r"\([0-9]+\)")
    assert not grader(None, '(1234566542)')['ok']
    assert grader(None, '(10)')['ok']
    expect = 'Your input is not in the expected format'
    with raises(InvalidInput, match=expect):
        grader(None, '1')

    grader = StringGrader(answers="10)",
                          validation_pattern=r"\([0-9]+\)")
    # Oh escaping hell...
    expect = r"The provided answer '10\)' does not match the validation pattern '\\\(\[0-9\]\+\\\)'"
    with raises(ConfigError, match=expect):
        grader(None, '1')
