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


class SpindleSpeedSchema(CommandSchema):
    @validates('command')
    def validate_spindle_speed(self, value):
        if value != "spindle_increase" and value != "spindle_decrease":
            raise ValidationError(
                "Unknown command. Command must be either spindle_increase or spindle_decrease")


class SpindleBrakeSchema(CommandSchema):
    @validates("command")
    def validate_spindle_brake(self, value):
        if value != "brake_engaged" and value != "brake_disengaged":
            raise ValidationError(
                "Unknown command. Command must be either brake_engaged or brake_disengaged")


class SpindleDirectionSchema(CommandSchema):
    @validates("command")
    def validate_spindle_direction(self, value):
        if value != "spindle_reverse" and value != "spindle_forward":
            raise ValidationError(
                "Unknown command. Command must be either spindle_reverse or spindle_forward")


class SpindleEnabledSchema(CommandSchema):
    @validates("command")
    def validate_spindle_enabled(self, value):
        if value != "spindle_on" and value != "spindle_off":
            raise ValidationError(
                "Unknown command. Command must be either spindle_on or spindle_off")


class SpindleOverrideSchema(Schema):
    command = fields.Float(required=True, strict=True)


class StatusSchema(CommandSchema):
    @validates("command")
    def validate_status(self, value):
        if value != "power" and value != "estop":
            raise ValidationError(
                "Unknown command. Command must be either estop or power")


class UpdateQueueSchema(Schema):
    new_queue = fields.List(fields.String())


class OpenFileSchema(Schema):
    name = fields.String(required=True)
