"""Inventory and replace MJxPrep.js and python_lib.zip in an Open edX Studio's courses.

Each course run keeps its own copy of these files in Studio's contentstore, so a
library fix reaches learners only when each run's copy is replaced. ``inventory``
reports what every run has, and ``replace`` swaps a file only in the runs whose
current copy has a hash you allowed, writing a report of what it did.

Build known.json (the hash of every MJxPrep.js this repository has had) from a
checkout with full history::

    python3 scripts/course_assets.py known -o known.json

``inventory`` and ``replace`` run inside a Studio (CMS) container with the
edxapp Python, e.g. after copying this file, known.json and the replacement in::

    python course_assets.py inventory --known known.json -o inventory.csv
    python course_assets.py replace --filename MJxPrep.js --replacement MJxPrep.js \\
        --inventory inventory.csv --status stock --dry-run -o report.csv

Without ``--dry-run``, ``replace`` writes to the contentstore. It saves each
copy it replaces in ``--backup-dir`` first (named with the copy's hash, never
overwritten), so copy that directory and the report out of the container before
it goes away. The report file must not exist yet, so each run keeps its own
record. To roll a course back, run ``replace`` with its backup as
``--replacement`` and ``--allow`` set to the new hash.

Only the asset with exactly this name is looked at, so a copy uploaded under
another name (e.g. one imported from a subfolder, ``js_MJxPrep.js``) is
reported as absent and left alone.

``replace`` doesn't touch git. A run exported to git (``git_repo`` in the
inventory) picks up the new file on its next export. A run imported from git
(``git_import``: the date, repository and branch of its latest import) gets the
old file back on its next import, so update its repository as well with
``git-replace``, on a workstation that can push to it::

    python3 scripts/course_assets.py git-replace --filename MJxPrep.js \\
        --replacement MJxPrep.js --inventory inventory.csv --status stock \\
        --push-branch mjxprep-3.1.0 --open-pr --dry-run

It fetches each repository's import branch into ``--work-dir``, replaces
``static/<filename>`` where its hash is allowed (the inventory's hashes for
those statuses, plus ``--allow``), and pushes one commit per repository to
``--push-branch``. Pushing to the import branch itself, when that is
edx-sysadmin's ``SYSADMIN_DEFAULT_BRANCH`` (``live`` on MIT's instances),
re-imports the run straight away along with anything else on that branch,
so a separate branch and a pull request for the course team is the default
to reach for. Rerunning is safe: a push branch that already has the new file
is reported ``already-pushed``, and ``--open-pr`` then opens its pull request
if it has none. edx-sysadmin records only the repository's name, so a run
imported from a repository other than its export repository needs
``--remote NAME=URL`` or ``--remote-prefix`` (e.g. ``git@github.mit.edu:mitx/``)
to be found; the report lists it as ``no-remote`` otherwise. A run whose
team edits in git but uploads the course through Studio's import page leaves
no record, so it shows up only as ``git_repo`` (or nothing).

Only the standard library is used outside the edxapp environment, so ``known``
and ``git-replace`` run with plain ``python3`` (``git-replace`` also needs
``git``, and ``gh`` for ``--open-pr``).
"""

import argparse
import csv
import datetime
import hashlib
import io
import json
import re
import subprocess
import sys
import zipfile
import zlib
from collections import defaultdict
from pathlib import Path

DEFAULT_FILES = ("MJxPrep.js", "python_lib.zip")
# Every path MJxPrep.js has had in this repository
MJXPREP_PATHS = ("MJxPrep.js", "mitxgraders-js/MJxPrep.js", "course/static/MJxPrep.js")
GIT_SYMLINK_MODE = "120000"
GIT_FILE_MODES = ("100644", "100755")
LIBRARY_PACKAGES = {"mitxgraders", "voluptuous"}
# Left by the tool that made the zip, not modules the course added
ZIP_NOISE = {"__MACOSX", "__pycache__", ".DS_Store"}
# What a damaged or unsupported zip raises when read (ValueError covers bad
# offsets and undecodable names)
ZIP_READ_ERRORS = (zipfile.BadZipFile, zlib.error, RuntimeError, NotImplementedError, EOFError, ValueError)
VERSION_PATTERN = re.compile(rb"""__version__\s*=\s*["']([^"']+)["']""")
LINE_CONTINUATION = re.compile(rb"\\[ \t]*\r?$", re.MULTILINE)
# edx-sysadmin's CourseGitLog.git_log ends with the branch it imported
GIT_IMPORT_BRANCH = re.compile(r"Branch: (\S+)")

