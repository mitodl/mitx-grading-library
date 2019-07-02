"""
Tests that python_lib.zip loads correctly
"""
from __future__ import print_function, division, absolute_import


import os
import pytest
import mitxgraders

try:
    # for Python 3
    from importlib import reload
except ImportError:
    # reload is builtin in Python 2
    pass

@pytest.fixture()
def loadzip():
    """pytest fixture to dynamically load the library from python_lib.zip"""
    # Add python_lib.zip to the path for searching for modules
    import sys
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    zip_path = os.path.join(parent_dir, 'python_lib.zip')
    sys.path.insert(0, zip_path)
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
