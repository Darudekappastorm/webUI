from marshmallow import Schema, fields, validates, ValidationError


class CommandSchema(Schema):
    command = fields.Str(required=True)

    @validates('command')
    def validate_command(self, value):
        if len(value) < 1:
            raise ValidationError("Cannot be empty")


class HomeSchema(CommandSchema):
    command = fields.Str(required=True)

    @validates('command')
    def validate_command(self, value):
        # CommandSchema().validate_command(value)
        if value != "home" and value != "unhome":
            raise ValidationError(
                "Unknown command. Command must be either home or unhome")


class ManualControlSchema(Schema):
    axes = fields.Integer(required=True, strict=True)
    speed = fields.Float(required=True)
    increment = fields.Float(required=True)


class ProgramSchema(CommandSchema):
    @validates('command')
    def validate_program(self, value):
        if value != "start" and value != "pause" and value != "stop" and value != "resume":
            raise ValidationError(
                "Unknown command. Command must be one of: start, pause, stop, resume")