INVENTORY_FIELDS = (
    "course_key", "display_name", "start", "end", "scope", "template", "reruns",
    "git_repo", "git_import",
    "filename", "status", "version", "sha256", "size", "locked", "extras",
)
REPORT_FIELDS = ("course_key", "filename", "action", "old_sha256", "new_sha256", "backup")
GIT_REPORT_FIELDS = (
    "course_key", "repo", "branch", "path", "action", "old_sha256", "new_sha256",
    "commit", "pushed_to", "pull_request", "error",
)
# What git accepts as a remote here; anything else (e.g. a value starting
# with "-") is refused rather than passed to git
REMOTE_URL = re.compile(r"^(git@[^:\s]+:|ssh://|https://|file://)\S+$")


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def normalized_sha256(data):
    """Hash ignoring line endings, indentation, trailing spaces and blank lines.

    Whitespace inside a line is kept, since in a string or regex literal it
    changes what the code does. Whitespace at the ends of a line can't be inside
    one, as long as no string spans lines (see :func:`spans_lines`).
    """
    lines = (line.strip() for line in data.splitlines())
    return sha256(b"\n".join(line for line in lines if line))


def spans_lines(data):
    """Whether JavaScript source may have a string spanning lines, which
    :func:`normalized_sha256` would change: a template literal, or a backslash
    line continuation."""
    return b"`" in data or LINE_CONTINUATION.search(data) is not None


def classify(data, known):
    """Compare a file's contents against known released versions.

    :param data: the file's bytes
    :param known: normalized_sha256 -> label of each released version of this
        file, or an empty dict when there are none to compare against
    :returns: (status, version label): ``stock`` when it matches a known
        version, ``customized`` when it doesn't, ``present`` with no known versions
    :rtype: tuple[str, str]
    """
    if not known:
        return "present", ""
    label = known.get(normalized_sha256(data))
    return ("stock", label) if label else ("customized", "")


def inspect_zip(data):
    """Report the mitxgraders version in a python_lib.zip and what else it bundles.

    The library files themselves aren't compared against a release, so a zip
    whose mitxgraders/ was edited still reports as ``library-only``.

    :param data: the zip's bytes
    :returns: (status, mitxgraders version, extra top-level names). Status is
        ``library-only`` when the zip holds only mitxgraders and voluptuous,
        ``extras`` when it also has the course's own modules, ``nested`` when
        mitxgraders is inside a folder (edX can't import it), ``no-mitxgraders``
        or ``unreadable``.
    :rtype: tuple[str, str, list[str]]
    """
    try:
        archive = zipfile.ZipFile(io.BytesIO(data))
        names = archive.namelist()
        tops = {name.split("/", 1)[0] for name in names}
        extras = sorted(tops - LIBRARY_PACKAGES - ZIP_NOISE)
        if "mitxgraders/version.py" in names:
            version_file = "mitxgraders/version.py"
            status = "extras" if extras else "library-only"
        else:
            nested = [
                name for name in names
                if name.endswith("/mitxgraders/version.py") and not name.startswith("__MACOSX/")
            ]
            if not nested:
                return "no-mitxgraders", "", extras
            version_file = nested[0]
            status = "nested"
        match = VERSION_PATTERN.search(archive.read(version_file))
        version = match.group(1).decode() if match else ""
    except ZIP_READ_ERRORS:
        return "unreadable", "", []
    return status, version, extras


def inspect_file(filename, data, known):
    """:returns: (status, version, extras) for one course's copy of a file"""
    if filename == "python_lib.zip":
        return inspect_zip(data)
    status, version = classify(data, known.get(filename, {}))
    return status, version, []


def course_scope(start, end, now):
    """:returns: ``upcoming``, ``active`` or ``archived`` for a run's dates"""
    if start is not None and start > now:
        return "upcoming"
    if end is None or end >= now:
        return "active"
    return "archived"


def is_template(course_key):
    # Course teams rerun courses from runs named e.g. course-v1:MITx+Template+2026_03_18
    return "template" in str(course_key).lower()


def latest_template_runs(runs):
    """Find the newest run of each template course, the one teams rerun from.

    :param runs: (course key, created) pairs, where created is when the run
        was created (start dates are no good for this: Studio defaults an unset
        start to 2040)
    :returns: course keys of the newest run of each template course
    :rtype: set[str]
    """
    newest = {}
    for course_key, created in runs:
        if not is_template(course_key):
            continue
        course = str(course_key).rsplit("+", 1)[0]
        order = (created, str(course_key))
        if course not in newest or order > newest[course]:
            newest[course] = order
    return {key for __, key in newest.values()}


def decide(current_sha256, new_sha256, allowed):
    """Decide what ``replace`` does with one course's copy.

    :param current_sha256: hash of the course's copy, or None when it has none
    :param new_sha256: hash of the replacement
    :param allowed: hashes that may be replaced
    :rtype: str
    """
    if current_sha256 is None:
        return "absent"
    if current_sha256 == new_sha256:
        return "already-current"
    if current_sha256 in allowed:
        return "replace"
    return "not-allowlisted"


