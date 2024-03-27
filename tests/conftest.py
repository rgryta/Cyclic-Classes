"""
Testing fixtures
"""

import sys
import shlex
import pathlib
import subprocess

import pytest

"""
[build-system]
requires = ["setuptools>=67.4.0"]
build-backend = "setuptools.build_meta"

[project]
name = "cc_one"
version = "0.0.1"

[tool.setuptools.package-dir]
"cc_one" = "cc_one"

"""


def packages_path():
    """
    Install local pip package
    """
    path = pathlib.Path(__file__).parent.resolve()
    return path / "packages"


sys.path.append(str(packages_path()))


@pytest.fixture
def cc_one():
    """Mock for Instance class"""

    import cc_one as cc  # pylint:disable=import-outside-toplevel

    return cc


@pytest.fixture
def cc_two():
    """Mock for Instance class"""

    import cc_two as cc  # pylint:disable=import-outside-toplevel

    return cc
