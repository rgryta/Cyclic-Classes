"""
Testing fixtures
"""

import sys
import pathlib


def packages_path():
    """
    Install local pip package
    """
    path = pathlib.Path(__file__).parent.resolve()
    return path / "packages"


sys.path.append(str(packages_path()))
