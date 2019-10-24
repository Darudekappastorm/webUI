import json
import settings
from decorators.auth import auth
from decorators.errors import errors
from flask import Blueprint, request, escape

program = Blueprint('program', __name__)

with open("./jsonFiles/errorMessages.json") as f:
    errorMessages = json.load(f)


@program.route("/machinekit/program", endpoint='control_program', methods=["POST"])
@auth
@errors
def control_program():
    if not "command" in request.json:
        raise ValueError(errorMessages['2'])

    data = request.json
    command = escape(data['command'])
    return settings.controller.run_program(command)
