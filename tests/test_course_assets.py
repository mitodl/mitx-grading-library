"""
Tests for the parts of scripts/course_assets.py that don't need Open edX
"""

import csv
import datetime
import importlib.util
import io
import subprocess
import types
from pathlib import Path

import pytest

from tests.helpers import zip_bytes
from tests.test_zip import REPO_ROOT

spec = importlib.util.spec_from_file_location("course_assets", REPO_ROOT / "scripts" / "course_assets.py")
course_assets = importlib.util.module_from_spec(spec)
spec.loader.exec_module(course_assets)



def test_classify_ignores_line_formatting():
    known = {course_assets.normalized_sha256(b"function f() {\n  return 'a b';\n}\n"): "v3.0.0"}
    for copy in (
        b"function f() {\r\n  return 'a b';\r\n}\r\n",  # CRLF
        b"\nfunction f() {  \n\treturn 'a b';\n\n}",  # indentation, trailing and blank lines
    ):
        assert course_assets.classify(copy, known) == ("stock", "v3.0.0")
    assert course_assets.classify(b"function f() {\n  return 'a c';\n}\n", known) == ("customized", "")
    assert course_assets.classify(b"x", {}) == ("present", "")


def test_classify_keeps_whitespace_inside_a_line():
    # e.g. the 18.02 fork's working.replace(/\[/g,'langle ') is a real customization
    known = {course_assets.normalized_sha256(b"x = s.replace(/a/g, 'langle');\n"): "v3.0.0"}
    assert course_assets.classify(b"x = s.replace(/a/g, 'langle ');\n", known) == ("customized", "")
    assert course_assets.classify(b"x = s.replace(/a /g, 'langle');\n", known) == ("customized", "")


@pytest.mark.parametrize("source, expected", [
    (b"var a = 'x';\nvar b = 2;\n", False),
    (b"var a = `x\n  y`;\n", True),
    (b"var a = 'x \\\n  y';\n", True),
    (b"var a = 'x \\\r\n  y';\n", True),
    (b"var a = /\\\\/;\n", False),
])
def test_spans_lines(source, expected):
    assert course_assets.spans_lines(source) == expected


