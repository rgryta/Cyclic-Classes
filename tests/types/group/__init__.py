from cyclic_classes.context import CyclicClassesImports
from cyclic_classes.decorators import register

with CyclicClassesImports():
    from ..instance import Instance
    from ..instance_two import Instance as _I
    from .subgroup import SubGroup


@register
class Group:

    @property
    def instances(self):
        return [Instance(), Instance()]

    @property
    def instances2(self):
        return [_I(), _I()]

    @property
    def subs(self):
        return [SubGroup(), SubGroup()]
