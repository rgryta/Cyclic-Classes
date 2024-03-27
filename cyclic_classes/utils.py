"""
Cyclic Classes - Utils
"""

from __future__ import annotations

import os
import sys
from pathlib import PurePath

import __main__


def main_module_name() -> str | None:
    """
    Retrieve the name of main module
    """
    package = __main__.__package__
    if package is None:
        package = __main__.__package__
        if not package:
            if hasattr(__main__, "__file__"):
                package = PurePath(__main__.__file__).parts[-1]
            else:
                path = sys.argv[0]
                if os.path.exists(path):
                    package = PurePath(path).parts[-1]
                else:
                    package = path.split("/")[-1].split("\\")[-1]
    return package
