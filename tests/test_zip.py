"""
Tests that python_lib.zip loads correctly
"""



import importlib.util
import sys
from importlib import reload
from pathlib import Path

import pytest
import mitxgraders

REPO_ROOT = Path(__file__).resolve().parent.parent


def load_python_lib_zip_script():
    """Import scripts/python_lib_zip.py, which isn't in a package"""
    spec = importlib.util.spec_from_file_location(
        "python_lib_zip", REPO_ROOT / "scripts" / "python_lib_zip.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def loadzip(tmp_path, monkeypatch):
    """pytest fixture to dynamically load the library from a freshly built python_lib.zip"""
    zip_path = tmp_path / "python_lib.zip"
    load_python_lib_zip_script().build(zip_path, REPO_ROOT)
    # mitxgraders reads its plugins from 'python_lib.zip' in the working
    # directory, as it does on edX
    monkeypatch.chdir(tmp_path)
    # Add python_lib.zip to the path for searching for modules
    sys.path.insert(0, str(zip_path))
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
