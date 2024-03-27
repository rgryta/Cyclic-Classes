# pylint:disable=missing-docstring,too-few-public-methods
from cc_one.main import Main

from cyclic_classes.decorators import register


@register
class AClass:

    @property
    def main(self):
        return Main()
