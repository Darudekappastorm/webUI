import os
import sys
import json
import logging
import settings
import configparser
from flask_cors import CORS
from flask_mysqldb import MySQL
from decorators.auth import auth
from werkzeug.utils import secure_filename
from flask import Flask, request, redirect, abort, escape, render_template, jsonify
from decorators.errors import errors

from routes.axes.axes import axes
from routes.status.status import status
from routes.program.program import program
from routes.spindle.spindle import spindle

settings.init()

config = configparser.ConfigParser()
config.read("default.ini")
app = Flask(__name__)
CORS(app)
app.config['MYSQL_HOST'] = config['mysql']['host']
app.config['MYSQL_USER'] = config['mysql']['user']
app.config['MYSQL_PASSWORD'] = config['mysql']['password']
app.config['MYSQL_DB'] = config['mysql']['database']
mysql = MySQL(app)

app.register_blueprint(axes)
app.register_blueprint(status)
app.register_blueprint(spindle)
app.register_blueprint(program)

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
file_handler = logging.FileHandler('logfile.log')
formatter = logging.Formatter(
    '%(asctime)s : %(levelname)s : %(name)s : %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

with open("./jsonFiles/errorMessages.json") as f:
    errorMessages = json.load(f)
with open("./jsonFiles/halCommands.json") as f:
    halCommands = json.load(f)

if config['server']['mockup'] == 'true':
    print("Mockup")
    from mockup.machinekitController import MachinekitController
    settings.controller = MachinekitController()
    settings.machinekit_running = True
else:
    import linuxcnc
    from classes.machinekitController import MachinekitController
    try:
        settings.controller = MachinekitController(
            config["server"]["axis_config"])
        settings.machinekit_running = True
    except (linuxcnc.error) as e:
        print("Machinekit is down please start machinekit and then restart the server")
    except Exception as e:
        logger.critical(e)
        sys.exit({"errors": [e]})


@app.route("/", methods=['GET'])
def home():
    """Landing page."""
    feed_override = 120
    spindle_override = 100
    max_velocity = 3200
    if config["server"]["mockup"] == 'false':
        feed_override = (float(settings.controller.max_feed_override) * 100)
        spindle_override = (
            float(settings.controller.max_spindle_override) * 100)
        max_velocity = settings.controller.max_velocity

    return render_template('/index.html', max_feed_override=feed_override, max_spindle_override=spindle_override, maxvel=max_velocity)


@app.route("/server/files", endpoint='return_files', methods=["GET"])
@auth
@errors
def return_files():
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
                    SELECT * FROM files
                    """)
        result = cur.fetchall()
        return {"result": result, "file_queue": settings.file_queue}
    except Exception as e:
        logger.critical(e)
        return {"errors": errorMessages['9']}, 500


@app.route("/server/update_file_queue", endpoint='update_file_queue', methods=["POST"])
@auth
@errors
def update_file_queue():
    if not "new_queue" in request.json:
        raise ValueError(errorMessages['2'])
    if not type(settings.file_queue) == list:
        raise ValueError(errorMessages['5'])

    data = request.json
    new_queue = data["new_queue"]

    for item in new_queue:
        if not os.path.isfile(settings.UPLOAD_FOLDER + "/" + escape(item)):
            raise NameError(errorMessages['6'])

    settings.file_queue = new_queue
    return {"success": "Queue updated"}


@app.route("/machinekit/halcmd", endpoint='halcmd', methods=["POST"])
@auth
@errors
def halcmd():
    if not "halcmd" in request.json:
        raise ValueError(errorMessages['2'])
    command = request.json["halcmd"]
    i_command = command.split(' ', 1)[0]

    isInList = False
    for item in halCommands:
        if item['command'] == i_command:
            isInList = True
            break
    if not isInList:
        raise ValueError(errorMessages['8'])

    os.system('halcmd ' + command + " > output.txt")
    f = open("output.txt", "r")
    return {"success": f.read()}


@app.route("/machinekit/open_file", endpoint='open_file', methods=["POST"])
@auth
@errors
def open_file():
    if not "name" in request.json:
        raise ValueError(errorMessages['2'])

    data = request.json
    name = escape(data["name"])
    return controller.open_file(os.path.join(settings.UPLOAD_FOLDER + "/" + name))


@app.route("/server/file_upload", endpoint='upload', methods=["POST"])
@auth
def upload():
    try:
        if "file" not in request.files:
            raise ValueError(errorMessages['5'])

        file = request.files["file"]
        filename = secure_filename(file.filename)

        cur = mysql.connection.cursor()
        cur.execute(
            """
            SELECT * FROM files
            WHERE file_name = '%s' """ % filename)

        result = cur.fetchall()

        if len(result) > 0:
            raise ValueError(errorMessages['7'])

        cur.execute("""
            INSERT INTO files (file_name, file_location)
            VALUES (%s, %s)
            """, (filename, settings.UPLOAD_FOLDER)
        )
        mysql.connection.commit()
        file.save(os.path.join(settings.UPLOAD_FOLDER + "/" + filename))
        return {"success": "file added"}
    except ValueError as e:
        print(e[0]['message'])
        return {"errors": {"message": e[0]['message'], "type": e[0]["type"], "status": e[0]["status"]}}, e[0]["status"]
    except Exception as e:
        logger.critical(e)
        return {"errors": errorMessages['9']}, 500


if __name__ == "__main__":
    app.run('0.0.0.0', debug=True,
            port=5000)
