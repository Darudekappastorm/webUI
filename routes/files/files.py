import json
import settings
from decorators.auth import auth
from decorators.errors import errors
from flask import Blueprint, request, escape

files = Blueprint('files', __name__)

with open("./jsonFiles/errorMessages.json") as f:
    errorMessages = json.load(f)