def select_from_inventory(rows, filename, statuses):
    """Pick the courses and hashes to replace from an inventory's rows.

    :param rows: rows of an ``inventory`` CSV
    :param filename: the file being replaced
    :param statuses: inventory statuses to replace, e.g. {"stock"}
    :returns: (course keys in inventory order, their current sha256 hashes)
    :rtype: tuple[list[str], set[str]]
    """
    courses = []
    allowed = set()
    for row in rows:
        if row["filename"] == filename and row["status"] in statuses:
            courses.append(row["course_key"])
            allowed.add(row["sha256"])
    return courses, allowed


def read_hashes(text):
    """Read sha256 hashes one per line, also accepting ``sha256sum`` output."""
    return {line.split()[0].lower() for line in text.splitlines() if line.strip()}


def backup_path(backup_dir, course_key, filename, old_sha256):
    """Where ``replace`` saves a course's copy before overwriting it."""
    safe_key = str(course_key).replace(":", "_").replace("/", "_")
    return Path(backup_dir) / f"{safe_key}.{old_sha256[:16]}.{filename}"


def _git(repo_root, *args):
    return subprocess.run(
        ["git", "-C", str(repo_root), *args], capture_output=True, check=True
    ).stdout


def _git_file(repo_root, rev, path):
    """:returns: the file's bytes at rev, or None when it's absent or a symlink there"""
    entry = _git(repo_root, "ls-tree", rev, "--", path).decode().split()
    if not entry or entry[0] == GIT_SYMLINK_MODE:
        return None
    return _git(repo_root, "cat-file", "blob", entry[2])


def _known_hash(data, source):
    if spans_lines(data):
        raise ValueError(
            f"{source} has a template literal or line continuation, so whitespace-normalized "
            "hashes could match a copy that differs inside a string; classify by exact hash instead"
        )
    return normalized_sha256(data)


def known_from_git(repo_root):
    """Collect every version of MJxPrep.js this repository has had.

    :param repo_root: a checkout of this repository with its full history
    :returns: {"MJxPrep.js": {normalized_sha256: label}}, labelled with the
        first release that shipped it, or else the first commit that had it
    :rtype: dict[str, dict[str, str]]
    :raises ValueError: on a shallow clone, which would leave old versions out
    """
    if _git(repo_root, "rev-parse", "--is-shallow-repository").strip() == b"true":
        raise ValueError(f"{repo_root} is a shallow clone; run `git fetch --unshallow --tags` first")
    labels = {}
    commits = _git(repo_root, "log", "--reverse", "--format=%H %as", "HEAD", "--", *MJXPREP_PATHS)
    for line in commits.decode().splitlines():
        commit, date = line.split()
        for path in MJXPREP_PATHS:
            data = _git_file(repo_root, commit, path)
            if data is not None:
                labels.setdefault(_known_hash(data, f"{commit[:7]}:{path}"), f"{commit[:7]} ({date})")
    # Oldest tag first, so a version is labelled with the first release that had it
    tagged = {}
    for tag in _git(repo_root, "tag", "--sort=creatordate").decode().split():
        for path in MJXPREP_PATHS:
            data = _git_file(repo_root, tag, path)
            if data is not None:
                tagged.setdefault(_known_hash(data, f"{tag}:{path}"), tag)
                break
    labels.update(tagged)
    if not labels:
        raise ValueError(f"No history of {', '.join(MJXPREP_PATHS)} in {repo_root}")
    return {"MJxPrep.js": labels}


def run_inventory(store, writer, runs, filenames, known, reruns):
    """Write one row per (course run, file) with what the run has.

    :param store: a :class:`StudioStore`, or a stand-in for tests
    :param writer: csv.DictWriter with INVENTORY_FIELDS
    :param runs: (course key, overview fields) for each run
    :param reruns: course key -> number of successful reruns made from it
    :returns: number of rows written
    :rtype: int
    """
    rows = 0
    for course_key, fields in runs:
        for filename in filenames:
            content = store.find(course_key, filename)
            row = {"course_key": str(course_key), "filename": filename, **fields,
                   "reruns": reruns.get(str(course_key), 0)}
            if content is None:
                row["status"] = "absent"
            else:
                data = bytes(content.data)
                status, version, extras = inspect_file(filename, data, known)
                row.update(status=status, version=version, sha256=sha256(data), size=len(data),
                           locked="yes" if content.locked else "", extras=" ".join(extras))
            writer.writerow(row)
            rows += 1
    return rows


