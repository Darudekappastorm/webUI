import json
import settings
from decorators.auth import auth
from decorators.errors import errors
from flask import Blueprint, request, escape
from schemas.schemas import SpindleSpeedSchema, SpindleBrakeSchema, SpindleDirectionSchema, SpindleEnabledSchema, SpindleOverrideSchema
from decorators.validate import validate
spindle = Blueprint('spindle', __name__)

with open("./jsonFiles/errorMessages.json") as f:
    MESSAGE = json.load(f)


@spindle.route("/machinekit/spindle/speed",
               endpoint='set_machinekit_spindle_speed',
               methods=["POST"])
@auth
@errors
@validate(SpindleSpeedSchema)
def set_machinekit_spindle_speed():
    """Control spindle speed"""
    data = request.sanitizedRequest
    command = escape(data["command"])
    return settings.controller.spindle_speed(command)


@spindle.route("/machinekit/spindle/brake",
               endpoint='set_machinekit_spindle_brake',
               methods=["POST"])
@auth
@errors
@validate(SpindleBrakeSchema)
def set_machinekit_spindle_brake():
    """Enable/disable spindle brake"""
    data = request.sanitizedRequest
    command = escape(data["command"])
    return settings.controller.spindle_brake(command)


@spindle.route("/machinekit/spindle/direction",
               endpoint='get_machinekit_spindle_direction',
               methods=["POST"])
@auth
@errors
@validate(SpindleDirectionSchema)
def set_machinekit_spindle_direction():
    """Control spindle direction"""
    data = request.sanitizedRequest
    command = escape(data['command'])
    return settings.controller.spindle_direction(command)


@spindle.route("/machinekit/spindle/enabled",
               endpoint='set_spindle_enabled',
               methods=["POST"])
@auth
@errors
@validate(SpindleEnabledSchema)
def set_spindle_enabled():
    """Enable/disable spindle"""
    data = request.sanitizedRequest
    command = escape(data["command"])
    return settings.controller.spindle_enabled(command)


@spindle.route("/machinekit/spindle/override",
               endpoint='set_machinekit_spindle_override',
               methods=["POST"])
@auth
@errors
@validate(SpindleOverrideSchema)
def set_machinekit_spindle_override():
    """Control spindleoverride"""
    data = request.sanitizedRequest
    return settings.controller.spindleoverride(data["command"])
