"""
MITx Grading Library
https://github.com/mitodl/mitx-grading-library
Copyright (c) 2017-2018 Jolyon Bloomfield and Chris Chudzicki
All Rights Reserved

See version.py for version number

An edX python grading library
"""

# Add the current version
from mitxgraders.version import __version__

# Add voluptuous
try:
    import voluptuous
except ImportError:
    raise ImportError("External dependency 'voluptuous' not found;"
                      " see https://github.com/mitodl/mitx-grading-library#faq")

# All modules defining grading classes must set __all__ to specify
# which classes are imported with the package
from mitxgraders.stringgrader import *
from mitxgraders.listgrader import *
from mitxgraders.formulagrader import *
from mitxgraders.sampling import *
from mitxgraders.exceptions import ConfigError, StudentFacingError
from mitxgraders.helpers.calc import *

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

    globals().update({'loaded_from': "mitxgraders directory"})


def import_zip_plugins():  # pragma: no cover
    """Imports all plugins from python_lib.zip into the global namespace"""
    import os
    import importlib
    import zipfile

    # Find all of the plugins in python_lib.zip
    with zipfile.ZipFile('python_lib.zip', 'r') as myzip:
        file_list = myzip.namelist()
        plugins = [
            file[:-3] for file in file_list
            if file.startswith("mitxgraders/plugins/")
            and file.endswith(".py")
            and not file.endswith("__init__.py")
        ]

    # Turn the plugin names into module names
    # Eg, "graders/plugins/template" becomes "graders.plugins.template"
    plugin_names = [plugin.replace("/", ".") for plugin in plugins]

    # Import all plugins
    for plugin in plugin_names:
        # Import the module into the namespace
        mod = importlib.import_module(plugin)
        # Add everything listed in plugin.__all__ to the global namespace
        # for this package
        if hasattr(mod, "__all__"):
            globals().update({name: mod.__dict__[name] for name in mod.__all__})

    globals().update({'loaded_from': "python_lib.zip"})


# Import all the plugins
if "python_lib.zip" in __file__:
    # If this package is inside python_lib.zip, we need to work a little differently
    import_zip_plugins()  # pragma: no cover
else:
    import_plugins()

# Clean up the namespace
del import_plugins, import_zip_plugins
