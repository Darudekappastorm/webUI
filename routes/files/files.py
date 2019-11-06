import os
import json
import settings
import configparser
from decorators.auth import auth
from decorators.errors import errors
from decorators.validate import validate
from flask import Blueprint, request, escape
from schemas.schemas import UpdateQueueSchema, OpenFileSchema, HalcmdSchema
from werkzeug.utils import secure_filename
import csv

config = configparser.ConfigParser()
config.read("default.ini")
files = Blueprint('files', __name__)
with open("./jsonFiles/errorMessages.json") as f:
    errorMessages = json.load(f)

files_on_server = []


@files.route("/server/files", endpoint='return_files', methods=["GET"])
@auth
@errors
def return_files():
    """ Return all machinekit files from the server """
    try:
        global files_on_server
        files_on_server = []
        with open("./routes/files/files.csv") as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                files_on_server.append([row['name'], row['path']])

        return {"result": files_on_server, "file_queue": settings.file_queue}
    except Exception as e:
        return {"errors": errorMessages['internal-server-error']}, errorMessages['internal-server-error']['status']


@files.route("/server/update_file_queue", endpoint='update_file_queue', methods=["POST"])
@auth
@errors
@validate(UpdateQueueSchema)
def update_file_queue():
    """ Update the file queue that is fed into machinekit """
    data = request.sanitizedRequest
    new_queue = data["new_queue"]

    for item in new_queue:
        if not os.path.isfile(config['storage']['upload_folder'] + "/" + escape(item)):
            raise NameError(
                errorMessages['file-not-found']['message'], errorMessages['file-not-found']['status'], errorMessages['file-not-found']['type'])

    settings.file_queue = new_queue
    return {"success": settings.file_queue}


@files.route("/machinekit/open_file", endpoint='open_file', methods=["POST"])
@auth
@errors
@validate(OpenFileSchema)
def open_file():
    """ Open a file """
    data = request.sanitizedRequest
    return settings.controller.open_file(config['storage']['upload_folder'], escape(data["name"]))


@files.route("/server/file_upload", endpoint='upload', methods=["POST"])
@auth
def upload():
    """ Upload a nc, ngc, gcode file to the server """
    try:
        if "file" not in request.files:
            raise ValueError(
                errorMessages['file-not-found']['message'], errorMessages['file-not-found']['status'], errorMessages['file-not-found']['type'])

        file = request.files["file"]
        filename = secure_filename(file.filename)
        file_exists = False
        last_id = 0

        print(files_on_server)
        for item in files_on_server:
            if item[0] == filename:
                file_exists = True
                break

        if file_exists:
            raise ValueError(
                errorMessages['file-exists']['message'], errorMessages['file-exists']['status'], errorMessages['file-exists']['type'])

        with open('./routes/files/files.csv', "a") as csvfile:
            fieldnames = ['name', 'path']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writerow(
                {'name': filename, 'path': config['storage']['upload_folder']})

        file.save(os.path.join(config['storage']
                               ['upload_folder'] + "/" + filename))
        return {"success": "file added"}
    except ValueError as e:
        message, status, errType = e
        return {"errors": {"message": message, "status": status, "type": errType}}, status
    except Exception as e:
        print(e)
        return {"errors": errorMessages['internal-server-error']}, errorMessages['internal-server-error']['status']


@files.route("/machinekit/halcmd", endpoint='halcmd', methods=["POST"])
@auth
@errors
@validate(HalcmdSchema)
def halcmd():
    """ Accepts whitelisted halcmds """
    data = request.sanitizedRequest
    command = data["halcmd"]
    os.system('halcmd ' + command + " > output.txt")
    f = open("output.txt", "r")
    return {"success": f.read()}
