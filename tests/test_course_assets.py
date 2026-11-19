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


def test_repo_name():
    assert course_assets.repo_name("git@github.mit.edu:mitxonline/MITx-6.00x-1T2026.git") == "MITx-6.00x-1T2026"
    assert course_assets.repo_name("https://github.com/mitx/content-devops-0001") == "content-devops-0001"
    assert course_assets.repo_name("git@host:repo.git") == "repo"


def test_parse_git_import():
    # The git_log edx-sysadmin's git_import.add_repo saves
    git_log = "Cloning into 'content-devops-0001'...\nCommit ID: abc123\n   \nBranch: live\n"
    value = course_assets.format_git_import(datetime.datetime(2021, 9, 1, 19, 56), "content-devops-0001", git_log)
    assert value == "2021-09-01 content-devops-0001@live"
    assert course_assets.parse_git_import(value) == ("content-devops-0001", "live")
    assert course_assets.format_git_import(None, "repo", None) == " repo@"
    assert course_assets.parse_git_import(" repo@") == ("repo", "")
    assert course_assets.parse_git_import("") == ("", "")


def inventory_row(course_key, status="stock", git_repo="", git_import=""):
    return {"course_key": course_key, "filename": "MJxPrep.js", "status": status, "sha256": OLD,
            "git_repo": git_repo, "git_import": git_import}


def test_git_targets():
    rows = [
        # Imported from its own export repo
        inventory_row("course-v1:a+same+1", git_repo="git@h:o/a-same-1.git", git_import="2026-01-01 a-same-1@live"),
        # Imported from a repository elsewhere, which edx-sysadmin records only by name
        inventory_row("course-v1:a+other+1", git_repo="git@h:o/a-other-1.git", git_import="2026-01-01 content@master"),
        inventory_row("course-v1:a+export+1", git_repo="git@h:o/a-export-1.git"),
        inventory_row("course-v1:a+studio+1"),
        inventory_row("course-v1:a+custom+1", status="customized", git_import="2026-01-01 custom@live"),
    ]
    assert course_assets.git_targets(rows, "MJxPrep.js", {"stock"}) == [
        ("course-v1:a+same+1", "git@h:o/a-same-1.git", "live"),
        ("course-v1:a+other+1", "", "master"),
    ]
    assert course_assets.git_targets(rows, "MJxPrep.js", {"stock"}, include_export_repos=True,
                                     remote_prefix="git@h:mitx/") == [
        ("course-v1:a+same+1", "git@h:o/a-same-1.git", "live"),
        ("course-v1:a+other+1", "git@h:mitx/content.git", "master"),
        ("course-v1:a+export+1", "git@h:o/a-export-1.git", ""),
    ]
    assert course_assets.git_targets(rows, "python_lib.zip", {"stock"}) == []
    # An explicit remote wins over both the export repository and the prefix
    assert course_assets.git_targets(rows[:2], "MJxPrep.js", {"stock"}, remote_prefix="git@h:mitx/",
                                     remotes={"content": "git@h:team/content.git",
                                              "a-same-1": "git@h:team/a-same-1.git"}) == [
        ("course-v1:a+same+1", "git@h:team/a-same-1.git", "live"),
        ("course-v1:a+other+1", "git@h:team/content.git", "master"),
    ]


def make_remote(bare, setup=None):
    """Make a bare course repository with static/MJxPrep.js on main and live.

    :param setup: called with the source tree before it's committed, to change it
    """
    source = bare.with_name(bare.name + ".src")
    (source / "static").mkdir(parents=True)
    (source / "static" / "MJxPrep.js").write_bytes(b"old")
    (source / "course.xml").write_text("<course/>")
    if setup:
        setup(source)
    git(source, "init", "-q", "-b", "main")
    git(source, "add", ".")
    git(source, "commit", "-q", "-m", "Initial commit")
    git(source, "branch", "live")
    subprocess.run(["git", "clone", "-q", "--bare", str(source), str(bare)], check=True, capture_output=True)
    return bare


@pytest.fixture
def remote(tmp_path, monkeypatch):
    """A course repository from make_remote, and git configured to commit."""
    config = tmp_path / "gitconfig"
    config.write_text("[user]\n\tname = t\n\temail = t@example.com\n[commit]\n\tgpgsign = false\n")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(config))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    return make_remote(tmp_path / "course.git")


def remote_file(bare, branch):
    result = subprocess.run(["git", "-C", str(bare), "show", f"{branch}:static/MJxPrep.js"],
                            capture_output=True, check=False)
    return result.stdout if result.returncode == 0 else None


def run_git_replace(tmp_path, targets, allowed, replacement=b"new", **kwargs):
    out = io.StringIO()
    writer = csv.DictWriter(out, course_assets.GIT_REPORT_FIELDS)
    writer.writeheader()
    counts = course_assets.run_git_replace(writer, "MJxPrep.js", replacement, targets, allowed,
                                           tmp_path / "work", "mjxprep", "Update MJxPrep.js", **kwargs)
    return counts, list(csv.DictReader(io.StringIO(out.getvalue())))


