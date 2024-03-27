from cyclic_classes.context import CyclicClassesImports
from cyclic_classes.decorators import register

with CyclicClassesImports():
    from ...instance import Instance  # pylint:disable=cyclic-import


@register
class SubGroup:

    @property
    def instances(self):
        return [Instance(), Instance()]
