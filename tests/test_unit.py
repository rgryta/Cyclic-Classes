"""
Base cyclic classes unit tests
"""

import types

import pytest

from cyclic_classes import registered


def test_testing_packages_present(cc_one, cc_two):
    """
    Check if test packages are installed and available for testing
    """
    if not all([cc_one, cc_two]):
        pytest.fail("Had to reinstall testing packages, please re-execute unit tests")
    assert True


def test_registered():
    """
    Test if everything was registered properly
    """
    module = types.ModuleType("dummy")
    print(set(registered.__dict__.keys()) - set(module.__dict__.keys()))


def test_cc_one(cc_one):
    group = cc_one.Group()
    print(group)
    assert False
