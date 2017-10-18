"""
Graders package
Version 0.2.0

An edX python grading library

Copyright 2017 Jolyon Bloomfield and Chris Chudzicki
"""
# All modules defining grading classes must set __all__ to specify
# which classes are imported with the package
from graders.stringgrader import *
from graders.listgrader import *
from graders.formulagrader import *
from graders.baseclasses import ConfigError

def import_plugins():
    """Imports all plugins into the global namespace"""
    import os
    import importlib

    # Get the list of all plugin files
    my_dir = os.path.dirname(os.path.realpath(__file__))
    plugin_dir = os.path.join(my_dir, "plugins")
    plugin_files = [
        x[:-3]
        for x in os.listdir(plugin_dir)
        if x.endswith(".py") and not x.startswith("_")
    ]

    # Import all plugins
    for plugin in plugin_files:
        # Import the module into the namespace
        mod = importlib.import_module(__name__ + ".plugins." + plugin)
        # Add everything listed in plugin.__all__ to the global namespace
        # for this package
        if hasattr(mod, "__all__"):
            globals().update({name: mod.__dict__[name] for name in mod.__all__})

# Import all the plugins and clean up the evidence
import_plugins()
del import_plugins
