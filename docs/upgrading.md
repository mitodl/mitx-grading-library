# Upgrading a Course

Each course run keeps its own copy of `python_lib.zip` and `MJxPrep.js` in its static assets (Files & Uploads in Studio), so a new release only reaches learners once those copies are replaced, course run by course run. Copying or rerunning a course copies its assets too, so update the course you rerun from as well.

## Which version is a course running?

`MJxPrep.js` logs a line to the browser's developer console on any page with a problem that loads it:

```
MITx Grading Library (MJxPrep.js 3.1.0): Updated AsciiMath renderer definitions (MathJax 4.1.2)
```

The version is also available in the console as `window.MJxPrep.version`. Copies from before version 3.1.0 log `MITx Grading Library: Updated AsciiMath renderer definitions` with no version; those copies stop answer previews from working on MathJax 4.

For `python_lib.zip`, open the zip and read `mitxgraders/version.py`, or set `debug=True` on a grader and submit an answer: the debug output starts with `MITx Grading Library Version 3.1.0`.

## Where to download

Each [GitHub release](https://github.com/mitodl/mitx-grading-library/releases) has these files attached:

* `python_lib.zip`: the grading library, with `mitxgraders/` and `voluptuous/` at the top level
* `MJxPrep.js`: the AsciiMath renderer definitions and preprocessor
* `python_lib_zip.py`: a script that updates the library inside a `python_lib.zip` that also holds a course's own modules (see below)

The latest release's files are always at:

* [https://github.com/mitodl/mitx-grading-library/releases/latest/download/python_lib.zip](https://github.com/mitodl/mitx-grading-library/releases/latest/download/python_lib.zip)
* [https://github.com/mitodl/mitx-grading-library/releases/latest/download/MJxPrep.js](https://github.com/mitodl/mitx-grading-library/releases/latest/download/MJxPrep.js)
* [https://github.com/mitodl/mitx-grading-library/releases/latest/download/python_lib_zip.py](https://github.com/mitodl/mitx-grading-library/releases/latest/download/python_lib_zip.py)

## Updating MJxPrep.js

Upload the new `MJxPrep.js` to the course's static assets under the same name, replacing the old one.

If your course's copy was edited (different options, extra symbols, or code in `customPreReplacements`/`customPostReplacements`), move those changes into a separate `MJxPrepCustom.js` first, as described in [Customizing for a Course](grading_math/renderer.md#customizing-for-a-course). Otherwise uploading the new file drops them.

## Updating python_lib.zip

If your course's `python_lib.zip` only contains `mitxgraders/` and `voluptuous/`, upload the new `python_lib.zip` under the same name, replacing the old one.

If it also holds your course's own modules, download `python_lib.zip` and `python_lib_zip.py` from the release into the same folder as your course's zip (renamed, e.g. to `course_python_lib.zip`), and run:

```
python3 python_lib_zip.py update course_python_lib.zip --release python_lib.zip
```

This writes `python_lib.updated.zip`, with `mitxgraders/` and `voluptuous/` replaced by the release's and everything else from your course's zip kept as is, including any [plugins](plugins.md) you added to `mitxgraders/plugins/`. It prints the old and new library versions and what it kept, and warns if your zip had edited one of the library's own plugin files (such as `defaults_sample.py`), since the release's copy replaces it; move those changes into a plugin file of your own. It needs Python 3 and nothing else. Rename `python_lib.updated.zip` to `python_lib.zip` and upload it. If your zip has the library inside a folder (e.g. `python_lib/mitxgraders/`), the script stops and points you at [How to Zip Correctly](index.md#how-to-zip-correctly).

## Updating every course run on an Open edX instance

Platform operators can update many course runs at once with [`scripts/course_assets.py`](https://github.com/mitodl/mitx-grading-library/blob/master/scripts/course_assets.py), which runs inside a Studio (CMS) container. `inventory` writes a CSV for each active or upcoming run, plus the newest run of each template course, with its `MJxPrep.js` (stock, meaning it matches a version this repository has had, customized, or absent) and `python_lib.zip` (library version and any extra modules). `replace` then swaps the file only in runs whose current copy has a hash you allow, e.g. every run the inventory lists as stock, saves each copy it replaces, and reports what it changed. Run it with `--dry-run` first. The script's docstring has the full steps.
