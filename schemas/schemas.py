from marshmallow import Schema, fields, validates, ValidationError
import json

with open("./jsonFiles/errorMessages.json") as f:
    MESSAGE = json.load(f)


class CommandSchema(Schema):
    """Basic schema for commands"""
    command = fields.Str(required=True)

    @validates('command')
    def validate_command(self, value):
        if len(value) < 1:
            raise ValidationError(MESSAGE['input-empty'])


class HomeSchema(CommandSchema):
    """Schema that validates the input for the home API endpoint"""
    command = fields.Str(required=True)

    @validates('command')
    def validate_command(self, value):
        # CommandSchema().validate_command(value)
        if value != "home" and value != "unhome":
            raise ValidationError(MESSAGE['invalid-home-command'])


class ManualControlSchema(Schema):
    """Schema that validates the input for the manual control API endpoint"""
    axes = fields.Integer(required=True, strict=True)
    speed = fields.Float(required=True)
    increment = fields.Float(required=True)


class ProgramSchema(CommandSchema):
    """Schema that validates the input for the program API endpoint"""
    @validates('command')
    def validate_program(self, value):
        if value != "start" and value != "pause" and value != "stop" and value != "resume":
            raise ValidationError(MESSAGE['invalid-program-command'])


class SpindleSpeedSchema(CommandSchema):
    """Schema that validates the input for the spindle speed control API endpoint"""
    @validates('command')
    def validate_spindle_speed(self, value):
        if value != "spindle_increase" and value != "spindle_decrease":
            raise ValidationError(MESSAGE['invalid-spindle-speed-command'])


class SpindleBrakeSchema(CommandSchema):
    """Schema that validates the input for the spindle brake API endpoint"""
    @validates("command")
    def validate_spindle_brake(self, value):
        if value != "brake_engaged" and value != "brake_disengaged":
            raise ValidationError(MESSAGE['invalid-spindle-brake-command'])


class SpindleDirectionSchema(CommandSchema):
    """Schema that validates the input for the spindle direction API endpoint"""
    @validates("command")
    def validate_spindle_direction(self, value):
        if value != "spindle_reverse" and value != "spindle_forward":
            raise ValidationError(MESSAGE['invalid-spindle-direction-command'])


class SpindleEnabledSchema(CommandSchema):
    """Schema that validates the input for the spindle enabled API endpoint"""
    @validates("command")
    def validate_spindle_enabled(self, value):
        if value != "spindle_on" and value != "spindle_off":
            raise ValidationError(MESSAGE['invalid-spindle-enabled-command'])


class SpindleOverrideSchema(Schema):
    """Schema that validates the input for the spindle override API endpoint"""
    command = fields.Float(required=True)

    @validates("command")
    def validate_min_max(self, value):
        if value < 0 or value > 1:
            raise ValidationError(MESSAGE['invalid-range'])


class FeedOverrideSchema(Schema):
    """Schema that validates the input for the feed override API endpoint"""
    command = fields.Float(required=True)

    @validates("command")
    def validate_min_max(self, value):
        if value < 0 or value > 1.2:
            raise ValidationError(MESSAGE['invalid-range'])


class MaxvelOverrideSchema(Schema):
    """Schema that validates the input for the max velocity API endpoint"""
    command = fields.Float(required=True)


class StatusSchema(CommandSchema):
    """Schema that validates the input for the machine status API endpoint"""
    @validates("command")
    def validate_status(self, value):
        if value != "power" and value != "estop":
            raise ValidationError(MESSAGE['invalid-status-command'])


class UpdateQueueSchema(Schema):
    """Schema that validates the input for the file_queue/files on server API endpoint"""
    new_queue = fields.List(fields.String())


class OpenFileSchema(Schema):
    """Schema that validates the input for the open file API endpoint"""
    name = fields.String(required=True)


class HalcmdSchema(Schema):
    """Schema that validates the input for the HALCMD API endpoint"""
    halcmd = fields.String(required=True)

    @validates("halcmd")
    def validate_halcmd(self, value):
        with open("./jsonFiles/halCommands.json") as f:
            halCommands = json.load(f)

        user_command = value.split(' ', 1)[0]
        is_in_list = False
        for command in halCommands:
            if command['command'] == user_command:
                is_in_list = True
                break

        if not is_in_list:
            raise ValidationError(MESSAGE['invalid-command'])

        if "&&" in value:
            raise ValidationError(MESSAGE['invalid-multiple-commands'])
