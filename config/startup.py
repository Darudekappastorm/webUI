import settings
import logging
import configparser
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

    app.logger = logging.getLogger(__name__)
    app.logger.setLevel(logging.WARNING)
    file_handler = logging.FileHandler('logfile.log')
    formatter = logging.Formatter(
        '%(asctime)s : %(levelname)s : %(name)s : %(message)s')
    file_handler.setFormatter(formatter)

    settings.init()
    settings.mysql = app.mysql
    settings.logger = app.logger
    app.logger.addHandler(file_handler)

    @app.route("/", methods=['GET'])
    def home():
        """Landing page."""
        feed_override = 120
        spindle_override = 100
        max_velocity = 3200
        if config["server"]["mockup"] == 'false':
            feed_override = (
                float(settings.controller.max_feed_override) * 100)
            spindle_override = (
                float(settings.controller.max_spindle_override) * 100)
            max_velocity = settings.controller.max_velocity
        return render_template('/index.html', max_feed_override=feed_override, max_spindle_override=spindle_override, maxvel=max_velocity)

    return app
