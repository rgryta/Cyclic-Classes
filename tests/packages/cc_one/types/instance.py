from cyclic_classes.context import CyclicClassesImports
from cyclic_classes.decorators import register

with CyclicClassesImports():
    import cc_one.types.group as group  # pylint:disable=cyclic-import

    from .group import subgroup  # pylint:disable=cyclic-import


@register
class Instance:

    def __init__(self, param):
        self.param = param

    @property
    def group(self):
        return group.Group()

    @staticmethod
    def group():
        print(group.Group)
        return group.Group.test()

    @register
    class SubInstance:

        @property
        def instance(self):
            return Instance()

        @register
        class SubSubInstance:

            @property
            def instance(self):
                return Instance(param=100)

            @classmethod
            def groups(cls):
                return cls()

    @property
    def subinstances(self):
        return [Instance.SubInstance.SubSubInstance()]