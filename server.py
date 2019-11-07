import sys
import json
import settings
import configparser
from flask import render_template
from marshmallow import Schema
from config.startup import app
import math

app = app()
settings.init()
CONFIG = configparser.ConfigParser()
CONFIG.read("default.ini")

if CONFIG['server']['mock'] == 'true':
    from mock.machinekitController import MachinekitController
    settings.controller = MachinekitController()
    settings.machinekit_running = True
else:
    import linuxcnc
    from classes.machinekitController import MachinekitController

    try:
        settings.controller = MachinekitController(
            CONFIG["server"]["axis_config"])
        settings.machinekit_running = True
    except (linuxcnc.error) as err:
        print(
            "Machinekit is down please start machinekit and then restart the server"
        )
    except Exception as err:
        sys.exit({"errors": [err]})


@app.route("/", methods=['GET'])
def home():
    """Landing page."""
    feed_override = 120
    spindle_override = 100
    max_velocity = 3200
    if not CONFIG["server"]["mock"] and settings.machinekit_running:
        feed_override = (float(settings.controller.max_feed_override) * 100)
        spindle_override = (float(settings.controller.max_spindle_override) *
                            100)
        max_velocity = (float(settings.controller.max_velocity) * 60)
    return render_template('/index.html',
                           max_feed_override=feed_override,
                           max_spindle_override=spindle_override,
                           maxvel=max_velocity,
                           host=CONFIG['server']['host'],
                           port=CONFIG['server']['port'])


if __name__ == "__main__":
    app.run(
        CONFIG['server']['host'],
        debug=((CONFIG['server'].get('debug') == 'true') if True else False),
        port=CONFIG['server']['port'])
