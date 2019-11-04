import json
import settings
from decorators.auth import auth
from decorators.errors import errors
from decorators.validate import validate
from flask import Blueprint, request, escape
from marshmallow import Schema
from schemas.schemas import HomeSchema, CommandSchema, ManualControlSchema

axes = Blueprint('axes', __name__)
with open("./jsonFiles/errorMessages.json") as f:
    errorMessages = json.load(f)


@axes.route("/machinekit/axes/home", endpoint='set_home_axes', methods=["POST"])
@auth
@errors
@validate(HomeSchema)
def set_home_axes():
    data = request.sanitizedRequest
    command = escape(data['command'])
    return settings.controller.home_all_axes(command)


@axes.route("/machinekit/position/mdi", endpoint='send_command', methods=["POST"])
@auth
@errors
@validate(CommandSchema)
def send_command():
    data = request.sanitizedRequest
    command = escape(data["command"])
    return settings.controller.mdi_command(command)


@axes.route("/machinekit/position/manual", endpoint='manual', methods=["POST"])
@auth
@errors
@validate(ManualControlSchema)
def manual():
    data = request.sanitizedRequest
    return settings.controller.manual_control(data['axes'], data['speed'], data['increment'])
