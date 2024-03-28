# pylint:disable=missing-docstring,too-few-public-methods
from cyclic_classes import register, cyclic_imports

with cyclic_imports():
    # pylint:disable=cyclic-import
    import submodule  # pylint:disable=import-error # Incorrect (but with CyclicClassesImport it still works, since IDE also is able to do so)
    import cc_one.amodule
    import module.submodule  # pylint:disable=import-error  # Incorrect (but with CyclicClassesImport it still works, since IDE also is able to do so)
    from nmodule import (  # pylint:disable=import-error  # Incorrect (but with CyclicClassesImport it still works, since IDE also is able to do so)
        Class,
    )
    from cc_one.mmodule import MClass

    from .anmodule import AClass
    from .snmodule import smodule
    from .asnmodule import smodule as amodule


@register
class Main:

    @property
    def s(self):
        return submodule.Class()

    @property
    def ms(self):
        return module.submodule.Class()

    @property
    def cc_am(self):
        return cc_one.amodule.Class()

    @property
    def nm(self):
        return Class()

    @property
    def an(self):
        return AClass()

    @property
    def sma(self):
        return smodule.Class()

    @property
    def asma(self):
        return amodule.Class()

    @property
    def cc_mm(self):
        return MClass()
