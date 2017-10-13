"""
This is a template file that also is used to test that the plugin loading
mechanism is working.
"""

# Make sure that imports are working
from graders.baseclasses import ItemGrader

def can_be_called():
    """Function is designed to be called as part of a test suite"""
    return True

# Allow the function to be imported with *
__all__ = ["can_be_called"]
