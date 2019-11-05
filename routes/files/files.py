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

config = configparser.ConfigParser()
config.read("default.ini")
files = Blueprint('files', __name__)

with open("./jsonFiles/errorMessages.json") as f:
    errorMessages = json.load(f)


@files.route("/server/files", endpoint='return_files', methods=["GET"])
@auth
@errors
def return_files():
    """ Return all machinekit files from the server """
    try:
        cur = settings.mysql.connection.cursor()
        cur.execute("""
                    SELECT * FROM files
                    """)
        result = cur.fetchall()
        return {"result": result, "file_queue": settings.file_queue}
    except Exception as e:
        print(e)
        return {"errors": errorMessages['9']}, 500


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
                errorMessages['6']['message'], errorMessages['6']['status'], errorMessages['6']['type'])

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
                errorMessages['5']['message'], errorMessages['5']['status'], errorMessages['5']['type'])

        file = request.files["file"]
        filename = secure_filename(file.filename)

        cur = settings.mysql.connection.cursor()
        cur.execute(
            """
            SELECT * FROM files
            WHERE file_name = '%s' """ % filename)

        result = cur.fetchall()

        if len(result) > 0:
            raise ValueError(
                errorMessages['7']['message'], errorMessages['7']['status'], errorMessages['7']['type'])

        cur.execute("""
            INSERT INTO files (file_name, file_location)
            VALUES (%s, %s)
            """, (filename, config['storage']['upload_folder'])
        )
        settings.mysql.connection.commit()
        file.save(os.path.join(config['storage']
                               ['upload_folder'] + "/" + filename))
        return {"success": "file added"}
    except ValueError as e:
        message, status, errType = e
        return {"errors": {"message": message, "status": status, "type": errType}}, status
    except Exception as e:
        return {"errors": errorMessages['9']}, 500


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
