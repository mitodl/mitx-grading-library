"""
Tests that python_lib.zip loads correctly
"""

import os
import pytest
import mitxgraders

@pytest.fixture()
def loadzip():
    """pytest fixture to dynamically load the library from python_lib.zip"""
    # Add python_lib.zip to the path for searching for modules
    import sys
    sys.path.insert(0, '/Users/jolyon/gitrepos/mitx-graders/mitx-graders/python_lib.zip')
    # The 0 tells it to search this zip file before even the module directory
    # Hence,
    reload(mitxgraders)
    # loads mitxgraders from the zip file
    # Now, provide the zipfile library to our test functions
    yield mitxgraders
    # Before resuming, fix the system path
    del sys.path[0]
    # And restore the old version of the library
    reload(mitxgraders)

@pytest.mark.skipif("TRAVIS" in os.environ and os.environ["TRAVIS"] == "true",
                    reason="Skipping this test on Travis CI.")
def test_zipfile(loadzip):
    """Test that the plugins have loaded properly from the zip file"""
    # Make sure that we have the zip file
    assert loadzip.loaded_from == "python_lib.zip"
    grader = loadzip.StringGrader(answers="hello")
    expect = {'grade_decimal': 1, 'msg': '', 'ok': True}
    assert grader(None, "hello") == expect
    assert loadzip.plugins.template.plugin_test()
    assert loadzip.plugin_test()

def test_notzipfile():
    """Test that the mitxgraders library loads normally"""
    assert mitxgraders.loaded_from == "mitxgraders directory"
