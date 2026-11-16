"""
MJxPrep.js and python_lib.zip are released together under one version, which
the release workflow also checks against the tag
"""

import re
from pathlib import Path

from mitxgraders.version import __version__

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_mjxprep_version_matches_the_library_version():
    text = (REPO_ROOT / "MJxPrep.js").read_text()
    assert re.search(r"var MJXPREP_VERSION = '([^']+)';", text).group(1) == __version__


def test_readme_shows_this_version():
    readme = (REPO_ROOT / "README.md").read_text()
    assert re.search(rf"^Version {re.escape(__version__)} ", readme, re.MULTILINE)


def test_changelog_has_a_section_for_this_version():
    changelog = (REPO_ROOT / "docs" / "changelog.md").read_text()
    assert re.search(rf"^### Version {re.escape(__version__)}\b", changelog, re.MULTILINE)
