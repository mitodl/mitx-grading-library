"""
Tests for StringGrader
"""
from graders import StringGrader

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
