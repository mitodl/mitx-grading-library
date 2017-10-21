"""
Tests that python_lib.zip will load correctly
"""

# Add python_lib.zip to the path for searching for modules
import sys
sys.path.insert(0, 'python_lib.zip')
# The 0 tells it to search this zip file before even the module directory
# Hence,
from graders import *
# loads graders from the zip file

def test_loaded():
    """Tests that the library has loaded correctly"""
    grader = StringGrader(answers="hello")
    expect = {'grade_decimal': 1, 'msg': '', 'ok': True}
    assert grader(None, "hello") == expect

def test_plugins():
    """Test that the plugins have loaded properly"""
    assert plugins.template.plugin_test() == True
    assert plugin_test() == True
