import json
import settings
from decorators.auth import auth
from decorators.errors import errors
from flask import Blueprint, request, escape

axes = Blueprint('axes', __name__)
with open("./jsonFiles/errorMessages.json") as f:
    errorMessages = json.load(f)


@axes.route("/machinekit/axes/home", endpoint='set_home_axes', methods=["POST"])
@auth
@errors
def set_home_axes():
    if not "command" in request.json:
        raise ValueError(errorMessages['2'])

    data = request.json
    command = escape(data['command'])
    return settings.controller.home_all_axes(command)


@axes.route("/machinekit/position/mdi", endpoint='send_command', methods=["POST"])
@auth
@errors
def send_command():
    if not "command" in request.json:
        raise ValueError(errorMessages['2'])

    if len(request.json["command"]) == 0:
        raise ValueError(errorMessages['3'])

    data = request.json
    command = escape(data["command"])
    return settings.controller.mdi_command(command)


@axes.route("/machinekit/position/manual", endpoint='manual', methods=["POST"])
@auth
@errors
def manual():
    if not "axes" in request.json or not "speed" in request.json or not "increment" in request.json:
        raise ValueError(errorMessages['2'])

    data = request.json
    axes = escape(data['axes'])
    speed = escape(data['speed'])
    increment = escape(data['increment'])
    return settings.controller.manual_control(axes, speed, increment)
