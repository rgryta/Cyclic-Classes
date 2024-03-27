"""
Cyclic Classes - Decorators
"""

from __future__ import annotations

from .classes import get_registered_class


def register(cls):
    """Register a class with the cyclic_classes space"""
    # Get registered class which we'll register under
    registered_name = cls.__qualname__
    name = cls.__module__ + "." + registered_name
    registered = get_registered_class(name=name, qualname=registered_name)

    # Create a new class that will now be registered under the registered_class and return that instead
    new_cls = type(
        cls.__qualname__,
        (
            cls,
            registered,
        ),
        dict(cls.__dict__),
        class_name=registered_name,
    )
    return new_cls
