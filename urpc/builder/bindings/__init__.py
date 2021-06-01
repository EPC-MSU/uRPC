from urpc.builder.bindings import csharp, python

# This is useless list
# but it is required for avoiding
# flake8 messages about unused modules
_modules_to_be_used_by_parents = [csharp.init(), python.init()]