def run_replace(store, writer, filename, replacement, course_keys, allowed, dry_run, backup_dir):
    """Replace ``filename`` in each course whose current copy's hash is allowed.

    The current copy is saved in ``backup_dir`` before it is overwritten, and
    each write is read back. If a write fails, the report gets a ``failed`` row
    naming the backup, the old copy is written back and checked (a
    ``restored`` row), and the run stops.

    :param store: a :class:`StudioStore`, or a stand-in for tests
    :param writer: csv.DictWriter with REPORT_FIELDS
    :returns: count of each action taken
    :rtype: dict[str, int]
    """
    new_sha256 = sha256(replacement)
    parsed = parse_keys(store, course_keys)
    counts = defaultdict(int)
    replaced = []
    try:
        for key, course_key in parsed:
            row = {"course_key": key, "filename": filename, "new_sha256": new_sha256}
            if not store.has_course(course_key):
                row["action"] = "no-course"
            else:
                current = store.find(course_key, filename)
                old_data = bytes(current.data) if current is not None else None
                old_sha256 = sha256(old_data) if old_data is not None else None
                row["old_sha256"] = old_sha256
                row["action"] = decide(old_sha256, new_sha256, allowed)
                if row["action"] == "replace" and dry_run:
                    row["action"] = "would-replace"
                elif row["action"] == "replace":
                    row["backup"] = str(save_backup(backup_dir, key, filename, old_data))
                    try:
                        _write_and_check(store, course_key, filename, current, replacement)
                    except BaseException:
                        writer.writerow({**row, "action": "failed"})
                        _write_and_check(store, course_key, filename, current, old_data)
                        writer.writerow({**row, "action": "restored"})
                        raise
                    row["action"] = "replaced"
                    replaced.append(course_key)
            writer.writerow(row)
            counts[row["action"]] += 1
    finally:
        # The LMS can cache the old file again from a lagging read replica
        # while the run is going, so clear each replaced file once more
        for course_key in replaced:
            store.clear_cache(course_key, filename)
    return dict(counts)


def parse_keys(store, course_keys):
    """Parse every key up front, so a typo fails before anything is written."""
    return [(key, store.parse(key)) for key in course_keys]


def save_backup(backup_dir, course_key, filename, data):
    """Save a course's copy under its hash, reusing an earlier backup only if it's intact.

    :returns: the backup's path
    :rtype: Path
    """
    path = backup_path(backup_dir, course_key, filename, sha256(data))
    if path.exists() and sha256(path.read_bytes()) == sha256(data):
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(path.name + ".partial")
    partial.write_bytes(data)
    partial.replace(path)
    return path


def _write_and_check(store, course_key, filename, current, data):
    store.write(course_key, filename, current, data)
    written = store.find(course_key, filename)
    if written is None or sha256(bytes(written.data)) != sha256(data):
        raise RuntimeError(f"{course_key}: {filename} didn't read back as {sha256(data)}")
    store.clear_cache(course_key, filename)


def repo_name(url):
    """:returns: a remote URL's repository name, e.g. ``MITx-6.00x-1T2026``"""
    return url.rstrip("/").rsplit("/", 1)[-1].rsplit(":", 1)[-1].removesuffix(".git")


def format_git_import(created, repo_dir, git_log):
    """:returns: an inventory's ``git_import`` for one edx-sysadmin CourseGitLog row"""
    branch = GIT_IMPORT_BRANCH.search(git_log or "")
    date = f"{created:%Y-%m-%d}" if created else ""
    return f"{date} {repo_dir}@{branch.group(1) if branch else ''}"


def parse_git_import(value):
    """:returns: (repo name, branch) from an inventory's ``git_import``, or ("", "")"""
    if not value:
        return "", ""
    repo, __, branch = value.split(" ", 1)[-1].rpartition("@")
    return repo, branch


def git_targets(rows, filename, statuses, include_export_repos=False, remote_prefix="", remotes=None):
    """Pick the repositories to update from an inventory's rows.

    A run imported from git is updated on the branch it was imported from.
    edx-sysadmin records only the repository's name, so its URL is taken
    from ``remotes`` (name -> URL), else the run's export repository when that
    has the same name, else ``remote_prefix`` + the name. A run that is only
    exported to git is skipped unless ``include_export_repos``, since Studio
    is its source and its next export brings the new file.

    :param rows: rows of an ``inventory`` CSV
    :param statuses: inventory statuses to update, e.g. {"stock"}
    :returns: (course key, remote URL or "" when unknown, branch or "" for the default)
    :rtype: list[tuple[str, str, str]]
    """
    remotes = remotes or {}
    targets = []
    for row in rows:
        if row["filename"] != filename or row["status"] not in statuses:
            continue
        url = row.get("git_repo", "")
        imported, branch = parse_git_import(row.get("git_import", ""))
        if imported:
            if imported in remotes:
                url = remotes[imported]
            elif repo_name(url) != imported:
                url = f"{remote_prefix}{imported}.git" if remote_prefix else ""
        elif not url or not include_export_repos:
            continue
        targets.append((row["course_key"], url, branch))
    return targets


class GitTargetError(Exception):
    """A target repository that can't be updated, reported as ``failed``."""


def work_tree_path(work_dir, url, branch):
    """Where ``git-replace`` fetches a repository's branch.

    The URL's hash is in the name, so two repositories with the same name
    (edx-sysadmin knows them only by name) never share a work tree.
    """
    digest = sha256(url.encode())[:8]
    return Path(work_dir) / f"{repo_name(url)}-{digest}@{branch.replace('/', '_')}"


