import os
import csv
import json
import settings
import configparser
from decorators.auth import auth
from decorators.errors import errors
from decorators.validate import validate
from flask import Blueprint, request, escape
from schemas.schemas import UpdateQueueSchema, OpenFileSchema, HalcmdSchema
from werkzeug.utils import secure_filename

CONFIG = configparser.ConfigParser()
CONFIG.read("default.ini")
files = Blueprint('files', __name__)
with open("./jsonFiles/errorMessages.json") as f:
    MESSAGE = json.load(f)

FILES_ON_SERVER = []


@files.route("/server/files", endpoint='return_files', methods=["GET"])
@auth
@errors
def return_files():
    """ Return all machinekit files from the server """
    try:
        global FILES_ON_SERVER
        FILES_ON_SERVER = []
        with open("./routes/files/files.csv") as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                FILES_ON_SERVER.append([row['name'], row['path']])

        return {"result": FILES_ON_SERVER, "file_queue": settings.file_queue}
    except Exception:
        return {
            "errors": MESSAGE['internal-server-error']
        }, MESSAGE['internal-server-error']['status']


@files.route("/server/update_file_queue",
             endpoint='update_file_queue',
             methods=["POST"])
@auth
@errors
@validate(UpdateQueueSchema)
def update_file_queue():
    """ Update the file queue that is fed into machinekit """
    data = request.sanitizedRequest
    new_queue = data["new_queue"]

    for item in new_queue:
        if not os.path.isfile(CONFIG['storage']['upload_folder'] + "/" +
                              escape(item)):
            raise NameError(MESSAGE['file-not-found']['message'],
                            MESSAGE['file-not-found']['status'],
                            MESSAGE['file-not-found']['type'])

    settings.file_queue = new_queue
    return {"success": settings.file_queue}


@files.route("/machinekit/open_file", endpoint='open_file', methods=["POST"])
@auth
@errors
@validate(OpenFileSchema)
def open_file():
    """ Open a file """
    data = request.sanitizedRequest
    return settings.controller.open_file(CONFIG['storage']['upload_folder'],
                                         escape(data["name"]))


@files.route("/server/file_upload", endpoint='upload', methods=["POST"])
@auth
def upload():
    """ Upload a nc, ngc, gcode file to the server """
    try:
        if "file" not in request.files:
            raise ValueError(MESSAGE['file-not-found']['message'],
                             MESSAGE['file-not-found']['status'],
                             MESSAGE['file-not-found']['type'])

        file = request.files["file"]
        filename = secure_filename(file.filename)
        file_exists = False

        for item in FILES_ON_SERVER:
            if item[0] == filename:
                file_exists = True
                break

        if file_exists:
            raise ValueError(MESSAGE['file-exists']['message'],
                             MESSAGE['file-exists']['status'],
                             MESSAGE['file-exists']['type'])

        with open('./routes/files/files.csv', "a") as csvfile:
            fieldnames = ['name', 'path']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writerow({
                'name': filename,
                'path': CONFIG['storage']['upload_folder']
            })

        file.save(
            os.path.join(CONFIG['storage']['upload_folder'] + "/" + filename))

        return {"success": "file added"}, 201
    except ValueError as err:
        message, status, err_type = err
        return {
            "errors": {
                "message": message,
                "status": status,
                "type": err_type
            }
        }, status
    except Exception:
        return {
            "errors": MESSAGE['internal-server-error']
        }, MESSAGE['internal-server-error']['status']


@files.route("/machinekit/halcmd", endpoint='halcmd', methods=["POST"])
@auth
@errors
@validate(HalcmdSchema)
def halcmd():
    """ Accepts whitelisted halcmds """
    data = request.sanitizedRequest
    command = data["halcmd"]
    os.system('halcmd ' + command + " > output.txt")
    output = open("output.txt", "r")
    return {"success": output.read()}
