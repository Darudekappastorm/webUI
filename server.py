import os
import time
import random
import logging
import eventlet
import linuxcnc
from flask_mysqldb import MySQL
from flask import Flask, jsonify
from flask_socketio import SocketIO, send, emit
from werkzeug.utils import secure_filename
from classes.machinekitController import MachinekitController

# halcmd setp hal_manualtoolchange.change_button true

host = "192.168.1.116"
eventlet.monkey_patch()
app = Flask(__name__)

app.config["SECRET_KEY"] = "very-secret"
api_token = "test_secret"

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'machinekit'
app.config['MYSQL_DB'] = 'machinekit'

mysql = MySQL(app)

UPLOAD_FOLDER = '/home/machinekit/devel/webUI/files'
ALLOWED_EXTENSIONS = set(['nc'])

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
file_handler = logging.FileHandler('logfile.log')
formatter = logging.Formatter(
    '%(asctime)s : %(levelname)s : %(name)s : %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

file_queue = []

socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins="*")

machinekit_down = False
try:
    controller = MachinekitController()
except Exception as e:
    machinekit_down = True
    print("Machinekit is not running")


@socketio.on("connect")
def client_connect():
    print("Client connected")
    emit("connected", {"success": "test"})


@socketio.on('set-status')
def toggle_estop(command):
    result = controller.machine_status(command)
    if result is not None:
        emit("errors", result)

    emit("vitals", controller.get_all_vitals())


@socketio.on('set-home')
def toggle_estop(command):
    if command == "home":
        result = controller.home_all_axes()
    else:
        result = controller.unhome_all_axes()

    if result is not None:
        emit("errors", result)

    emit("vitals", controller.get_all_vitals())


@socketio.on("vitals")
def vitals():
    if machinekit_down:
        emit("vitals", {"errors": "machinekit is not running"})
    else:
        emit("vitals", controller.get_all_vitals())


@socketio.on("manual-control")
def manual_control(command):
    result = controller.manual_control(
        command['axes'], command['speed'], command['increment'])
    if result is not None:
        emit("errors", result)
    emit("vitals", controller.get_all_vitals())


@socketio.on("program-control")
def program_control(command):
    result = controller.run_program(command)
    if result is not None:
        emit("errors", result)
    emit("vitals", controller.get_all_vitals())


@socketio.on("spindle-control")
def spindle_control(command):
    if "spindle_brake" in command:
        result = controller.spindle_brake(command["spindle_brake"])
    elif "spindle_direction" in command:
        result = controller.spindle_direction(command["spindle_direction"])
    elif "spindle_override" in command:
        result = controller.spindleoverride(command["spindle_override"])

    if result is not None:
        emit("errors", result)
    emit("vitals", controller.get_all_vitals())


@socketio.on("feed-override")
def feed_override(command):
    result = controller.feedoverride(command)
    if result is not None:
        emit("errors", result)
    emit("vitals", controller.get_all_vitals())


@socketio.on("maxvel")
def maxvel(command):
    result = controller.maxvel(command)
    if result is not None:
        emit("errors", result)
    emit("vitals", controller.get_all_vitals())


@socketio.on("send-command")
def send_command(command):
    result = controller.mdi_command(command)
    if result is not None:
        emit("errors", result)
    emit("vitals", controller.get_all_vitals())


@socketio.on("get-files")
def get_files():
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
        SELECT * FROM files
        """)
        result = cur.fetchall()
        files_on_server = []
        for res in result:
            my_file = res[2] + "/" + res[1]
            if(os.path.isfile(my_file)):
                files_on_server.append(res)
            else:
                cur.execute("""
                            DELETE FROM files WHERE file_id = %s
                """ % res[0])
                cur.connection.commit()

        emit("get-files", {"result": tuple(files_on_server),
                           "file_queue": file_queue})
        vitals()
    except Exception as e:
        emit("errors", str(e))


@socketio.on("update-file-queue")
def update_file_queue(new_queue):
    global file_queue
    file_queue = new_queue
    get_files()


@socketio.on("tool-changed")
def tool_changed():
    os.system("halcmd setp hal_manualtoolchange.change_button true")
    time.sleep(2)
    os.system("halcmd setp hal_manualtoolchange.change_button false")
    emit("vitals", controller.get_all_vitals())


@socketio.on("open-file")
def open_file():
    controller.open_file("/home/machinekit/devel/webUI/files/" + file_queue[0])
    emit("vitals", controller.get_all_vitals())


@socketio.on("file-upload")
def upload(data):
    try:
        f = open(os.path.join("./files/" + data['name']), "w")
        f.write(data['file'].encode("utf8"))
        f.close()

        filename = secure_filename(data['name'])
        cur = mysql.connection.cursor()
        cur.execute(
            """
            SELECT * FROM files
            WHERE file_name = '%s' """ % filename)

        result = cur.fetchall()

        if len(result) > 0:
            return emit("errors", {"errors": "File with given name already on server"})

        cur.execute("""
            INSERT INTO files (file_name, file_location)
            VALUES (%s, %s)
            """, (filename, "/home/machinekit/devel/webUI/files")
        )
        mysql.connection.commit()
        vitals()
    except Exception as e:
        print(e)
        emit("errors", str(e))


if __name__ == "__main__":
    app.debug = True
    socketio.run(app, host=host)
