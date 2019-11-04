from marshmallow import Schema, fields


class CommandSchema(Schema):
    command = fields.Str()
