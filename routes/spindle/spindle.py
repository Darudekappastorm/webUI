import json
import settings
from decorators.auth import auth
from decorators.errors import errors
from flask import Blueprint, request, escape

spindle = Blueprint('spindle', __name__)

with open("./jsonFiles/errorMessages.json") as f:
    errorMessages = json.load(f)


@spindle.route("/machinekit/spindle/speed", endpoint='set_machinekit_spindle_speed', methods=["POST"])
@auth
@errors
def set_machinekit_spindle_speed():
    if not "command" in request.json:
        raise ValueError(errorMessages['2'])

    data = request.json
    command = escape(data["command"])
    return settings.controller.spindle_speed(command)


@spindle.route("/machinekit/spindle/brake", endpoint='set_machinekit_spindle_brake', methods=["POST"])
@auth
@errors
def set_machinekit_spindle_brake():
    if not "command" in request.json:
        raise ValueError(errorMessages['2'])

    data = request.json
    command = escape(data["command"])
    return settings.controller.spindle_brake(command)


@spindle.route("/machinekit/spindle/direction", endpoint='get_machinekit_spindle_direction', methods=["POST"])
@auth
@errors
def set_machinekit_spindle_direction():
    if not "command" in request.json:
        raise ValueError(errorMessages['2'])

    data = request.json
    command = escape(data['command'])
    return settings.controller.spindle_direction(command)


@spindle.route("/machinekit/spindle/enabled", endpoint='set_spindle_enabled', methods=["POST"])
@auth
@errors
def set_spindle_enabled():
    if not "command" in request.json:
        raise ValueError(errorMessages['2'])

    data = request.json
    command = escape(data["command"])
    return settings.controller.spindle_enabled(command)


@spindle.route("/machinekit/spindle/override", endpoint='set_machinekit_spindle_override', methods=["POST"])
@auth
@errors
def set_machinekit_spindle_override():
    if not "command" in request.json:
        raise ValueError(errorMessages['2'])

    data = request.json
    command = escape(data["command"])
    return settings.controller.spindleoverride(float(command))
