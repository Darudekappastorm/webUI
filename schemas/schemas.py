from marshmallow import Schema, fields, validates, ValidationError
import json

with open("./jsonFiles/errorMessages.json") as f:
    errorMessages = json.load(f)


class CommandSchema(Schema):
    command = fields.Str(required=True)

    @validates('command')
    def validate_command(self, value):
        if len(value) < 1:
            raise ValidationError(errorMessages['input-empty'])


class HomeSchema(CommandSchema):
    command = fields.Str(required=True)

    @validates('command')
    def validate_command(self, value):
        # CommandSchema().validate_command(value)
        if value != "home" and value != "unhome":
            raise ValidationError(errorMessages['invalid-home-command'])


class ManualControlSchema(Schema):
    axes = fields.Integer(required=True, strict=True)
    speed = fields.Float(required=True)
    increment = fields.Float(required=True)


class ProgramSchema(CommandSchema):
    @validates('command')
    def validate_program(self, value):
        if value != "start" and value != "pause" and value != "stop" and value != "resume":
            raise ValidationError(errorMessages['invalid-program-command'])


class SpindleSpeedSchema(CommandSchema):
    @validates('command')
    def validate_spindle_speed(self, value):
        if value != "spindle_increase" and value != "spindle_decrease":
            raise ValidationError(
                errorMessages['invalid-spindle-speed-command'])


class SpindleBrakeSchema(CommandSchema):
    @validates("command")
    def validate_spindle_brake(self, value):
        if value != "brake_engaged" and value != "brake_disengaged":
            raise ValidationError(
                errorMessages['invalid-spindle-brake-command'])


class SpindleDirectionSchema(CommandSchema):
    @validates("command")
    def validate_spindle_direction(self, value):
        if value != "spindle_reverse" and value != "spindle_forward":
            raise ValidationError(
                errorMessages['invalid-spindle-direction-command'])


class SpindleEnabledSchema(CommandSchema):
    @validates("command")
    def validate_spindle_enabled(self, value):
        if value != "spindle_on" and value != "spindle_off":
            raise ValidationError(
                errorMessages['invalid-spindle-enabled-command'])


class SpindleOverrideSchema(Schema):
    command = fields.Float(required=True, strict=True)


class StatusSchema(CommandSchema):
    @validates("command")
    def validate_status(self, value):
        if value != "power" and value != "estop":
            raise ValidationError(errorMessages['invalid-status-command'])


class UpdateQueueSchema(Schema):
    new_queue = fields.List(fields.String())


class OpenFileSchema(Schema):
    name = fields.String(required=True)


class HalcmdSchema(Schema):
    halcmd = fields.String(required=True)

    @validates("halcmd")
    def validate_halcmd(self, value):
        with open("./jsonFiles/halCommands.json") as f:
            halCommands = json.load(f)

        user_command = value.split(' ', 1)[0]
        isInList = False
        for command in halCommands:
            if command['command'] == user_command:
                isInList = True
                break

        if not isInList:
            raise ValidationError(errorMessages['invalid-command'])

        if "&&" in value:
            raise ValidationError(errorMessages['invalid-multiple-commands'])
