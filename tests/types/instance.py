from cyclic_classes.context import CyclicClassesImports
from cyclic_classes.decorators import register

with CyclicClassesImports():
    import tests.types.group as group

import tests.types.group as _group2


@register
class Instance:

    @property
    def group(self):
        return group.Group()