def test_run_git_replace_pushes_a_branch_and_leaves_the_import_branch(tmp_path, remote):
    url = f"file://{remote}"
    counts, rows = run_git_replace(tmp_path, [("course-v1:a+b+1", url, "live")], {OLD})
    assert counts == {"pushed": 1}
    assert rows[0]["old_sha256"] == OLD
    assert rows[0]["pushed_to"] == "mjxprep"
    assert remote_file(remote, "mjxprep") == b"new"
    assert remote_file(remote, "live") == b"old"
    # Run again: the import branch still has the old copy, but the push branch
    # has the new one, so nothing more is pushed
    counts, rows = run_git_replace(tmp_path, [("course-v1:a+b+1", url, "live")], {OLD})
    assert counts == {"already-pushed": 1}
    # A push branch holding something else is left alone
    counts, rows = run_git_replace(tmp_path, [("course-v1:a+b+1", url, "live")], {OLD},
                                   replacement=b"newer")
    assert counts == {"branch-exists": 1}
    assert remote_file(remote, "mjxprep") == b"new"


def test_run_git_replace_default_branch_and_dry_run(tmp_path, remote):
    url = f"file://{remote}"
    counts, rows = run_git_replace(tmp_path, [("course-v1:a+b+1", url, "")], {OLD}, dry_run=True)
    assert counts == {"would-replace": 1}
    assert rows[0]["action"] == "would-replace"
    assert rows[0]["branch"] == "main"
    assert remote_file(remote, "mjxprep") is None


def test_run_git_replace_only_replaces_allowlisted_copies(tmp_path, remote):
    url = f"file://{remote}"
    targets = [
        ("course-v1:a+b+1", url, "live"),
        ("course-v1:a+b+2", url, "live"),
        ("course-v1:a+c+1", "", "live"),
        ("course-v1:a+d+1", "--upload-pack=touch /tmp/x", "live"),
        ("course-v1:a+e+1", f"file://{tmp_path}/missing.git", "live"),
    ]
    counts, rows = run_git_replace(tmp_path, targets, {"0" * 64})
    assert counts["failed"] == 2
    assert [row["action"] for row in rows] == [
        "not-allowlisted", "duplicate-repo", "no-remote", "failed", "failed",
    ]
    assert rows[3]["error"] == "not a git remote URL"
    assert remote_file(remote, "mjxprep") is None


