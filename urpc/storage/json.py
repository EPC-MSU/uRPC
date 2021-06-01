import re
from io import TextIOWrapper
from uuid import UUID

from marshmallow import fields, Schema, post_load

from urpc import ast


class TypeField(fields.Field):
    def __init__(self):
        # Because "type" is keyword in Python, we will use other variable name
        super(TypeField, self).__init__(dump_to="type", load_from="type")

    # TODO: replace with dconv
    def _from_base_type(self, type_obj):
        if isinstance(type_obj, ast.IntegerType):
            return ("" if type_obj.signed else "u") + "int" + str(type_obj.size * 8)
        elif isinstance(type_obj, ast.FloatType):
            return "float"

    def _from_type(self, type_obj):
        if isinstance(type_obj, ast.ArrayType):
            return self._from_base_type(type_obj.type_) + "[{}]".format(len(type_obj))
        else:
            return self._from_base_type(type_obj)

    def _serialize(self, value, attr, obj):
        return self._from_type(value)

    def _to_base_type(self, type_str):
        if type_str == "float":
            return ast.Float
        elif type_str == "int64":
            return ast.Integer64s
        elif type_str == "uint64":
            return ast.Integer64u
        elif type_str == "int32":
            return ast.Integer32s
        elif type_str == "uint32":
            return ast.Integer32u
        elif type_str == "int16":
            return ast.Integer16s
        elif type_str == "uint16":
            return ast.Integer16u
        elif type_str == "uint8":
            return ast.Integer8u
        elif type_str == "int8":
            return ast.Integer8s
        raise ValueError("wrong int size")

    def _deserialize(self, value, attr, data):
        parsed = re.search(r"(?P<type>[u]?int[1-9]+?|float)(?:\[(?P<length>[0-9]+?)\])?$", data["type"])

        base_type = self._to_base_type(parsed.group("type"))
        length = parsed.group("length") or False

        return ast.ArrayType(base_type, int(length)) if length else base_type


class DescriptionField(fields.Field):
    def _format_text(self, text):
        return text.replace("\r", "")

    def _serialize(self, value, attr, obj):
        return {lang: self._format_text(text) for lang, text in dict(value).items()}

    def _deserialize(self, value, attr, data):
        result = ast.AstNode.Description()
        for k, v in value.items():
            result[k] = self._format_text(v)
        return result


class UuidField(fields.Field):
    def _serialize(self, value, attr, obj):
        assert isinstance(value, UUID)
        return str(value)

    def _deserialize(self, value, attr, data):
        return UUID(value)


class FlagConstantSchema(Schema):
    name = fields.String()
    value = fields.Integer()
    description = DescriptionField()
    extra_options = fields.String(required=False)
    uid = UuidField(required=True)

    @post_load
    def decode(self, data):
        return ast.FlagConstant(**data)


class ArgumentSchema(Schema):
    name = fields.String()
    type_ = TypeField()
    description = DescriptionField()
    consts = fields.Nested(FlagConstantSchema, many=True)
    extra_options = fields.String(required=False)
    uid = UuidField(required=True)

    @post_load
    def decode(self, data):
        return ast.Argument(**data)


class MessageSchema(Schema):
    args = fields.Nested(ArgumentSchema, many=True)
    description = DescriptionField()
    extra_options = fields.String(required=False)
    uid = UuidField(required=True)

    @post_load
    def decode(self, data):
        return ast.Message(**data)


class CommandSchema(Schema):
    name = fields.String()
    cid = fields.String()
    request = fields.Nested(MessageSchema)
    response = fields.Nested(MessageSchema)
    description = DescriptionField()
    extra_options = fields.String(required=False)
    uid = UuidField(required=True)

    @post_load
    def decode(self, data):
        return ast.Command(**data)


class ProtocolSchema(Schema):
    name = fields.String()
    version = fields.String()
    project_name = fields.String()
    commands = fields.Nested(CommandSchema, many=True)
    extra_options = fields.String(required=False)
    uid = UuidField(required=True)

    @post_load
    def decode(self, data):
        protocol = ast.Protocol(**data)

        return protocol


class JsonStorage:
    def __init__(self):
        self._schema = ProtocolSchema()

    def save(self, protocol, output):
        data, errors = self._schema.dumps(protocol, ensure_ascii=False, indent=2, sort_keys=True)
        if len(errors):
            raise ValueError(errors)
        text_output = TextIOWrapper(output, encoding="utf-8")
        text_output.write(data)
        text_output.flush()
        text_output.detach()

    def load(self, _input):
        text_input = TextIOWrapper(_input, encoding="utf-8")
        protocol, errors = self._schema.loads(text_input.read())
        text_input.flush()
        text_input.detach()
        if len(errors):
            raise ValueError(errors)

        return protocol

    def init(self):
        # Empty function for flake8
        return None
