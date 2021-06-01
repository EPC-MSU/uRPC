from .oldxi import OldxiStorage
from .json import JsonStorage

# This is useless list
# but it is required for avoiding
# flake8 messages about unused modules
d = OldxiStorage()
f = JsonStorage()
_modules_to_be_used_by_parents = [d.init(), f.init()]
