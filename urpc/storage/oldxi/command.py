from pyparsing import Each, Suppress, Optional, ZeroOrMore, Or, CaselessLiteral, \
    Word, ParseException, Group, QuotedString, \
    OneOrMore
from pyparsing import nums

from urpc.storage.oldxi import ast, doxygen
import urpc.ast.types as ast_base
from urpc.storage.oldxi.common import identifier, exclude_attributes, include_attributes


def _build_ctype():
    tlist = (
        "int64s", "int64u", "int32s", "int32u", "int16u", "int16s", "int8u", "int8s", "float", "double", "char", "byte"
    )
    types = Or(CaselessLiteral(s) for s in tlist)
    return types


_ctype = _build_ctype()
_array = Optional(Suppress("[") + Word(nums) + Suppress("]"))


def str2ast_type(type_str, type_len=None):
    def extract_base_type(type_str):
        if type_str == "float":
            return ast_base.Float
        elif type_str == "int64s":
            return ast_base.Integer64s
        elif type_str == "int64u":
            return ast_base.Integer64u
        elif type_str == "int32s":
            return ast_base.Integer32s
        elif type_str == "int32u":
            return ast_base.Integer32u
        elif type_str == "int16u":
            return ast_base.Integer16u
        elif type_str == "int16s":
            return ast_base.Integer16s
        elif type_str == "int8u" or type_str == "byte":
            return ast_base.Integer8u
        elif type_str == "int8s" or type_str == "char":
            return ast_base.Integer8s
        else:
            raise ValueError("Wrong C type supplied")

    base_type = extract_base_type(type_str)
    if type_len:
        base_type = ast_base.Array(base_type, int(type_len))
    return base_type


def _normalize_type(s, loc, toks):
    type_str, type_len = toks[0], None
    if len(toks) == 4:
        # Normalize array declaration
        type_len = toks[3]
        del toks[3]
        # return toks [ast.Array(base_type, int(toks[4])), toks[1]]
    toks[0] = str2ast_type(type_str, type_len)
    return toks


def _build_normal_field():
    def normalize(s, loc, toks):
        return ast.NormalField(*toks)

    premod = Optional(Or(("calb", "normal")), None)
    postmod = Optional(Or(("serviceanswer", "serviceresult")), None)
    name_type_postmod = (_ctype + postmod + identifier + _array).setParseAction(_normalize_type)
    metalen = Optional("metalen", None)
    field = premod + name_type_postmod + metalen + Optional(doxygen.inline, [])

    return field.setParseAction(normalize)


_normal_field = _build_normal_field()


def _build_flagset_field():
    def normalize(s, loc, toks):
        return ast.FlagsetField(toks[0], toks[2], toks[3], toks[4])

    type_and_name = (_ctype + "flag" + identifier + _array).setParseAction(_normalize_type)
    field = type_and_name + Suppress("of") + identifier + Optional(doxygen.inline, [])

    return field.setParseAction(normalize)


_flagset_field = _build_flagset_field()


def _build_reserved_field():
    def normalize(s, loc, toks):
        return ast.ReservedField(int(toks[0]), toks[1])

    field = Suppress("reserved") + Word(nums) + Optional(doxygen.inline, [])

    return field.setParseAction(normalize)


_reserved_field = _build_reserved_field()

# Order matters cause _normal_field is more general then _flagset_field
_field = _flagset_field | _normal_field | _reserved_field


def _build_roles():
    def normalize(s, loc, toks):
        role_type = ast.RoleType[toks[0]]
        cid = toks[1]
        if role_type in (ast.RoleType.reader, ast.RoleType.writer) and not 3 <= len(cid) <= 4:
            raise ParseException("reader and writer cid must be 3 or 4 ascii symbols long")
        elif role_type is ast.RoleType.universal and len(cid) != 3:
            raise ParseException("universal cid must be exactly 4 ascii symbols long")
        return ast.Role(role_type, cid, int(toks[2]))

    def validate(s, loc, toks):
        role_types = {t.type for t in toks[0]}
        if role_types.issubset({ast.RoleType.reader, ast.RoleType.writer}) or role_types == {ast.RoleType.universal}:
            return True
        return False

    cid = QuotedString('"')
    size = Suppress("(") + Word(nums) + Suppress(")")

    role = (Or("reader writer universal".split()) + cid + size).setParseAction(normalize)

    return Group(OneOrMore(role)).addCondition(validate)


_roles = _build_roles()


def _build_attributes():
    def normalize(s, loc, toks):
        return ast.AttributeSet(toks.get("include", []), toks.get("exclude", []))

    attributes = Optional(Each((include_attributes, exclude_attributes)) | include_attributes | exclude_attributes)
    return attributes.setParseAction(normalize)


_attributes = _build_attributes()


def _build_command():
    def normalize(s, loc, toks):
        cmd = ast.Command(
            toks[3],
            toks[4].asList(),
            toks[5],
            toks[6],
            toks[7],
            ast.CommandDescription(
                toks[0],
                toks[1],
                toks[2]
            )
        )

        return cmd

    reader_descr = Optional(doxygen.reader, [])
    writer_descr = Optional(doxygen.writer, [])
    struct_descr = Optional(doxygen.struct, [])

    name = QuotedString('"')
    header = Optional(Suppress("service")) + Suppress("command") + name + _roles + _attributes

    fields = Optional(Suppress("fields:") + Group(ZeroOrMore(_field)), [])
    answer = Optional(Suppress("answer:") + Group(ZeroOrMore(_field)), [])

    # return description + _build_header() + request + response
    command = reader_descr + writer_descr + struct_descr + header + fields + answer
    return command.setParseAction(normalize)


_command = _build_command()

# exported
command = doxygen.OpenGroup + _command + doxygen.CloseGroup
