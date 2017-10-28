"""
This is a template file that also is used to test that the plugin loading
mechanism is working.
"""

# Make sure that imports are working
from mitxgraders.baseclasses import ItemGrader

def plugin_test():
    """Function is designed to be called as part of a test suite"""
    return True

# Allow the function to be imported with *
__all__ = ["plugin_test"]
