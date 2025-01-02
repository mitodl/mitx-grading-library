"""
This script is used to test the integration of the mitx-graders library with the Open edX platform.
Running a code that uses the functions provided by the library using the safe_exec function, and in the MIT course context,
to be able to use the python_lib.zip that contains the library.
"""

import logging
import os
import sys

import django
from opaque_keys.edx.keys import CourseKey
from xmodule.capa.safe_exec import safe_exec
from xmodule.contentstore.django import contentstore
from xmodule.util.sandboxing import SandboxService

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cms.envs.test")
django.setup()

log = logging.getLogger(__name__)

# Define the code to be executed
GRADING_CLASSES_CODE = """
from mitxgraders import (
    StringGrader,
    FormulaGrader,
    NumericalGrader,
    MatrixGrader,
    SingleListGrader,
    ListGrader,
    IntegralGrader,
    IntervalGrader,
    SumGrader,
)

"""


def execute_code(course_key_str):
    """
    Executes the provided code in a sandboxed environment with the specified course context.

    Args:
        course_key_str (str): The string representation of the course key.

    Returns:
        None
    """
    course_key = CourseKey.from_string(course_key_str)
    sandbox_service = SandboxService(
        course_id=course_key,
        contentstore=contentstore
    )
    zip_lib = sandbox_service.get_python_lib_zip()

    extra_files = []
    python_path = []

    if zip_lib is not None:
        extra_files.append(("python_lib.zip", zip_lib))
        python_path.append("python_lib.zip")

    safe_exec(
        code=GRADING_CLASSES_CODE,
        globals_dict={},
        python_path=python_path,
        extra_files=extra_files,
        slug="integration-test",
        limit_overrides_context=course_key_str,
        unsafely=False,
    )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python integration_test.py <course_key>")
        sys.exit(1)
    
    course_key_str = sys.argv[1]
    execute_code(course_key_str)
