from flask import Flask
from flask_cors import CORS

from routes.axes.axes import axes
from routes.status.status import status
from routes.program.program import program
from routes.spindle.spindle import spindle
from routes.files.files import files


def app():
    app = Flask(__name__)
    CORS(app)

    app.register_blueprint(axes)
    app.register_blueprint(status)
    app.register_blueprint(spindle)
    app.register_blueprint(program)
    app.register_blueprint(files)
    return app
