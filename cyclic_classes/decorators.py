from __future__ import annotations

import inspect

from .classes import get_registered_class


def register(cls):
    # Get registered class which we'll register under
    registered_name = cls.__qualname__
    name = cls.__module__ + "." + registered_name
    registered = get_registered_class(name=name, qualname=registered_name)

    # Create a new class that will now be registered under the registered_class and return that instead
    parent_bases = inspect.getmro(registered)
    child_bases = tuple(set(inspect.getmro(cls)) - {cls})
    bases = tuple([item for item in parent_bases if item not in child_bases]) + child_bases

    new_cls = type(cls.__qualname__, bases, dict(cls.__dict__), class_name=registered_name)
    return new_cls
