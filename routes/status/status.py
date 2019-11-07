import os
import time
import json
import settings
from decorators.auth import auth
from decorators.errors import errors
from decorators.validate import validate
from flask import Blueprint, request, escape
import configparser
from schemas.schemas import StatusSchema, FeedOverrideSchema, MaxvelOverrideSchema

CONFIG = configparser.ConfigParser()
CONFIG.read("default.ini")
status = Blueprint('status', __name__)

with open("./jsonFiles/errorMessages.json") as f:
    MESSAGE = json.load(f)


@status.route("/machinekit/status",
              endpoint='get_machine_status',
              methods=["GET"])
@auth
@errors
def get_machinekit_status():
    """Returns machinekit vitals"""
    return settings.controller.get_all_vitals()


@status.route("/machinekit/position",
              endpoint='get_machinekit_position',
              methods=["GET"])
@auth
@errors
def get_machinekit_position():
    """Returns position of axes"""
    return settings.controller.axes_position()


@status.route("/machinekit/status",
              endpoint='set_machinekit_status',
              methods=["POST"])
@auth
@errors
@validate(StatusSchema)
def set_machinekit_status():
    """Power/Estop control"""
    data = request.sanitizedRequest
    command = escape(data['command'])
    return settings.controller.machine_status(command)


@status.route("/machinekit/feed",
              endpoint='set_machinekit_feedrate',
              methods=["POST"])
@auth
@errors
@validate(FeedOverrideSchema)
def set_machinekit_feedrate():
    """Control feedrate"""
    data = request.sanitizedRequest
    return settings.controller.feedoverride(data["command"])


@status.route("/machinekit/maxvel", endpoint='maxvel', methods=["POST"])
@auth
@errors
@validate(MaxvelOverrideSchema)
def maxvel():
    """Control maxvel"""
    data = request.sanitizedRequest
    return settings.controller.maxvel(data["command"])


@status.route("/machinekit/toolchange",
              endpoint='tool_changer',
              methods=["GET"])
@auth
@errors
def tool_changer():
    """Accept toolchange prompt"""
    if CONFIG['server']['mock'] == 'true':
        return {"success": "Command executed"}

    # Dirty fix to bypass toolchange prompt
    os.system("halcmd setp hal_manualtoolchange.change_button true")
    time.sleep(3)
    os.system("halcmd setp hal_manualtoolchange.change_button false")
    return {"success": "Command executed"}