def test_main_git_replace_reads_the_inventory(tmp_path, remote, monkeypatch):
    inventory = tmp_path / "inventory.csv"
    with inventory.open("w", newline="") as out:
        writer = csv.DictWriter(out, course_assets.INVENTORY_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerow(inventory_row("course-v1:a+b+1", git_repo=f"file://{remote}",
                                      git_import="2026-01-01 course@live"))
        writer.writerow(inventory_row("course-v1:a+studio+1"))
    replacement = tmp_path / "MJxPrep.js"
    replacement.write_bytes(b"new")
    monkeypatch.chdir(tmp_path)
    args = ["git-replace", "--filename", "MJxPrep.js", "--replacement", str(replacement),
            "--inventory", str(inventory), "--status", "stock"]
    with pytest.raises(SystemExit):
        course_assets.main(args)  # no --push-branch
    assert course_assets.main([*args, "--push-branch", "live"]) == 0
    assert remote_file(remote, "live") == b"new"
    report = list(csv.DictReader((tmp_path / "git-report.csv").open()))
    assert [(row["course_key"], row["action"]) for row in report] == [("course-v1:a+b+1", "pushed")]


def test_run_git_replace_keeps_same_named_repositories_apart(tmp_path, remote):
    # edx-sysadmin knows repositories only by name, so two orgs' "course" can both be targets
    other = make_remote(tmp_path / "other" / "course.git")
    targets = [("course-v1:a+b+1", f"file://{remote}", "live"), ("course-v1:a+b+2", f"file://{other}", "live")]
    counts, __ = run_git_replace(tmp_path, targets, {OLD})
    assert counts == {"pushed": 2}
    assert remote_file(remote, "mjxprep") == remote_file(other, "mjxprep") == b"new"


def test_run_git_replace_refuses_a_work_tree_that_isnt_a_repository(tmp_path, remote):
    # The work dir sits in a checkout, which git must not fall through to
    enclosing = tmp_path / "checkout"
    enclosing.mkdir()
    git(enclosing, "init", "-q", "-b", "main")
    (enclosing / "kept").write_text("x")
    git(enclosing, "add", ".")
    git(enclosing, "commit", "-q", "-m", "init")
    url = f"file://{remote}"
    course_assets.work_tree_path(enclosing / "work", url, "live").mkdir(parents=True)
    out = io.StringIO()
    writer = csv.DictWriter(out, course_assets.GIT_REPORT_FIELDS)
    counts = course_assets.run_git_replace(writer, "MJxPrep.js", b"new", [("course-v1:a+b+1", url, "live")],
                                           {OLD}, enclosing / "work", "mjxprep", "Update")
    assert counts == {"failed": 1}
    assert "isn't a git repository" in out.getvalue()
    head = subprocess.run(["git", "-C", str(enclosing), "branch", "--show-current"],
                          capture_output=True, check=True, text=True).stdout.strip()
    assert head == "main"
    assert (enclosing / "kept").read_text() == "x"


def test_run_git_replace_leaves_copies_studio_imports_differently(tmp_path, remote):
    def symlinked(source):
        (source / "MJxPrep.js").write_bytes(b"old")
        (source / "static" / "MJxPrep.js").unlink()
        (source / "static" / "MJxPrep.js").symlink_to("../MJxPrep.js")

    def overridden(source):
        (source / "static_import").mkdir()
        (source / "static_import" / "MJxPrep.js").write_bytes(b"old")

    symlink = make_remote(tmp_path / "symlink.git", symlinked)
    static_import = make_remote(tmp_path / "static_import.git", overridden)
    empty = tmp_path / "empty.git"
    subprocess.run(["git", "init", "-q", "--bare", str(empty)], check=True, capture_output=True)
    targets = [
        ("course-v1:a+b+1", f"file://{symlink}", "live"),
        ("course-v1:a+b+2", f"file://{static_import}", "live"),
        ("course-v1:a+b+3", f"file://{empty}", ""),
        ("course-v1:a+b+4", f"file://{remote}", "live"),
    ]
    counts, rows = run_git_replace(tmp_path, targets, {OLD})
    assert [row["action"] for row in rows] == ["symlink", "static-import", "failed", "pushed"]
    assert rows[2]["error"] == "remote has no default branch"
    assert remote_file(symlink, "mjxprep") is None


def test_run_git_replace_opens_a_missing_pull_request_on_a_rerun(tmp_path, remote, monkeypatch):
    calls = []

    def fail_then_open(url, base, head, title, body):
        calls.append((url, base, head))
        if len(calls) == 1:
            raise subprocess.CalledProcessError(1, "gh", stderr="gh: not logged in")
        return "https://example.com/pull/1"

    monkeypatch.setattr(course_assets, "_open_pull_request", fail_then_open)
    url = f"file://{remote}"
    __, rows = run_git_replace(tmp_path, [("course-v1:a+b+1", url, "live")], {OLD}, open_pr=True)
    assert (rows[0]["action"], rows[0]["error"]) == ("pushed", "pull request: gh: not logged in")
    __, rows = run_git_replace(tmp_path, [("course-v1:a+b+1", url, "live")], {OLD}, open_pr=True)
    assert (rows[0]["action"], rows[0]["pull_request"]) == ("already-pushed", "https://example.com/pull/1")
    assert calls == [(url, "live", "mjxprep")] * 2


def test_run_git_replace_dry_run_opens_no_pull_request(tmp_path, remote, monkeypatch):
    url = f"file://{remote}"
    run_git_replace(tmp_path, [("course-v1:a+b+1", url, "live")], {OLD})

    def refuse(*args):
        raise AssertionError("opened a pull request in a dry run")

    monkeypatch.setattr(course_assets, "_open_pull_request", refuse)
    counts, __ = run_git_replace(tmp_path, [("course-v1:a+b+1", url, "live")], {OLD}, dry_run=True, open_pr=True)
    assert counts == {"already-pushed": 1}


def test_main_git_replace_open_pr_needs_gh(tmp_path, monkeypatch):
    inventory = tmp_path / "inventory.csv"
    with inventory.open("w", newline="") as out:
        writer = csv.DictWriter(out, course_assets.INVENTORY_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerow(inventory_row("course-v1:a+b+1", git_import="2026-01-01 course@live"))
    replacement = tmp_path / "MJxPrep.js"
    replacement.write_bytes(b"new")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(course_assets.shutil, "which", lambda name: None)
    with pytest.raises(SystemExit):
        course_assets.main(["git-replace", "--filename", "MJxPrep.js", "--replacement", str(replacement),
                            "--inventory", str(inventory), "--status", "stock", "--remote-prefix",
                            "git@example.com:mitx/", "--push-branch", "mjxprep", "--open-pr"])
    assert not (tmp_path / "git-report.csv").exists()


def test_run_git_replace_adds_a_missing_origin(tmp_path, remote):
    # A run stopped between `git init` and `git remote add` leaves this behind
    url = f"file://{remote}"
    tree = course_assets.work_tree_path(tmp_path / "work", url, "live")
    tree.mkdir(parents=True)
    git(tree, "init", "-q")
    counts, __ = run_git_replace(tmp_path, [("course-v1:a+b+1", url, "live")], {OLD})
    assert counts == {"pushed": 1}


@pytest.mark.parametrize("url", [
    "git@github.mit.edu:mitx/repo.git",
    "ssh://git@github.mit.edu/mitx/repo.git",
    "ssh://git@github.mit.edu:2222/mitx/repo.git",
    "https://github.mit.edu/mitx/repo",
])
def test_gh_repo(url):
    assert course_assets.gh_repo(url) == "github.mit.edu/mitx/repo"

