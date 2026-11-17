"""
Tests for scripts/python_lib_zip.py, which builds the release python_lib.zip
and updates the library inside a course's python_lib.zip
"""

import zipfile

import pytest

from mitxgraders.version import __version__
from tests.helpers import zip_bytes
from tests.test_zip import REPO_ROOT, load_python_lib_zip_script

python_lib_zip = load_python_lib_zip_script()


def make_zip(path, files):
    path.write_bytes(zip_bytes(files))
    return path


def test_build_has_the_library_at_the_top_level_and_nothing_else(tmp_path):
    names = python_lib_zip.build(tmp_path / "python_lib.zip", REPO_ROOT)
    assert {name.split("/", 1)[0] for name in names} == {"mitxgraders", "voluptuous"}
    assert "mitxgraders/LICENSE" in names
    assert "mitxgraders/plugins/template.py" in names
    assert not [name for name in names if "__pycache__" in name or name.endswith(".pyc")]
    with zipfile.ZipFile(tmp_path / "python_lib.zip") as archive:
        assert archive.namelist() == names


def test_build_is_reproducible(tmp_path):
    python_lib_zip.build(tmp_path / "a.zip", REPO_ROOT)
    python_lib_zip.build(tmp_path / "b.zip", REPO_ROOT)
    assert (tmp_path / "a.zip").read_bytes() == (tmp_path / "b.zip").read_bytes()


def test_update_keeps_the_course_modules_and_replaces_the_library(tmp_path):
    release = tmp_path / "release.zip"
    python_lib_zip.build(release, REPO_ROOT)
    course = make_zip(tmp_path / "course.zip", {
        "mitxgraders/version.py": '__version__ = "2.2.0"\n',
        "mitxgraders/removed_since.py": "",
        "mitxgraders/plugins/template.py": "# edited copy of a library plugin\n",
        "mitxgraders/plugins/defaults.py": "# the course's own plugin\n",
        "voluptuous/old.py": "",
        "sigfigs.py": "SIGFIGS = 3\n",
        "grader_lib/__init__.py": "",
        # A namespace package: on Python 3.11/3.12 zipimport needs the
        # directory entry to find it
        "nslib/": "",
        "nslib/helpers.py": "",
        # macOS Finder's Compress adds these
        "__MACOSX/mitxgraders/._version.py": "",
    })

    old, new, kept, replaced = python_lib_zip.update(course, release, tmp_path / "updated.zip")

    assert (old, new) == ("2.2.0", __version__)
    assert kept == ["grader_lib", "nslib", "sigfigs.py", "mitxgraders/plugins/defaults.py"]
    assert replaced == ["mitxgraders/plugins/template.py"]
    with zipfile.ZipFile(tmp_path / "updated.zip") as updated, zipfile.ZipFile(release) as built:
        names = set(updated.namelist())
        assert names == set(built.namelist()) | {
            "sigfigs.py", "grader_lib/__init__.py", "nslib/", "nslib/helpers.py",
            "mitxgraders/plugins/defaults.py",
        }
        assert updated.read("sigfigs.py") == b"SIGFIGS = 3\n"
        assert updated.read("mitxgraders/plugins/defaults.py") == b"# the course's own plugin\n"
        assert updated.read("mitxgraders/version.py") == built.read("mitxgraders/version.py")
        assert updated.read("mitxgraders/plugins/template.py") == built.read("mitxgraders/plugins/template.py")


def test_update_rejects_a_zip_of_the_folder_instead_of_its_contents(tmp_path):
    release = tmp_path / "release.zip"
    python_lib_zip.build(release, REPO_ROOT)
    course = make_zip(tmp_path / "course.zip", {"python_lib/mitxgraders/__init__.py": ""})
    with pytest.raises(ValueError, match="zip the folder's contents, not the folder"):
        python_lib_zip.update(course, release, tmp_path / "updated.zip")
    assert not (tmp_path / "updated.zip").exists()


def test_update_cli_refuses_to_overwrite_an_input(tmp_path, monkeypatch, capsys):
    release = tmp_path / "python_lib.zip"
    python_lib_zip.build(release, REPO_ROOT)
    make_zip(tmp_path / "course.zip", {"sigfigs.py": ""})
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        python_lib_zip.main(["update", "course.zip", "-o", "course.zip"])
    assert "--output must be a new file" in capsys.readouterr().err