def _checkout(url, branch, work_dir):
    """Fetch the tip of ``branch`` (or the remote's default branch) into a work tree.

    :returns: (work tree path, branch name)
    :rtype: tuple[Path, str]
    :raises GitTargetError: when the remote has no default branch, or the work
        tree's directory exists but isn't a repository (git would otherwise
        work on whatever checkout encloses it)
    """
    if not branch:
        head = _git(".", "ls-remote", "--symref", url, "HEAD").decode()
        if "refs/heads/" not in head:
            raise GitTargetError("remote has no default branch")
        branch = head.split("refs/heads/", 1)[1].split()[0]
    tree = work_tree_path(work_dir, url, branch)
    if not tree.exists():
        _git(".", "init", "--quiet", str(tree))
        _git(tree, "remote", "add", "origin", url)
    elif not (tree / ".git").is_dir():
        raise GitTargetError(f"{tree} exists but isn't a git repository")
    _git(tree, "remote", "set-url", "origin", url)
    _git(tree, "fetch", "--quiet", "--depth", "1", "origin", f"refs/heads/{branch}")
    _git(tree, "checkout", "--quiet", "--force", "-B", "course-assets", "FETCH_HEAD")
    _git(tree, "clean", "--quiet", "-d", "--force")
    return tree, branch


def _push_branch_state(tree, push_branch, path, new_sha256):
    """Check a push branch from an earlier run, so running again doesn't fail or duplicate it.

    :returns: ``replace`` when the remote has no such branch,
        ``already-pushed`` when it has the new file, else ``branch-exists``
    :rtype: str
    """
    ref = f"refs/heads/{push_branch}"
    if not _git(tree, "ls-remote", "origin", ref).strip():
        return "replace"
    _git(tree, "fetch", "--quiet", "--depth", "1", "origin", ref)
    try:
        pushed = _git(tree, "show", f"FETCH_HEAD:{path}")
    except subprocess.CalledProcessError:
        return "branch-exists"
    return "already-pushed" if sha256(pushed) == new_sha256 else "branch-exists"


def _last_line(error):
    """:returns: the last line a failed command wrote to stderr"""
    output = error.stderr if isinstance(error.stderr, str) else (error.stderr or b"").decode(errors="replace")
    return output.strip().splitlines()[-1] if output.strip() else str(error)


def _gh(*args):
    return subprocess.run(["gh", *args], capture_output=True, check=True, text=True).stdout.strip()


def _open_pull_request(url, base, head, title, body):
    """Open a pull request with the ``gh`` CLI, or find the one already open.

    :returns: its URL
    """
    host_path = re.sub(r"^(git@|ssh://git@|https://|ssh://)", "", url).replace(":", "/", 1)
    repo = host_path.removesuffix(".git")
    existing = _gh("pr", "list", "--repo", repo, "--base", base, "--head", head,
                   "--state", "open", "--json", "url", "--jq", ".[0].url // empty")
    return existing or _gh("pr", "create", "--repo", repo, "--base", base, "--head", head,
                           "--title", title, "--body", body)


def _tree_entry(tree, path):
    """:returns: the git mode of ``path`` at HEAD, or None when it's absent"""
    entry = _git(tree, "ls-tree", "HEAD", "--", path).decode().split()
    return entry[0] if entry else None


