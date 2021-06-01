from collections import namedtuple
from enum import Enum


class AttributeSet:
    def __init__(self, include, exclude):
        self.include = include
        self.exclude = exclude


class Protocol:
    def __init__(self, version, attributes, flagsets, commands):
        self.version = version
        self.attributes = attributes
        self.flagsets = flagsets
        self.commands = commands


class Flagset:
    def __init__(self, name, members, description):
        self.name = name
        self.members = members
        self.description = description


class FlagsetMember:
    def __init__(self, name, value, description):
        self.name = name
        self.value = value
        self.description = description


class Attribute(Enum):
    crc = 1
    answer = 2
    public = 3
    inline = 4
    dualsync = 5
    lock = 6
    publicstruct = 7


class RoleType(Enum):
    reader = 1
    writer = 2
    universal = 3


Role = namedtuple("Role", ("type", "cid", "size"))


class CommandDescription:
    def __init__(self, reader, writer, struct, reader_calb, writer_calb, struct_calb):
        self.reader = reader
        self.writer = writer
        self.struct = struct
        self.reader_calb = reader_calb
        self.writer_calb = writer_calb
        self.struct_calb = struct_calb


class Command:
    def __init__(self, name, roles, attributes, fields, answer, description):
        self.name = name
        self.roles = roles
        self.attributes = attributes
        self.fields = fields
        self.answer = answer
        self.description = description


class PreModifier(Enum):
    normal = 0
    calb = 1


class PostModifier(Enum):
    serviceanswer = 0
    serviceresult = 1


class ReservedField:
    def __init__(self, size, description):
        self.size = size
        self.description = description


class FlagsetField:
    def __init__(self, _type, name, flagset, description):
        self.type_ = _type
        self.name = name
        self.flagset = flagset
        self.description = description


class NormalField:
    def __init__(self, premod, _type, postmod, name, metalen, description):
        self.premod = premod
        self.type_ = _type
        self.postmod = postmod
        self.name = name
        self.metalen = metalen
        self.description = description
