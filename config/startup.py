import settings
import configparser
import sys
from flask import Flask, render_template
from flask_cors import CORS
from flask_mysqldb import MySQL

from routes.axes.axes import axes
from routes.status.status import status
from routes.program.program import program
from routes.spindle.spindle import spindle
from routes.files.files import files

config = configparser.ConfigParser()
config.read("default.ini")


def app():
    app = Flask(__name__)
    CORS(app)
    app.config['MYSQL_HOST'] = config['mysql']['host']
    app.config['MYSQL_USER'] = config['mysql']['user']
    app.config['MYSQL_PASSWORD'] = config['mysql']['password']
    app.config['MYSQL_DB'] = config['mysql']['database']
    app.mysql = MySQL(app)

    app.register_blueprint(axes)
    app.register_blueprint(status)
    app.register_blueprint(spindle)
    app.register_blueprint(program)
    app.register_blueprint(files)
    return app
