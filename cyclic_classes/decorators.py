from __future__ import annotations

import inspect

from .classes import create_registered_class


def register(cls):
    registered_name = cls.__qualname__
    registered = create_registered_class(name=cls.__module__ + "." + registered_name)

    parent_bases = inspect.getmro(registered)
    child_bases = tuple(set(inspect.getmro(cls)) - {cls})
    bases = tuple([item for item in parent_bases if item not in child_bases]) + child_bases

    new_cls = type(cls.__qualname__, bases, dict(cls.__dict__), class_name=registered_name)
    return new_cls
