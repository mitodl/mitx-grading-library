"""Build python_lib.zip, or update the library inside a course's python_lib.zip.

Course teams run this with plain ``python3`` (no packages to install), so it
only uses the standard library.

Update a course's zip that also holds its own modules::

    python3 python_lib_zip.py update course_python_lib.zip --release python_lib.zip

Build the release zip from a checkout of this repository::

    python3 scripts/python_lib_zip.py build
"""

import argparse
import copy
import re
import sys
import zipfile
from pathlib import Path

LIBRARY_PACKAGES = ("mitxgraders", "voluptuous")
# Where course teams add their own plugins (docs/plugins.md)
PLUGINS_DIR = "mitxgraders/plugins/"
SKIPPED_NAMES = {"__pycache__", ".DS_Store"}
SKIPPED_SUFFIXES = {".pyc"}
# Fixed timestamp so building the same source twice gives the same bytes
ZIP_DATE_TIME = (1980, 1, 1, 0, 0, 0)
VERSION_PATTERN = re.compile(r"""__version__\s*=\s*["']([^"']+)["']""")


def _library_files(repo_root):
    """Yield (path on disk, name in zip) for the library, in sorted order."""
    for package in LIBRARY_PACKAGES:
        for path in sorted((repo_root / package).rglob("*")):
            relative = path.relative_to(repo_root)
            if (
                path.is_file()
                and not SKIPPED_NAMES.intersection(relative.parts)
                and path.suffix not in SKIPPED_SUFFIXES
            ):
                yield path, relative.as_posix()
    # Distributed with the library, as the old makezip.sh did
    yield repo_root / "LICENSE", "mitxgraders/LICENSE"


def build(output, repo_root):
    """Write python_lib.zip with mitxgraders and voluptuous at the top level.

    :param output: path of the zip file to write
    :param repo_root: root of a mitx-grading-library checkout
    :returns: the names written to the zip
    :rtype: list[str]
    """
    names = []
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for path, name in sorted(_library_files(repo_root), key=lambda item: item[1]):
            info = zipfile.ZipInfo(name, date_time=ZIP_DATE_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())
            names.append(name)
    return names


def _top_level(name):
    return name.split("/", 1)[0]


def _library_version(archive):
    try:
        text = archive.read("mitxgraders/version.py").decode("utf-8")
    except KeyError:
        return None
    match = VERSION_PATTERN.search(text)
    return match.group(1) if match else None


def _is_macos_metadata(name):
    # macOS Finder's Compress adds these resource-fork copies of every file
    return name.startswith("__MACOSX/")


def update(course_zip, release_zip, output):
    """Replace mitxgraders/ and voluptuous/ in a course's zip with a release's.

    Everything else in the course's zip (its own modules) is kept as is, and
    so are the course's own plugins in mitxgraders/plugins/ (see plugins.md).
    macOS __MACOSX/ metadata is dropped.

    :param course_zip: the course's current python_lib.zip
    :param release_zip: python_lib.zip from a mitx-grading-library release
    :param output: path of the updated zip to write
    :returns: (old library version, new library version, what was kept from
        the course's zip: top-level names, then plugin file paths, and the
        course's edited copies of release plugins that were replaced)
    :rtype: tuple[str | None, str | None, list[str], list[str]]
    :raises ValueError: if either zip has the library inside a folder instead
        of at the top level
    """
    with zipfile.ZipFile(course_zip) as course, zipfile.ZipFile(release_zip) as release:
        for label, archive in (("course", course), ("release", release)):
            nested = [
                name for name in archive.namelist()
                if "/mitxgraders/" in name
                and not name.startswith("mitxgraders/")
                and not _is_macos_metadata(name)
            ]
            if nested:
                raise ValueError(
                    f"The {label} zip has mitxgraders inside a folder "
                    f"({nested[0]}). edX needs mitxgraders/ at the top level of "
                    "python_lib.zip: zip the folder's contents, not the folder. See "
                    "https://mitodl.github.io/mitx-grading-library/#how-to-zip-correctly"
                )
        old_version = _library_version(course)
        new_version = _library_version(release)
        if new_version is None:
            raise ValueError(f"{release_zip} has no mitxgraders/version.py; is it a release python_lib.zip?")

        release_names = set(release.namelist())
        course_modules = []
        course_plugins = []
        replaced_plugins = []
        for info in course.infolist():
            name = info.filename
            if _is_macos_metadata(name):
                continue
            if _top_level(name) not in LIBRARY_PACKAGES:
                # Directory entries too: on Python 3.11/3.12, zipimport only
                # finds a package without __init__.py through its directory entry
                course_modules.append(info)
            elif info.is_dir() or not name.startswith(PLUGINS_DIR):
                continue
            elif name not in release_names:
                course_plugins.append(info)
            elif course.read(info) != release.read(name):
                replaced_plugins.append(name)

        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as updated:
            kept = course_modules + course_plugins
            for source, infos in ((course, kept), (release, release.infolist())):
                for info in infos:
                    # writestr rewrites the ZipInfo's offsets for the new file
                    updated.writestr(copy.copy(info), source.read(info))
        kept_names = sorted({_top_level(info.filename) for info in course_modules})
        kept_names += sorted(info.filename for info in course_plugins)
        return old_version, new_version, kept_names, sorted(replaced_plugins)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)

    build_parser = commands.add_parser("build", help="build python_lib.zip from this repository")
    build_parser.add_argument("-o", "--output", type=Path, default=Path("python_lib.zip"))

    update_parser = commands.add_parser(
        "update", help="replace the library in a course's python_lib.zip, keeping the course's own modules"
    )
    update_parser.add_argument("course_zip", type=Path, help="the course's current python_lib.zip")
    update_parser.add_argument(
        "--release", type=Path, default=Path("python_lib.zip"),
        help="python_lib.zip downloaded from a mitx-grading-library release (default: %(default)s)",
    )
    update_parser.add_argument(
        "-o", "--output", type=Path, default=Path("python_lib.updated.zip"),
        help="where to write the updated zip (default: %(default)s)",
    )

    args = parser.parse_args(argv)
    if args.command == "build":
        names = build(args.output, Path(__file__).resolve().parent.parent)
        print(f"Wrote {args.output} ({len(names)} files)")
        return 0

    if args.output.resolve() in (args.course_zip.resolve(), args.release.resolve()):
        parser.error("--output must be a new file, not one of the input zips")
    try:
        old, new, kept, replaced = update(args.course_zip, args.release, args.output)
    except ValueError as err:
        print(f"error: {err}", file=sys.stderr)
        return 1
    print(f"Wrote {args.output}: mitxgraders {old or 'not present'} -> {new}")
    print("Kept from the course's zip: " + (", ".join(kept) if kept else "nothing else"))
    for name in replaced:
        print(
            f"warning: the course's {name} differed from the release's and was replaced. "
            "Copy your changes into a plugin file of your own (see plugins.md).",
            file=sys.stderr,
        )
    print(f"Rename {args.output} to python_lib.zip and upload it to the course's Files & Uploads.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
