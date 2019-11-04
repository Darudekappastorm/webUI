import json
import settings
from decorators.auth import auth
from decorators.errors import errors
from flask import Blueprint, request, escape
from marshmallow import Schema
from schemas.schemas import ProgramSchema
from decorators.validate import validate


program = Blueprint('program', __name__)

with open("./jsonFiles/errorMessages.json") as f:
    errorMessages = json.load(f)


@program.route("/machinekit/program", endpoint='control_program', methods=["POST"])
@auth
@errors
@validate(ProgramSchema)
def control_program():
    data = request.sanitizedRequest
    command = escape(data['command'])
    return settings.controller.run_program(command)
