"""
Toolkit - Common: Classes
"""

import importlib
import inspect
import logging
import types
from abc import ABC, ABCMeta
from typing import Callable

from . import registered as _registered
from .constants import REGISTERED_MODULE
from .exceptions import CyclicRegisteredClassError
from .utils import main_module_name

logger = logging.getLogger(__name__)


class _PostInitCaller(ABCMeta):
    """Enable post_init"""

    def __call__(cls, *args, **kwargs):
        obj = type.__call__(cls, *args, **kwargs)
        if post_init := getattr(obj, "__post_init__", False):
            post_init()
        return obj


class PostInitClass(metaclass=_PostInitCaller):
    """Class with a __post_init__ support"""


class _RegisteredClassM(_PostInitCaller):
    """
    Helper metaclass for RegisteredClass

    (post_init enabled)
    """

    __refs__: dict[Callable] = {}

    def __new__(mcs, name, bases, dct, **kwargs):
        # Base registration classes provide the registered_class kwarg as True
        if kwargs.get("registered_class", False):
            return super().__new__(mcs, name, bases, dct)

        # Actual classes should contain class_name (comes from name in decorator - or automatically retrieved by it)
        class_name = kwargs.get("class_name")
        if class_name is None:
            raise CyclicRegisteredClassError("class_name is required for RegisteredClass")

        filtered_bases = filter(lambda base: base.__name__[len(base.__name__) - len(class_name) :] == class_name, bases)
        cb = next(filtered_bases)

        if clz := _RegisteredClassM.__refs__.get(cb, False):
            raise CyclicRegisteredClassError(f"Class {cb} already is registered with: {clz}")

        reg_clz = super().__new__(mcs, name, bases, dct)
        logger.debug(f"Registering class {cb} as {reg_clz}")
        _RegisteredClassM.__refs__[cb] = reg_clz

        class_name = cb.__name__
        setattr(_registered, class_name, cb)

        # Add references for static methods
        reg_clz_attrs = reg_clz.__dict__.copy()
        for k, v in reg_clz_attrs.items():
            if isinstance(v, staticmethod):
                logger.debug(f"Registering static method `{k}` from {reg_clz} to {cb}")
                setattr(cb, k, reg_clz.__dict__[k])

        cb.__original_name = reg_clz.__name__
        return reg_clz


class RegisteredClass(ABC, metaclass=_RegisteredClassM, registered_class=True):
    """
    Special metaclass that allows class registration
    Meaning that if there's a class A and class B that inherits from A, then calling A() will in fact call B() instead
    However - name of the B class has to be maintained the same (module can differ)
    """

    def __new__(cls, *_, **__):
        create = _RegisteredClassM.__refs__.get(cls, cls)
        if create.__module__ == REGISTERED_MODULE:
            raise CyclicRegisteredClassError(
                f"Class {create} was not registered, registered class should be imported, e.g. in root module: {main_module_name()}"
            )
        try:
            logger.debug(f"Creating object of registered class {cls} from {create}")
            return super().__new__(create)  # Do not pass args and kwargs to object()
        except TypeError as exc:
            raise CyclicRegisteredClassError(
                f"Could not instantiate object of class {cls} with registered class {create}, reason: [{exc}]"
            ) from exc


def create_registered_class(name: str):
    """Create a registered class"""
    dct = RegisteredClass.__dict__.copy()
    dct["__module__"] = REGISTERED_MODULE

    module = create_registered_module(name=name.rsplit(".", maxsplit=1)[0])
    mod_clz_name = name.rsplit(".", maxsplit=1)[-1]
    if clz := getattr(module, mod_clz_name, None):
        return clz

    clz = type(name, inspect.getmro(RegisteredClass), dct, registered_class=True)
    setattr(module, mod_clz_name, clz)

    return clz


def create_registered_module(name: str):
    """Create a registered module"""
    module = importlib.import_module(REGISTERED_MODULE)

    for mod_name in name.split("."):
        submodule = getattr(module, mod_name, None)
        if submodule is None:
            submodule = types.ModuleType(module.__name__ + "." + mod_name)
        setattr(module, mod_name, submodule)
        module = submodule
    return module
