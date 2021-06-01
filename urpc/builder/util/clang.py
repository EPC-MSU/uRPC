from collections import OrderedDict
from itertools import chain

from urpc.util.accessor import split_by_type
from urpc.util.cconv import type_to_cstr
from version import BUILDER_VERSION_MAJOR, BUILDER_VERSION_MINOR, BUILDER_VERSION_BUGFIX, BUILDER_VERSION_SUFFIX, \
    BUILDER_VERSION


class _Argstruct:
    def __init__(self, name, args):
        self._name = name
        self._args = args

    @property
    def name(self):
        return self._name

    @property
    def members(self):
        for arg in self._args:
            decl = type_to_cstr(arg.type_, arg.name)
            yield (decl, arg.description)

    @property
    def empty(self):
        return bool(len(self._args))

    @property
    def children(self):
        return self._args

    @property
    def args(self):
        return self._args

    @property
    def fields(self):
        return self._args


class _Flagset:
    def __init__(self, arg):
        self._arg = arg

    @property
    def name(self):
        return self._arg.name + "_flagset"

    @property
    def members(self):
        for c in self._arg.children:
            name = c.name.upper()
            value = hex(c.value)
            yield (name, value, c.description)


def get_argstructs(commands, accessors):
    argstructs = OrderedDict()

    for cmd in commands:
        request, response = cmd.request, cmd.response
        in_name, out_name = cmd.name + "_t", cmd.name + "_t"
        if len(response.args) and len(request.args) and not response.compare(request):
            in_name, out_name = "in_" + in_name, "out_" + out_name

        argstructs[request] = _Argstruct(in_name, request.args)
        argstructs[response] = _Argstruct(out_name, response.args)

    for (getter, setter) in accessors:
        name = getter.name[4:]
        in_name, out_name = name + "_t", name + "_t"
        if len(getter.response.args) and len(setter.request.args) and not getter.response.compare(setter.request):
            in_name, out_name = "in_" + in_name, "out_" + out_name

        argstructs[setter.request] = _Argstruct(in_name, setter.request.args)
        argstructs[setter.response] = _Argstruct(in_name, setter.response.args)
        argstructs[getter.request] = _Argstruct(out_name, getter.request.args)
        argstructs[getter.response] = _Argstruct(out_name, getter.response.args)

    return argstructs


def unique_argstructs_iter(argstructs):
    seen = set()
    for msg, s in argstructs.items():
        if s.name in seen or not len(msg.children):
            continue
        seen.add(s.name)
        yield s


def flagset_arg_iter(commands, accessors):
    # iterate only simple commands and accessors - otherwise there will be duplicated flagsets for accessors
    for cmd in chain(commands, (acc[0] for acc in accessors)):
        for msg in cmd.children:
            for arg in msg.children:
                if len(arg.children) == 0:
                    continue
                yield arg


def non_empty_unique_argstructs_iter(argstructs):
    seen = set()
    for struct in argstructs:
        if struct.name in seen or len(struct.children) == 0:
            continue
        seen.add(struct.name)
        yield struct


def library_shared_file(protocol):
    return protocol.name.lower()


def library_header_file(protocol):
    return protocol.name.lower()


def namespace_symbol(protocol, symbol):
    return "{}_{}".format(protocol.name, symbol)


class ClangView:
    BUILDER_VERSION_MAJOR = BUILDER_VERSION_MAJOR
    BUILDER_VERSION_MINOR = BUILDER_VERSION_MINOR
    BUILDER_VERSION_BUGFIX = BUILDER_VERSION_BUGFIX
    BUILDER_VERSION_SUFFIX = BUILDER_VERSION_SUFFIX
    BUILDER_VERSION = BUILDER_VERSION

    def __init__(self, project):
        self._project = project

        # convert from iterators to sequences
        commands, accessors = split_by_type(project.children)
        self._commands = list(commands)
        self._accessors = list(accessors)

        self._argstructs = get_argstructs(self._commands, self._accessors)

    @property
    def version(self):
        return self._project.version

    @property
    def name(self):
        return self._project.name.lower()

    @property
    def flagsets(self):
        for arg in flagset_arg_iter(self._commands, self._accessors):
            yield _Flagset(arg)

    @property
    def argstructs(self):
        return unique_argstructs_iter(self._argstructs)

    def library_shared_file(self, protocol):
        return library_shared_file(protocol)

    def library_header_file(self, protocol):
        return library_header_file(protocol)
