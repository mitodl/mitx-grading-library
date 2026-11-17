"""
Tests for the parts of scripts/course_assets.py that don't need Open edX
"""

import datetime
import importlib.util
import io
import subprocess
import zipfile

import pytest

from tests.test_zip import REPO_ROOT

spec = importlib.util.spec_from_file_location("course_assets", REPO_ROOT / "scripts" / "course_assets.py")
course_assets = importlib.util.module_from_spec(spec)
spec.loader.exec_module(course_assets)


def zip_bytes(files):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, text in files.items():
            archive.writestr(name, text)
    return buffer.getvalue()


def test_classify_ignores_whitespace():
    known = {course_assets.normalized_sha256(b"var a = 1;\n"): "v3.0.0"}
    assert course_assets.classify(b"var a = 1;\r\n", known) == ("stock", "v3.0.0")
    assert course_assets.classify(b"  var  a =\t1;", known) == ("stock", "v3.0.0")
    assert course_assets.classify(b"var a = 2;", known) == ("customized", "")
    assert course_assets.classify(b"var a = 2;", {}) == ("present", "")


@pytest.mark.parametrize("files, expected", [
    (
        {"mitxgraders/version.py": "__version__ = '3.0.0'\n", "voluptuous/__init__.py": ""},
        ("stock", "3.0.0", []),
    ),
    (
        {
            "mitxgraders/version.py": '__version__ = "2.4.1"\n',
            "voluptuous/__init__.py": "",
            "grader_lib/__init__.py": "",
            "newsubs.py": "",
            "__MACOSX/._newsubs.py": "",
            "__pycache__/x.pyc": "",
        },
        ("extras", "2.4.1", ["grader_lib", "newsubs.py"]),
    ),
    (
        {"python_lib/mitxgraders/version.py": "__version__ = '3.0.0'\n"},
        ("nested", "3.0.0", ["python_lib"]),
    ),
    ({"sketchresponse.py": ""}, ("no-mitxgraders", "", ["sketchresponse.py"])),
])
def test_inspect_zip(files, expected):
    assert course_assets.inspect_zip(zip_bytes(files)) == expected


def test_inspect_zip_unreadable():
    assert course_assets.inspect_zip(b"not a zip") == ("unreadable", "", [])


def test_inspect_file_uses_known_for_the_filename():
    known = {"MJxPrep.js": {course_assets.normalized_sha256(b"x"): "v3.1.0"}}
    assert course_assets.inspect_file("MJxPrep.js", b"x", known) == ("stock", "v3.1.0", [])
    assert course_assets.inspect_file("hotfix16.js", b"x", known) == ("present", "", [])


def test_course_scope():
    now = datetime.datetime(2026, 11, 17)
    day = datetime.timedelta(days=1)
    assert course_assets.course_scope(now + day, None, now) == "upcoming"
    assert course_assets.course_scope(now - day, None, now) == "active"
    assert course_assets.course_scope(now - day, now + day, now) == "active"
    assert course_assets.course_scope(None, None, now) == "active"
    assert course_assets.course_scope(now - 2 * day, now - day, now) == "archived"


def test_is_template():
    assert course_assets.is_template("course-v1:MITx+Template+2026_03_18")
    assert course_assets.is_template("course-v1:MITx+Template.PC.Firefox+2026_08_05")
    assert not course_assets.is_template("course-v1:MITxT+18.02.1x+3T2025")


def test_latest_template_runs():
    day = datetime.datetime(2026, 1, 1)
    runs = [
        ("course-v1:MITx+Template+2026_03_11", day.replace(month=3)),
        ("course-v1:MITx+Template+2026_03_18", day.replace(month=4)),
        ("course-v1:MITx+Template+undated", None),
        ("course-v1:MITx+Template.Mac+2025_01", day.replace(year=2025)),
        ("course-v1:MITxT+18.02.1x+3T2025", day.replace(month=9)),
    ]
    assert course_assets.latest_template_runs(runs) == {
        "course-v1:MITx+Template+2026_03_18",
        "course-v1:MITx+Template.Mac+2025_01",
    }


@pytest.mark.parametrize("current, expected", [
    (None, "absent"),
    ("new", "already-current"),
    ("old", "replace"),
    ("other", "not-allowlisted"),
])
def test_decide(current, expected):
    assert course_assets.decide(current, "new", {"old"}) == expected


def test_select_from_inventory():
    rows = [
        {"course_key": "a", "filename": "MJxPrep.js", "status": "stock", "sha256": "1"},
        {"course_key": "a", "filename": "python_lib.zip", "status": "stock", "sha256": "2"},
        {"course_key": "b", "filename": "MJxPrep.js", "status": "customized", "sha256": "3"},
        {"course_key": "c", "filename": "MJxPrep.js", "status": "stock", "sha256": "4"},
        {"course_key": "d", "filename": "MJxPrep.js", "status": "absent", "sha256": ""},
    ]
    assert course_assets.select_from_inventory(rows, "MJxPrep.js", {"stock"}) == (["a", "c"], {"1", "4"})


def git(repo, *args):
    subprocess.run(
        ["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@example.com",
         "-c", "commit.gpgsign=false", "-c", "tag.gpgsign=false", *args],
        check=True, capture_output=True,
    )


def test_known_from_git_labels_versions_by_first_release(tmp_path):
    git(tmp_path, "init", "-q")
    (tmp_path / "MJxPrep.js").write_text("one")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-q", "-m", "one")
    git(tmp_path, "tag", "-a", "v1", "-m", "v1")
    (tmp_path / "MJxPrep.js").write_text("two")
    git(tmp_path, "commit", "-q", "-am", "two")
    (tmp_path / "MJxPrep.js").write_text("three")
    git(tmp_path, "commit", "-q", "-am", "three")
    git(tmp_path, "tag", "-a", "v2", "-m", "v2")

    labels = course_assets.known_from_git(tmp_path)["MJxPrep.js"]
    assert labels[course_assets.normalized_sha256(b"one")] == "v1"
    assert labels[course_assets.normalized_sha256(b"three")] == "v2"
    # Committed between releases
    assert labels[course_assets.normalized_sha256(b"two")].endswith(")")
    assert len(labels) == 3


def test_known_from_git_needs_history(tmp_path):
    git(tmp_path, "init", "-q")
    (tmp_path / "README").write_text("")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-q", "-m", "init")
    with pytest.raises(ValueError, match="full clone"):
        course_assets.known_from_git(tmp_path)


def test_main_replace_needs_courses_and_hashes(tmp_path):
    replacement = tmp_path / "MJxPrep.js"
    replacement.write_text("x")
    with pytest.raises(SystemExit):
        course_assets.main(["replace", "--filename", "MJxPrep.js", "--replacement", str(replacement),
                            "--allow", "abc"])
    with pytest.raises(SystemExit):
        course_assets.main(["replace", "--filename", "MJxPrep.js", "--replacement", str(replacement),
                            "--course", "course-v1:a+b+c"])