def run_git_replace(writer, filename, replacement, targets, allowed, work_dir, push_branch,
                    message, dry_run=False, open_pr=False):
    """Replace ``static/<filename>`` in each target repository whose copy's hash is allowed.

    Each change is committed on its own and pushed to ``push_branch``. When
    that is the branch the run is imported from and edx-sysadmin's
    ``SYSADMIN_DEFAULT_BRANCH`` (``live`` on MIT's instances), its webhook
    re-imports the run. Otherwise the change waits on that branch, and
    ``open_pr`` opens a pull request for it (or finds the one already open,
    so a rerun can add a missing one). A repository that fails is reported
    and the run moves on, since nothing was pushed to it.

    A symlinked ``static/<filename>`` (or ``static/``), which Studio's import
    follows, and a ``static_import/<filename>``, which the import loads over
    ``static/``, are reported and left for a person to sort out.

    :param targets: (course key, remote URL, branch) from :func:`git_targets`
    :param writer: csv.DictWriter with GIT_REPORT_FIELDS
    :returns: count of each action taken
    :rtype: dict[str, int]
    """
    new_sha256 = sha256(replacement)
    path = f"static/{filename}"
    counts = defaultdict(int)
    seen = set()
    for course_key, url, branch in targets:
        row = {"course_key": course_key, "repo": url, "branch": branch, "path": path,
               "new_sha256": new_sha256}
        if not url:
            row["action"] = "no-remote"
        elif not REMOTE_URL.match(url):
            row.update(action="failed", error="not a git remote URL")
        elif (url, branch) in seen:
            row["action"] = "duplicate-repo"
        else:
            seen.add((url, branch))
            try:
                tree, row["branch"] = _checkout(url, branch, work_dir)
                current = tree / path
                mode = _tree_entry(tree, path)
                if GIT_SYMLINK_MODE in (_tree_entry(tree, "static"), mode):
                    row["action"] = "symlink"
                elif _tree_entry(tree, f"static_import/{filename}"):
                    row["action"] = "static-import"
                else:
                    old_data = current.read_bytes() if mode in GIT_FILE_MODES else None
                    row["old_sha256"] = sha256(old_data) if old_data is not None else None
                    row["action"] = decide(row["old_sha256"], new_sha256, allowed)
                if row["action"] == "replace" and push_branch and push_branch != row["branch"]:
                    row["action"] = _push_branch_state(tree, push_branch, path, new_sha256)
                if row["action"] == "replace" and dry_run:
                    row["action"] = "would-replace"
                elif row["action"] == "replace":
                    current.write_bytes(replacement)
                    _git(tree, "add", "--", path)
                    _git(tree, "commit", "--quiet", "-m", message)
                    row["commit"] = _git(tree, "rev-parse", "HEAD").decode().strip()
                    _git(tree, "push", "--quiet", "origin", f"HEAD:refs/heads/{push_branch}")
                    row.update(action="pushed", pushed_to=push_branch)
            except subprocess.CalledProcessError as error:
                row.update(action="failed", error=_last_line(error))
            except GitTargetError as error:
                row.update(action="failed", error=str(error))
            if open_pr and row["action"] in ("pushed", "already-pushed") and push_branch != row["branch"]:
                try:
                    row["pull_request"] = _open_pull_request(
                        url, row["branch"], push_branch, message,
                        f"Replaces `{path}` (sha256 {row['old_sha256']}) with sha256 {new_sha256}.",
                    )
                except subprocess.CalledProcessError as error:
                    row["error"] = f"pull request: {_last_line(error)}"
        writer.writerow(row)
        counts[row["action"]] += 1
    return dict(counts)


