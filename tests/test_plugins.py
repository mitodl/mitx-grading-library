"""
Tests that the plugin implementation is functioning
"""
from mitxgraders import *

def test_plugins():
    """
    Tests that the functions loaded with the template can be accessed
    in all the appropriate ways
    """
    assert plugins.template.plugin_test() == True
    assert plugin_test() == True
