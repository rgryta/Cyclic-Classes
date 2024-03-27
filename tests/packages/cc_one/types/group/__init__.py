from cyclic_classes.context import CyclicClassesImports
from cyclic_classes.decorators import register

with CyclicClassesImports():
    # pylint:disable=cyclic-import

    import subgroup
    from subgroup import SubGroup
    from cc_one.types.instance import Instance

    from ..instance import Instance
    from ..instance_two import Instance as _I


@register
class Group:

    @property
    def instances(self):
        return [Instance(param=3), Instance(param=4)]

    @property
    def subintances(self):
        return [i for s in self.instances for i in s.subinstances]

    @property
    def instances2(self):
        return [_I(), _I()]

    @property
    def subs(self):
        return [SubGroup(), SubGroup()]

    @property
    def subs2(self):
        return [subgroup.SubGroup(), SubGroup()]

    @classmethod
    def test(cls):
        return "THIS IS STATIC METHOD TEST"
