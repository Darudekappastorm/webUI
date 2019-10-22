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
    if not "spindle_speed" in request.json:
        raise ValueError(errorMessages['2'])

    data = request.json
    command = escape(data["spindle_speed"])
    return settings.controller.spindle_speed(command)


@spindle.route("/machinekit/spindle/brake", endpoint='set_machinekit_spindle_brake', methods=["POST"])
@auth
@errors
def set_machinekit_spindle_brake():
    if not "spindle_brake" in request.json:
        raise ValueError(errorMessages['2'])

    data = request.json
    command = escape(data["spindle_brake"])
    return settings.controller.spindle_brake(command)


@spindle.route("/machinekit/spindle/direction", endpoint='get_machinekit_spindle_direction', methods=["POST"])
@auth
@errors
def set_machinekit_spindle_direction():
    if not "spindle_direction" in request.json:
        raise ValueError(errorMessages['2'])

    data = request.json
    command = escape(data['spindle_direction'])
    return settings.controller.spindle_direction(command)


@spindle.route("/machinekit/spindle/enabled", endpoint='set_spindle_enabled', methods=["POST"])
@auth
@errors
def set_spindle_enabled():
    if not "spindle_enabled" in request.json:
        raise ValueError(errorMessages['2'])

    data = request.json
    command = escape(data["spindle_enabled"])
    return settings.controller.spindle_enabled(command)


@spindle.route("/machinekit/spindle/override", endpoint='set_machinekit_spindle_override', methods=["POST"])
@auth
@errors
def set_machinekit_spindle_override():
    if not "spindle_override" in request.json:
        raise ValueError(errorMessages['2'])

    data = request.json
    command = escape(data["spindle_override"])
    return settings.controller.spindleoverride(float(command))