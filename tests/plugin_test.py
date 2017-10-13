"""
Tests that the plugin implementation is functioning
"""
from graders import *

def test_plugins():
    """
    Tests that the functions loaded with the template can be accessed
    in all the appropriate ways
    """
    assert plugins.template.can_be_called() == True
    assert can_be_called() == True
