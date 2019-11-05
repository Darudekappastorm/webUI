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
settings.mysql = app.mysql
config = configparser.ConfigParser()
config.read("default.ini")

if config['server']['mockup'] == 'true':
    from mockup.machinekitController import MachinekitController

    print("Starting mock server")
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
        print(
            "Machinekit is down please start machinekit and then restart the server")
    except Exception as e:
        sys.exit({"errors": [e]})


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
        max_velocity = (float(settings.controller.velocity) * 60)
    return render_template('/index.html', max_feed_override=feed_override, max_spindle_override=spindle_override, maxvel=max_velocity)


if __name__ == "__main__":
    app.run('0.0.0.0',
            debug=((config['server'].get('debug')
                    == 'true') if True else False),
            port=config['server']['port'])