class StudioStore:
    """Course assets in the contentstore of the Studio this runs in."""

    def __init__(self):
        import os

        from openedx.core.lib.safe_lxml import defuse_xml_libs

        defuse_xml_libs()
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cms.envs.production")
        os.environ.setdefault("SERVICE_VARIANT", "cms")
        import django

        django.setup()

    @staticmethod
    def parse(key):
        from opaque_keys.edx.keys import CourseKey

        return CourseKey.from_string(key)

    @staticmethod
    def has_course(course_key):
        from xmodule.modulestore.django import modulestore

        return bool(modulestore().has_course(course_key))

    @staticmethod
    def _location(course_key, filename):
        from xmodule.contentstore.content import StaticContent

        return StaticContent.compute_location(course_key, filename)

    def find(self, course_key, filename):
        from xmodule.contentstore.django import contentstore

        return contentstore().find(self._location(course_key, filename), throw_on_not_found=False)

    def write(self, course_key, filename, current, data):
        """Save data over the current asset, keeping its name, type, lock and import path."""
        from xmodule.contentstore.content import StaticContent
        from xmodule.contentstore.django import contentstore

        location = self._location(course_key, filename)
        contentstore().save(StaticContent(
            location, current.name, current.content_type, data,
            thumbnail_location=current.thumbnail_location,
            import_path=current.import_path, locked=current.locked,
        ))

    def clear_cache(self, course_key, filename):
        from openedx.core.djangoapps.contentserver.caching import del_cached_content

        del_cached_content(self._location(course_key, filename))

    @staticmethod
    def course_runs(course_keys, include_archived):
        """Yield (course key, overview fields) for the runs to inventory."""
        from django.utils import timezone
        from opaque_keys.edx.keys import CourseKey
        from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

        now = timezone.now()
        # CCX runs share their parent course's assets
        overviews = [
            overview for overview in CourseOverview.objects.order_by("id")
            if not str(overview.id).startswith("ccx-")
        ]
        latest_templates = latest_template_runs((overview.id, overview.created) for overview in overviews)
        sources = StudioStore.git_sources()
        if course_keys:
            wanted = {CourseKey.from_string(key) for key in course_keys}
            overviews = [overview for overview in overviews if overview.id in wanted]
        for overview in overviews:
            scope = course_scope(overview.start, overview.end, now)
            template = ""
            if is_template(overview.id):
                template = "latest" if str(overview.id) in latest_templates else "older"
            if include_archived or course_keys or scope != "archived" or template == "latest":
                yield overview.id, {
                    "display_name": overview.display_name,
                    "start": overview.start.date().isoformat() if overview.start else "",
                    "end": overview.end.date().isoformat() if overview.end else "",
                    "scope": scope,
                    "template": template,
                    **sources.get(str(overview.id), {}),
                }

    @staticmethod
    def git_sources():
        """Find the runs tied to a git repository.

        ``git_repo`` is where ol-openedx-git-auto-export pushes the run on
        each publish; ``git_import`` is the run's latest import from git by
        edx-sysadmin (its GitHub webhook or ``git_add_course``), which
        replaces what Studio has with the repository's branch.

        :returns: course key -> {"git_repo": url, "git_import": "date repo@branch"}
        :rtype: dict[str, dict[str, str]]
        """
        from django.apps import apps

        sources = defaultdict(dict)
        if apps.is_installed("ol_openedx_git_auto_export"):
            repos = apps.get_model("ol_openedx_git_auto_export", "ContentGitRepository").objects
            for key, url in repos.filter(is_export_enabled=True).values_list("content_key", "git_url"):
                sources[str(key)]["git_repo"] = url
        if apps.is_installed("edx_sysadmin"):
            logs = apps.get_model("edx_sysadmin", "CourseGitLog").objects.exclude(course_id=None)
            # Oldest first, so each run ends up with its latest import
            for log in logs.order_by("created", "id"):
                sources[str(log.course_id)]["git_import"] = format_git_import(log.created, log.repo_dir, log.git_log)
        return sources

    @staticmethod
    def rerun_counts():
        from common.djangoapps.course_action_state.managers import CourseRerunUIStateManager
        from common.djangoapps.course_action_state.models import CourseRerunState

        counts = defaultdict(int)
        succeeded = CourseRerunState.objects.filter(state=CourseRerunUIStateManager.State.SUCCEEDED)
        for source in succeeded.values_list("source_course_key", flat=True):
            counts[str(source)] += 1
        return counts


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)

    known_parser = commands.add_parser("known", help="write known.json from this repository's history")
    known_parser.add_argument("-o", "--output", type=Path, default=Path("known.json"))

    inventory_parser = commands.add_parser("inventory", help="report each course run's copies (in Studio)")
    inventory_parser.add_argument("--known", type=Path, required=True, help="known.json from the known command")
    inventory_parser.add_argument(
        "--file", dest="filenames", action="append",
        help=f"asset filename to report; repeat for more (default: {', '.join(DEFAULT_FILES)})",
    )
    inventory_parser.add_argument("--course", dest="course_keys", action="append", default=[],
                                  help="only this course run; repeat for more")
    inventory_parser.add_argument(
        "--include-archived", action="store_true",
        help="also report archived runs (by default: active, upcoming, and the newest run of each template)",
    )
    inventory_parser.add_argument("-o", "--output", type=Path, default=Path("inventory.csv"))

    replace_parser = commands.add_parser("replace", help="replace an asset where its hash is allowed (in Studio)")
    replace_parser.add_argument("--filename", required=True, help="asset filename, e.g. MJxPrep.js")
    replace_parser.add_argument("--replacement", type=Path, required=True, help="file to upload in its place")
    replace_parser.add_argument("--inventory", type=Path,
                                help="inventory CSV: replace in the runs listed with --status, at their hashes")
    replace_parser.add_argument("--status", action="append", default=[],
                                help="inventory status to replace, e.g. stock; repeat for more")
    replace_parser.add_argument("--course", dest="course_keys", action="append", default=[],
                                help="course run to replace in; repeat for more")
    replace_parser.add_argument("--allow", action="append", default=[],
                                help="sha256 of a current copy that may be replaced; repeat for more")
    replace_parser.add_argument("--allow-file", type=Path,
                                help="file of allowed sha256 hashes, one per line (sha256sum output works)")
    replace_parser.add_argument("--dry-run", action="store_true", help="report what would change, write nothing")
    replace_parser.add_argument(
        "--backup-dir", type=Path, default=Path("backups"),
        help="where to save each replaced copy, to roll back with (default: %(default)s)",
    )
    replace_parser.add_argument("-o", "--output", type=Path, default=Path("report.csv"))

    git_parser = commands.add_parser(
        "git-replace", help="replace a file in the git repositories runs are imported from (on a workstation)",
    )
    git_parser.add_argument("--filename", required=True, help="asset filename, e.g. MJxPrep.js")
    git_parser.add_argument("--replacement", type=Path, required=True, help="file to commit in its place")
    git_parser.add_argument("--inventory", type=Path, required=True, help="inventory CSV from the inventory command")
    git_parser.add_argument("--status", action="append", required=True,
                            help="inventory status to replace, e.g. stock; repeat for more")
    git_parser.add_argument("--course", dest="course_keys", action="append", default=[],
                            help="only this course run; repeat for more")
    git_parser.add_argument("--allow", action="append", default=[],
                            help="sha256 of a repository's copy that may be replaced, beyond the inventory's")
    git_parser.add_argument(
        "--include-export-repos", action="store_true",
        help="also update runs that are only exported to git (Studio's next export would anyway)",
    )
    git_parser.add_argument(
        "--remote", dest="remotes", action="append", default=[], metavar="NAME=URL",
        help="remote URL of an imported repository, by the name in git_import; repeat for more",
    )
    git_parser.add_argument(
        "--remote-prefix", default="",
        help="remote of any other imported repository, before its name, e.g. git@github.mit.edu:mitx/",
    )
    git_parser.add_argument(
        "--push-branch",
        help="branch to push each change to; the import branch itself (e.g. live) re-imports the run",
    )
    git_parser.add_argument("--open-pr", action="store_true",
                            help="open a pull request from --push-branch to the import branch (needs gh)")
    git_parser.add_argument("--message", help="commit message (default: names the file and its new hash)")
    git_parser.add_argument("--dry-run", action="store_true", help="report what would change, push nothing")
    git_parser.add_argument("--work-dir", type=Path, default=Path("course-repos"),
                            help="where to fetch the repositories (default: %(default)s)")
    git_parser.add_argument("-o", "--output", type=Path, default=Path("git-report.csv"))

    args = parser.parse_args(argv)
    if args.command == "known":
        known = known_from_git(Path(__file__).resolve().parent.parent)
        args.output.write_text(json.dumps(known, indent=2, sort_keys=True) + "\n")
        print(f"Wrote {args.output} ({len(known['MJxPrep.js'])} versions of MJxPrep.js)")
        return 0

    if args.command == "inventory":
        known = json.loads(args.known.read_text())
        store = StudioStore()
        with open(args.output, "w", newline="") as out:
            writer = csv.DictWriter(out, INVENTORY_FIELDS)
            writer.writeheader()
            rows = run_inventory(store, writer, store.course_runs(args.course_keys, args.include_archived),
                                 args.filenames or DEFAULT_FILES, known, store.rerun_counts())
        print(f"Wrote {args.output} ({rows} rows) at {datetime.datetime.now(datetime.timezone.utc):%Y-%m-%dT%H:%MZ}")
        return 0

    if "/" in args.filename or "\\" in args.filename:
        parser.error("--filename is the asset's name, e.g. MJxPrep.js, not a path")
    replacement = args.replacement.read_bytes()
    if zipfile.is_zipfile(io.BytesIO(replacement)) != args.filename.endswith(".zip"):
        parser.error(f"--replacement {args.replacement} doesn't look like a {args.filename}")
    if args.command == "git-replace":
        return git_replace_main(parser, args, replacement)
    course_keys = list(args.course_keys)
    allowed = {value.lower() for value in args.allow}
    if args.allow_file:
        allowed |= read_hashes(args.allow_file.read_text())
    if args.inventory:
        if not args.status:
            parser.error("--inventory needs --status, e.g. --status stock")
        with args.inventory.open(newline="") as rows:
            selected, hashes = select_from_inventory(csv.DictReader(rows), args.filename, set(args.status))
        course_keys += [key for key in selected if key not in course_keys]
        allowed |= hashes
    if not course_keys:
        parser.error("no course runs selected; pass --course or --inventory with --status")
    if not allowed:
        parser.error("no allowed hashes; pass --allow, --allow-file or --inventory with --status")
    store = StudioStore()
    parse_keys(store, course_keys)
    # "x": never overwrite an earlier run's report, the record of what it replaced
    with open(args.output, "x", newline="") as out:
        writer = csv.DictWriter(out, REPORT_FIELDS)
        writer.writeheader()
        counts = run_replace(store, writer, args.filename, replacement, course_keys, allowed,
                             args.dry_run, args.backup_dir)
    summary = ", ".join(f"{action} {count}" for action, count in sorted(counts.items()))
    print(f"{'Dry run: ' if args.dry_run else ''}{summary}. Report: {args.output}")
    return 0


