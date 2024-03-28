"""
Toolkit - Common: Classes
"""

from __future__ import annotations

import types
import inspect
import logging
from abc import ABC, ABCMeta
from typing import Callable

from . import registered as _registered
from .utils import main_module_name
from .constants import REGISTERED_MODULE
from .exceptions import CyclicRegisteredClassError

logger = logging.getLogger(__name__)


class _PostInitCaller(ABCMeta):
    """Enable post_init on a newly created class"""

    def __call__(cls, *args, **kwargs):
        obj = type.__call__(cls, *args, **kwargs)
        if post_init := getattr(obj, "__post_init__", False):
            post_init()
        return obj


class PostInitClass(metaclass=_PostInitCaller):  # pylint: disable=too-few-public-methods
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

        # Actual classes should contain class_name (comes from decorator)
        class_name = kwargs.get("class_name")
        if class_name is None:
            raise CyclicRegisteredClassError("class_name is required for RegisteredClass")

        # There should be a baseclass with cyclic_classes.registered <- pick this one
        expected_base_class = ".".join([REGISTERED_MODULE, dct["__module__"], class_name])
        filtered_bases = filter(lambda base: base.__module__ + "." + base.__qualname__ == expected_base_class, bases)
        cb = next(filtered_bases)

        if clz := _RegisteredClassM.__refs__.get(cb, False):
            raise CyclicRegisteredClassError(f"Class {cb} already is registered with: {clz}")

        # Create a Registered class within cyclic_classes.registered module
        reg_clz = super().__new__(mcs, name, bases, dct)
        logger.debug(f"Registering class {cb} as {reg_clz}")
        _RegisteredClassM.__refs__[cb] = reg_clz

        # Add references for static methods
        reg_clz_attrs = reg_clz.__dict__.copy()
        for k, v in reg_clz_attrs.items():
            if isinstance(v, (staticmethod, classmethod)):
                logger.debug(f"Registering static/class method `{k}` from {reg_clz} to {cb}")
                setattr(cb, k, reg_clz.__dict__[k])

        return reg_clz


class RegisteredClass(
    ABC, metaclass=_RegisteredClassM, registered_class=True
):  # pylint: disable=too-few-public-methods
    """
    Special metaclass that allows class registration
    Meaning that if there's a class A and class B that inherits from A, then calling A() will in fact call B() instead
    However - name of the B class has to be maintained the same (module can differ)
    """

    def __new__(cls, *_, **__):
        create = _RegisteredClassM.__refs__.get(cls, cls)
        if create.__module__.startswith(REGISTERED_MODULE):
            raise CyclicRegisteredClassError(
                f"Class {create} was not registered, registered class should be imported, e.g. in "
                f"root module: {main_module_name()}"
            )
        try:
            logger.debug(f"Creating object of registered class {cls} from {create}")
            return super().__new__(create)  # Do not pass args and kwargs to object()
        except TypeError as exc:
            raise CyclicRegisteredClassError(
                f"Could not instantiate object of class {cls} with registered class {create}, reason: [{exc}]"
            ) from exc


def _get_recursive(obj: object, name: str, qualname: str, obj_factory: Callable[[str], type]) -> type:
    """
    Get class recursively - create outer classes as needed

    Retrieve a class with `name` from the object `obj`. When the `name` is an inner class and outer classes were not yet
    created - recreate the structure locally.
    """
    if "." in name:
        # `Subname` is an inner class of `name`
        name, subname = name.split(".", maxsplit=1)

        if new_obj := getattr(obj, name, None):
            return _get_recursive(obj=new_obj, name=subname, qualname=qualname, obj_factory=obj_factory)
        new_obj = obj_factory(obj.__qualname__ + "." + name if hasattr(obj, "__qualname__") else name)
        setattr(obj, name, new_obj)
        return _get_recursive(obj=new_obj, name=subname, qualname=qualname, obj_factory=obj_factory)

    # `Name` is no longer splittable
    if new_obj := getattr(obj, name, None):
        return new_obj

    new_obj = obj_factory(qualname)
    setattr(obj, name, new_obj)
    return new_obj


def get_registered_class(name: str, qualname: str):
    """
    Create a registered class

    Based on a full name (module + qualname) and qualname create a new RegisteredClass class specific for the `name`
    class.
    """

    logger.debug(f"Getting registered class: {name}")

    def create_class(qualname: str) -> type:
        """
        Create RegisteredClass class
        """
        dct = RegisteredClass.__dict__.copy()
        dct["__module__"] = module.__name__
        clz = type(qualname, inspect.getmro(RegisteredClass), dct, registered_class=True)
        return clz

    module_name = name[0 : -len(qualname)]
    if module_name.endswith("."):
        module_name = module_name[:-1]
    module = get_registered_module(name=module_name if module_name else None)

    clz = _get_recursive(obj=module, name=qualname, qualname=qualname, obj_factory=create_class)
    return clz


def get_registered_module(name: str):
    """
    Create a registered module

    If we're registering a class from a package/module - which is in most cases, we're recreating the structure locally
    under cyclic_classes.registered submodule.
    """
    logger.debug(f"Getting registered module: {name}")
    module = _registered

    if name:
        for mod_name in name.split("."):
            submodule = getattr(module, mod_name, None)
            if submodule is None:
                submodule = types.ModuleType(module.__name__ + "." + mod_name)
                setattr(module, mod_name, submodule)
            module = submodule
    return module
