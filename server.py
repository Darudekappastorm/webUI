import sys
import json
import settings
import configparser
from flask import render_template
from marshmallow import Schema
from config.startup import app

app = app()
config = configparser.ConfigParser()
config.read("default.ini")

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
        settings.logger.critical(e)
        sys.exit({"errors": [e]})

if __name__ == "__main__":
    app.run('0.0.0.0',
            debug=(True if config['server'].get('debug', False) else False),
            port=config['server']['port'])
