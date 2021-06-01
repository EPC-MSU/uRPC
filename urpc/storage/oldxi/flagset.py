from pyparsing import OneOrMore, Suppress, Regex, Optional, Group

from urpc.storage.oldxi import doxygen, ast
from urpc.storage.oldxi.common import identifier


# utility
def _build_flagset():
    def normalize_member(s, loc, toks):
        return ast.FlagsetMember(toks[0], int(toks[1], 16), toks[2])

    def normalize_flagset(s, loc, toks):
        return ast.Flagset(toks[1], toks[2], toks[0])

    member_name = Regex("0[xX][0-9a-fA-F]+")
    member = (identifier + Suppress("=") + member_name + Optional(doxygen.inline, []))
    member.setParseAction(normalize_member)

    flagset_name = Suppress("flagset") + identifier + Suppress(":")
    flagset = Optional(doxygen.flagset, []) + flagset_name + Group(OneOrMore(member))
    flagset.setParseAction(normalize_flagset)

    return flagset


_flagset = _build_flagset()

# exported
flagset = doxygen.OpenGroup + _flagset + doxygen.CloseGroup
