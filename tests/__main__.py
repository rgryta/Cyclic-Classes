from cyclic_classes.classes import RegisteredClass

from .types.group import Group
from .types.group.subgroup import SubGroup
from .types.instance import Instance
from .types.instance_two import Instance as Instance2

instance = Instance()
instance2 = Instance2()
group = Group()

print(RegisteredClass.__refs__)

print(instance)
print(instance.group)
print(instance2)
print(group)
print(group.instances)
print(group.instances2)
print([sub.instances for sub in group.subs])
