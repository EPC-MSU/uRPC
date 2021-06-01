# from functools import lru_cache as memoize
from collections import namedtuple

from pyparsing import Regex, SkipTo, ParseException, OneOrMore, Optional, Suppress, Empty

Language = namedtuple("Language", ["code", "text"])


# directives
# _dsee = Suppress("@see")+SkipTo(LineEnd())
# _dparam = Suppress("@param")+SkipTo(LineEnd())
# _dname = Suppress("@name")+SkipTo(LineEnd())
#
#
# _text = Optional(_dname) + SkipTo(Or((Suppress(_dsee), Suppress(_dparam), StringEnd())), include=True)


def _build_language():
    # TODO: use regexp backreference
    def check_match(s, loc, toks):
        start = toks[0].strip()
        stop = toks[1][1].strip()
        if start[1:] != stop[4:]:
            raise ParseException("Language tags mismatch")
        code = start[1:]
        content = toks[1][0].strip()
        return Language(code, content)

    open_ = Regex(r"\\([a-zA-Z0-9]+?)\s")
    close = Regex(r"\\end([a-zA-Z0-9]+?)(\s|$)")

    return (open_ + SkipTo(close, include=True)).setParseAction(check_match)


_language = _build_language()


def _build_doxygen(spec):
    def is_meta(s):
        for m in ("@param", "@name", "@see"):
            if s.startswith(m):
                return True

    def normalize(s, loc, toks):
        decommented = (l.strip() for l in toks[0].replace("*", "").split("\n"))
        cleaned = " ".join(l.strip() for l in decommented if not is_meta(l))
        languages = OneOrMore(_language).parseString(cleaned, parseAll=True)
        return [languages]

    end = "*/"
    return (Suppress(r"/**") + Suppress(spec) + SkipTo(end) + Suppress(end)).setParseAction(normalize)


# Exported
inline = _build_doxygen(r"<")
reader = _build_doxygen(r"$XIR")
writer = _build_doxygen(r"$XIW")
struct = _build_doxygen(r"$XIS")
flagset = _build_doxygen(Empty())
OpenGroup = Suppress(Optional(Optional(_build_doxygen(Empty())) + r"//@{"))
CloseGroup = Suppress(Optional(r"//@}"))
