from warnings import warn
import re
from bidict import frozenorderedbidict
from urpc import ast
from urpc.util.accessor import split_by_type


clang_primitives = frozenorderedbidict((
    ("uint8_t", ast.Integer8u),
    ("uint16_t", ast.Integer16u),
    ("uint32_t", ast.Integer32u),
    ("uint64_t", ast.Integer64u),
    ("int8_t", ast.Integer8s),
    ("int16_t", ast.Integer16s),
    ("int32_t", ast.Integer32s),
    ("int64_t", ast.Integer64s),
    ("float", ast.Float),
))


def cstr_to_type(cstr, array_length=None):
    result = None
    try:
        result = clang_primitives[cstr]
    except KeyError:
        all_types = "|".join(clang_primitives.keys())
        # match C style array declaration e.g. int32_t abcd[42]
        match = re.match(r"(?P<type>" + all_types + ") (?:[_a-zA-Z][_a-zA-Z0-9]{0,30})+(?P<length>\\[[0-9]+\\])$", cstr)
        if array_length and not match:
            raise ValueError("Wrong C type supplied")

        result = clang_primitives[match.group("type")]
        array_length = match.group("length")

    if array_length:
        result = ast.Array(result, int(array_length))
    return result


def type_to_cstr(type_obj, cidentifier=None):
    assert isinstance(type_obj, ast.FieldType)
    array_length = ""
    if isinstance(type_obj, ast.Array):
        array_length = "[{}]".format(len(type_obj))
        type_obj = type_obj.type
    try:
        base = clang_primitives.inv[type_obj]
        if cidentifier:
            return "{} {}{}".format(base, cidentifier, array_length)
        return base, array_length
    except KeyError:
        raise ValueError("Unknown type class supplied")


def ascii_to_hex(text):
    return "0x" + "".join("%0.2X" % ord(c) for c in reversed(text))


def get_msg_len(msg):
    assert isinstance(msg, ast.Message)
    cid_len_bytes = 4
    crc_len_bytes = 2
    return cid_len_bytes + sum(a.type.size for a in msg.args) + (crc_len_bytes if len(msg.args) else 0)


def build_argstructs(commands, accessors):
    from urpc.builder.util.clang import get_argstructs

    warn("for backward-compatibility use urpc.builder.util.clang", DeprecationWarning)

    return get_argstructs(commands, accessors)


def constants_iter(commands):
    from itertools import chain
    messages = chain.from_iterable((cmd.request, cmd.response) for cmd in commands)
    arguments = chain.from_iterable(msg.args for msg in messages)
    constants = chain.from_iterable(arg.consts for arg in arguments)

    seen = set()
    for const in constants:
        tpl = (const.name, const.value)
        if tpl in seen:
            continue
        seen.add(tpl)
        yield const


def argstructs_iter(commands):
    seen = set()
    for argstruct in build_argstructs(*split_by_type(commands)).values():
        if argstruct.name in seen or not len(argstruct.fields) or not argstruct.name:
            continue
        seen.add(argstruct.name)

        yield argstruct
