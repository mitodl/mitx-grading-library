"""
Tests that python_lib.zip loads correctly
"""

import pytest

@pytest.fixture(scope="module")
def loadzip():
    """pytest fixture to dynamically load the library from python_lib.zip"""
    # Add python_lib.zip to the path for searching for modules
    import sys
    sys.path.insert(0, 'python_lib.zip')
    # The 0 tells it to search this zip file before even the module directory
    # Hence,
    import mitxgraders
    # loads mitxgraders from the zip file
    # Now, provide the zipfile library to our test functions
    yield mitxgraders
    # Before resuming, fix the system path
    del sys.path[0]

def test_zipfile(loadzip):
    """Test that the plugins have loaded properly from the zip file"""
    grader = loadzip.StringGrader(answers="hello")
    expect = {'grade_decimal': 1, 'msg': '', 'ok': True}
    assert grader(None, "hello") == expect
    assert loadzip.plugins.template.plugin_test()
    assert loadzip.plugin_test()
