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
it goes away. To roll a course back, run ``replace`` with its backup as
``--replacement`` and ``--allow`` set to the new hash.

The runs' git exports aren't touched; they pick up the new file on the run's
next export. A run that is imported from git gets the old file back on its next
import unless its repository is updated too.

Only the standard library is used outside the edxapp environment, so ``known``
runs with plain ``python3``.
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
LIBRARY_PACKAGES = {"mitxgraders", "voluptuous"}
# Left by the tool that made the zip, not modules the course added
ZIP_NOISE = {"__MACOSX", "__pycache__", ".DS_Store"}
# What a damaged or unsupported zip member raises when read
ZIP_READ_ERRORS = (zipfile.BadZipFile, zlib.error, RuntimeError, NotImplementedError, EOFError)
VERSION_PATTERN = re.compile(rb"""__version__\s*=\s*["']([^"']+)["']""")
WHITESPACE = re.compile(rb"\s+")

INVENTORY_FIELDS = (
    "course_key", "display_name", "start", "end", "scope", "template", "reruns",
    "filename", "status", "version", "sha256", "size", "locked", "extras",
)
REPORT_FIELDS = ("course_key", "filename", "action", "old_sha256", "new_sha256", "backup")


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def normalized_sha256(data):
    """Hash ignoring whitespace, so re-indented or re-saved copies still match."""
    return sha256(WHITESPACE.sub(b"", data))


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
    except ZIP_READ_ERRORS:
        return "unreadable", "", []
    return status, match.group(1).decode() if match else "", extras


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
                labels.setdefault(normalized_sha256(data), f"{commit[:7]} ({date})")
    # Oldest tag first, so a version is labelled with the first release that had it
    tagged = {}
    for tag in _git(repo_root, "tag", "--sort=creatordate").decode().split():
        for path in MJXPREP_PATHS:
            data = _git_file(repo_root, tag, path)
            if data is not None:
                tagged.setdefault(normalized_sha256(data), tag)
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
    each write is read back. If a write fails, the old copy is written back
    and the run stops.

    :param store: a :class:`StudioStore`, or a stand-in for tests
    :param writer: csv.DictWriter with REPORT_FIELDS
    :returns: count of each action taken
    :rtype: dict[str, int]
    """
    new_sha256 = sha256(replacement)
    # Parse every key before writing anything, so a typo doesn't stop a run halfway
    parsed = [(key, store.parse(key)) for key in course_keys]
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
                    backup = backup_path(backup_dir, key, filename, old_sha256)
                    backup.parent.mkdir(parents=True, exist_ok=True)
                    if not backup.exists():
                        backup.write_bytes(old_data)
                    row["backup"] = str(backup)
                    try:
                        store.write(course_key, filename, current, replacement)
                        written = store.find(course_key, filename)
                        if written is None or sha256(bytes(written.data)) != new_sha256:
                            raise RuntimeError(f"{key}: {filename} didn't read back as {new_sha256}")
                    except Exception:
                        store.write(course_key, filename, current, old_data)
                        writer.writerow({**row, "action": "failed-restored"})
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
        self.clear_cache(course_key, filename)

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
                }

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

    replacement = args.replacement.read_bytes()
    if zipfile.is_zipfile(io.BytesIO(replacement)) != args.filename.endswith(".zip"):
        parser.error(f"--replacement {args.replacement} doesn't look like a {args.filename}")
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
    with open(args.output, "w", newline="") as out:
        writer = csv.DictWriter(out, REPORT_FIELDS)
        writer.writeheader()
        counts = run_replace(store, writer, args.filename, replacement, course_keys, allowed,
                             args.dry_run, args.backup_dir)
    summary = ", ".join(f"{action} {count}" for action, count in sorted(counts.items()))
    print(f"{'Dry run: ' if args.dry_run else ''}{summary}. Report: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