def git_replace_main(parser, args, replacement):
    if not args.dry_run and not args.push_branch:
        parser.error("--push-branch is required unless --dry-run")
    if any("=" not in value for value in args.remotes):
        parser.error("--remote takes NAME=URL")
    remotes = dict(value.split("=", 1) for value in args.remotes)
    with args.inventory.open(newline="") as rows:
        rows = list(csv.DictReader(rows))
    if args.course_keys:
        rows = [row for row in rows if row["course_key"] in args.course_keys]
    __, allowed = select_from_inventory(rows, args.filename, set(args.status))
    allowed |= {value.lower() for value in args.allow}
    targets = git_targets(rows, args.filename, set(args.status), args.include_export_repos,
                          args.remote_prefix, remotes)
    if not targets:
        parser.error("no runs selected that are imported from git (or, with --include-export-repos, exported)")
    message = args.message or f"Replace static/{args.filename} (sha256 {sha256(replacement)[:12]})"
    args.work_dir.mkdir(parents=True, exist_ok=True)
    with open(args.output, "x", newline="") as out:
        writer = csv.DictWriter(out, GIT_REPORT_FIELDS)
        writer.writeheader()
        counts = run_git_replace(writer, args.filename, replacement, targets, allowed, args.work_dir,
                                 args.push_branch, message, args.dry_run, args.open_pr)
    summary = ", ".join(f"{action} {count}" for action, count in sorted(counts.items()))
    print(f"{'Dry run: ' if args.dry_run else ''}{summary}. Report: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