@pytest.mark.parametrize("files, expected", [
    (
        {"mitxgraders/version.py": "__version__ = '3.0.0'\n", "voluptuous/__init__.py": ""},
        ("library-only", "3.0.0", []),
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
        ("course-v1:MITx+Template+2025_01", day.replace(year=2025)),
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
    # The repository keeps symlinks to the root file in other folders
    (tmp_path / "course" / "static").mkdir(parents=True)
    (tmp_path / "course" / "static" / "MJxPrep.js").symlink_to("../../MJxPrep.js")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-q", "-m", "three")
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
    with pytest.raises(ValueError, match="No history"):
        course_assets.known_from_git(tmp_path)
    shallow = tmp_path / "shallow"
    subprocess.run(["git", "clone", "-q", "--depth", "1", f"file://{tmp_path}", str(shallow)],
                   check=True, capture_output=True)
    with pytest.raises(ValueError, match="shallow"):
        course_assets.known_from_git(shallow)


def test_read_hashes():
    text = "ABC123  MJxPrep.js\n\ndef456\n"
    assert course_assets.read_hashes(text) == {"abc123", "def456"}


def test_main_replace_needs_courses_and_hashes(tmp_path):
    replacement = tmp_path / "MJxPrep.js"
    replacement.write_text("x")
    with pytest.raises(SystemExit):
        course_assets.main(["replace", "--filename", "MJxPrep.js", "--replacement", str(replacement),
                            "--allow", "abc"])
    with pytest.raises(SystemExit):
        course_assets.main(["replace", "--filename", "MJxPrep.js", "--replacement", str(replacement),
                            "--course", "course-v1:a+b+c"])


def test_main_replace_refuses_a_mismatched_replacement(tmp_path):
    replacement = tmp_path / "python_lib.zip"
    replacement.write_bytes(zip_bytes({"mitxgraders/version.py": ""}))
    with pytest.raises(SystemExit):
        course_assets.main(["replace", "--filename", "MJxPrep.js", "--replacement", str(replacement),
                            "--allow", "abc", "--course", "course-v1:a+b+c"])


class FakeStore:
    """Stands in for StudioStore: assets in a dict, courses in a set."""

    def __init__(self, assets, courses=None, fail_writes=0):
        self.assets = dict(assets)
        self.courses = set(courses if courses is not None else (key for key, __ in assets))
        self.fail_writes = fail_writes
        self.writes = []
        self.cleared = []

    def parse(self, key):
        if not key.startswith("course-v1:"):
            raise ValueError(key)
        return key

    def has_course(self, course_key):
        return course_key in self.courses

    def find(self, course_key, filename):
        data = self.assets.get((course_key, filename))
        return None if data is None else types.SimpleNamespace(data=data, locked=False)

    def write(self, course_key, filename, current, data):
        self.writes.append((course_key, data))
        if self.fail_writes:
            self.fail_writes -= 1
            # As MongoContentStore.save does, the old file is gone before the write fails
            self.assets.pop((course_key, filename), None)
            raise OSError("write failed")
        self.assets[(course_key, filename)] = data

    def clear_cache(self, course_key, filename):
        self.cleared.append(course_key)


def run_replace(store, tmp_path, course_keys, allowed, dry_run=False):
    out = io.StringIO()
    writer = csv.DictWriter(out, course_assets.REPORT_FIELDS)
    writer.writeheader()
    try:
        counts = course_assets.run_replace(store, writer, "MJxPrep.js", b"new", course_keys, allowed,
                                           dry_run, tmp_path / "backups")
    finally:
        rows = list(csv.DictReader(io.StringIO(out.getvalue())))
    return counts, {row["course_key"]: row for row in rows}


OLD = course_assets.sha256(b"old")
NEW = course_assets.sha256(b"new")
ASSETS = {
    ("course-v1:a+stock+1", "MJxPrep.js"): b"old",
    ("course-v1:a+custom+1", "MJxPrep.js"): b"custom",
    ("course-v1:a+current+1", "MJxPrep.js"): b"new",
}
KEYS = ["course-v1:a+stock+1", "course-v1:a+custom+1", "course-v1:a+current+1",
        "course-v1:a+empty+1", "course-v1:a+gone+1"]


def test_run_replace_only_writes_allowlisted_copies(tmp_path):
    store = FakeStore(ASSETS, courses=[*(key for key, __ in ASSETS), "course-v1:a+empty+1"])
    counts, rows = run_replace(store, tmp_path, KEYS, {OLD})

    assert store.writes == [("course-v1:a+stock+1", b"new")]
    assert store.assets[("course-v1:a+custom+1", "MJxPrep.js")] == b"custom"
    assert {key: row["action"] for key, row in rows.items()} == {
        "course-v1:a+stock+1": "replaced",
        "course-v1:a+custom+1": "not-allowlisted",
        "course-v1:a+current+1": "already-current",
        "course-v1:a+empty+1": "absent",
        "course-v1:a+gone+1": "no-course",
    }
    assert counts["replaced"] == 1
    backup = Path(rows["course-v1:a+stock+1"]["backup"])
    assert backup.read_bytes() == b"old"
    assert OLD[:16] in backup.name
    assert rows["course-v1:a+stock+1"]["old_sha256"] == OLD
    # After the write, and again at the end of the run
    assert store.cleared == ["course-v1:a+stock+1", "course-v1:a+stock+1"]


def test_run_replace_dry_run_writes_nothing(tmp_path):
    store = FakeStore(ASSETS)
    counts, rows = run_replace(store, tmp_path, KEYS[:3], {OLD}, dry_run=True)
    assert store.writes == []
    assert rows["course-v1:a+stock+1"]["action"] == "would-replace"
    assert not (tmp_path / "backups").exists()


def test_run_replace_keeps_an_existing_backup(tmp_path):
    store = FakeStore(ASSETS)
    run_replace(store, tmp_path, ["course-v1:a+stock+1"], {OLD})
    # Roll back, then replace again: the first backup must survive
    store.assets[("course-v1:a+stock+1", "MJxPrep.js")] = b"old"
    __, rows = run_replace(store, tmp_path, ["course-v1:a+stock+1"], {OLD})
    assert Path(rows["course-v1:a+stock+1"]["backup"]).read_bytes() == b"old"
    assert len(list((tmp_path / "backups").iterdir())) == 1


def report_rows(store, tmp_path, course_keys, allowed):
    out = io.StringIO()
    writer = csv.DictWriter(out, course_assets.REPORT_FIELDS)
    with pytest.raises(OSError):
        course_assets.run_replace(store, writer, "MJxPrep.js", b"new", course_keys, allowed,
                                  False, tmp_path / "backups")
    return list(csv.DictReader(io.StringIO(out.getvalue()), course_assets.REPORT_FIELDS))


def test_run_replace_restores_the_old_copy_when_a_write_fails(tmp_path):
    assets = {**ASSETS, ("course-v1:a+stock+2", "MJxPrep.js"): b"old"}
    store = FakeStore(assets, fail_writes=1)
    rows = report_rows(store, tmp_path, ["course-v1:a+stock+1", "course-v1:a+stock+2"], {OLD})

    assert store.assets[("course-v1:a+stock+1", "MJxPrep.js")] == b"old"
    assert [row["action"] for row in rows] == ["failed", "restored"]
    assert Path(rows[0]["backup"]).read_bytes() == b"old"
    # Stopped before the second course, though it was allowed too
    assert store.assets[("course-v1:a+stock+2", "MJxPrep.js")] == b"old"
    assert [key for key, __ in store.writes] == ["course-v1:a+stock+1", "course-v1:a+stock+1"]


def test_run_replace_reports_a_failed_restore(tmp_path):
    store = FakeStore(ASSETS, fail_writes=2)
    rows = report_rows(store, tmp_path, ["course-v1:a+stock+1"], {OLD})
    # The asset is gone, but the report says so and names the backup
    assert [row["action"] for row in rows] == ["failed"]
    assert Path(rows[0]["backup"]).read_bytes() == b"old"


def test_run_replace_replaces_a_truncated_backup(tmp_path):
    backup = course_assets.backup_path(tmp_path / "backups", "course-v1:a+stock+1", "MJxPrep.js", OLD)
    backup.parent.mkdir()
    backup.write_bytes(b"ol")
    run_replace(FakeStore(ASSETS), tmp_path, ["course-v1:a+stock+1"], {OLD})
    assert backup.read_bytes() == b"old"


def test_inspect_zip_survives_damaged_zips():
    data = zip_bytes({"mitxgraders/version.py": "__version__ = '3.0.0'\n", "voluptuous/__init__.py": ""})
    for cut in range(len(data)):
        course_assets.inspect_zip(data[:cut])
    for i in range(len(data)):
        course_assets.inspect_zip(data[:i] + bytes([data[i] ^ 0xFF]) + data[i + 1:])


def test_run_replace_checks_every_key_before_writing(tmp_path):
    store = FakeStore(ASSETS)
    with pytest.raises(ValueError):
        run_replace(store, tmp_path, ["course-v1:a+stock+1", "typo"], {OLD})
    assert store.writes == []


def test_run_inventory_rows_feed_replace(tmp_path):
    known = {"MJxPrep.js": {course_assets.normalized_sha256(b"old"): "v2.3.1"}}
    store = FakeStore(ASSETS)
    out = io.StringIO()
    writer = csv.DictWriter(out, course_assets.INVENTORY_FIELDS)
    writer.writeheader()
    runs = [(key, {"scope": "active"}) for key in KEYS[:4]]
    rows = course_assets.run_inventory(store, writer, runs, ["MJxPrep.js"], known,
                                       {"course-v1:a+stock+1": 2})
    assert rows == 4
    inventory = list(csv.DictReader(io.StringIO(out.getvalue())))
    assert [(row["status"], row["version"]) for row in inventory] == [
        ("stock", "v2.3.1"), ("customized", ""), ("customized", ""), ("absent", ""),
    ]
    assert inventory[0]["reruns"] == "2"
    assert course_assets.select_from_inventory(inventory, "MJxPrep.js", {"stock"}) == (
        ["course-v1:a+stock+1"], {OLD},
    )
