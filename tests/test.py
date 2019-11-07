import sys
import json
import time
import configparser
import unittest
import settings
from config.startup import app
from flask import Flask, jsonify
from flask_testing import TestCase


with open("./jsonFiles/errorMessages.json") as f:
    errorMessages = json.load(f)

settings.init()
config = configparser.ConfigParser()
config.read("default.ini")

if config['server']['mock'] == 'true':
    from mock.machinekitController import MachinekitController

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


def make_orderer():
    order = {}

    def ordered(f):
        order[f.__name__] = len(order)
        return f

    def compare(a, b):
        return [1, -1][order[a] < order[b]]

    return ordered, compare


ordered, compare = make_orderer()
unittest.defaultTestLoader.sortTestMethodsUsing = compare

global homed
homed = False


class Startup(TestCase):

    def create_app(self):
        application = app()
        return application

    @ordered
    def test_fail_authorization(self):
        res = self.client.get("/machinekit/status")
        self.assertEqual(res.json, {"errors": errorMessages['authorization']})
        self.assert401(res)

    @ordered
    def test_pass_authorization(self):
        res = self.client.get("/machinekit/status",
                              headers={"API_KEY": config['security'].get("token")})
        axes = res.json['position']
        global homed
        for axe in axes:
            if axes[axe]['homed'] == True:
                homed = True
            else:
                homed = False
                break
        self.assert200(res)

    @ordered
    def test_fail_invalid_json(self):
        res = self.client.post(
            '/machinekit/status', headers={"API_KEY": config['security'].get("token")}, data={"command": "power"})
        self.assertEqual(
            res.json, {"errors": errorMessages['content-not-allowed']})

    @ordered
    def test_fail_invalid_key(self):
        command = {"commandq": "power"}
        res = self.client.post(
            '/machinekit/status', headers={"API_KEY": config['security'].get("token"), "Content-Type": "application/json"}, data=json.dumps(command))
        self.assertEqual(res.json, {u'errors': {u'keys': {u'command': [
                         u'Missing data for required field.']}, u'status': 400, u'type': u'ValidationError'}})
        self.assert400(res)

    @ordered
    def test_fail_power_on_while_estop(self):
        command = {"command": "power"}
        res = self.client.post(
            '/machinekit/status', headers={"API_KEY": config['security'].get("token"), "Content-Type": "application/json"}, data=json.dumps(command))
        self.assertEqual(res.json, {u'errors': {
            u'status': 502, u'message': u"Can't turn on machine while it is in E_STOP modus", u'type': u'RuntimeError'}}, "Shouldnt be able to turn on machine while in estop")

    @ordered
    def test_pass_disable_estop(self):
        command = {"command": "estop"}
        res = self.client.post(
            '/machinekit/status', headers={"API_KEY": config['security'].get("token"), "Content-Type": "application/json"}, data=json.dumps(command))
        self.assert200(res)

    @ordered
    def test_pass_enable_power(self):
        command = {"command": "power"}
        res = self.client.post(
            '/machinekit/status', headers={"API_KEY": config['security'].get("token"), "Content-Type": "application/json"}, data=json.dumps(command))
        self.assert200(res)

    @ordered
    def test_pass_home_axes(self):
        if homed:
            self.skipTest("Already homed")

        command = {"command": "home"}
        res = self.client.post(
            '/machinekit/axes/home', headers={"API_KEY": config['security'].get("token"), "Content-Type": "application/json"}, data=json.dumps(command))
        time.sleep(10)
        self.assert200(
            res, "Should home machine axes. Probably returns error after first time homing! bug in machinekit")

    @ordered
    def test_pass_mdi_command(self):
        command = {"command": "Y1 X1 Z1"}
        res = self.client.post(
            '/machinekit/position/mdi', headers={"API_KEY": config['security'].get("token"), "Content-Type": "application/json"}, data=json.dumps(command))
        time.sleep(2)
        self.assert200(
            res, "Should move axes to given position. Will not work if axes are not homed")

    @ordered
    def test_pass_manual_control(self):
        command = {
            "axes": 0,
            "speed": 10,
            "increment": 1
        }
        res = self.client.post(
            '/machinekit/position/manual', headers={"API_KEY": config['security'].get("token"), "Content-Type": "application/json"}, data=json.dumps(command))
        time.sleep(2)
        self.assert200(
            res, "Should move axes to given position. Will not work if axes are not homed")

    @ordered
    def test_pass_mdi_reset(self):
        command = {"command": "Y0 X0 Z0"}
        res = self.client.post(
            '/machinekit/position/mdi', headers={"API_KEY": config['security'].get("token"), "Content-Type": "application/json"}, data=json.dumps(command))
        self.assert200(
            res, "Should move axes to given position. Will not work if axes are not homed")

    @ordered
    def test_pass_spindle_reverse(self):
        command = {"command": "spindle_reverse"}
        res = self.client.post(
            '/machinekit/spindle/direction', headers={"API_KEY": config['security'].get("token"), "Content-Type": "application/json"}, data=json.dumps(command))
        self.assert200(
            res)
        time.sleep(1)

    @ordered
    def test_pass_spindle_forward(self):
        command = {"command": "spindle_forward"}
        res = self.client.post(
            '/machinekit/spindle/direction', headers={"API_KEY": config['security'].get("token"), "Content-Type": "application/json"}, data=json.dumps(command))
        self.assert200(
            res)

    @ordered
    def test_pass_spindle_increase(self):
        i = 0
        while i < 3:
            command = {"command": "spindle_increase"}
            res = self.client.post(
                '/machinekit/spindle/speed', headers={"API_KEY": config['security'].get("token"), "Content-Type": "application/json"}, data=json.dumps(command))
            self.assert200(res)
            time.sleep(1)
            i += 1

    @ordered
    def test_pass_spindle_decrease(self):
        i = 0
        while i < 3:
            command = {"command": "spindle_decrease"}
            res = self.client.post(
                '/machinekit/spindle/speed', headers={"API_KEY": config['security'].get("token"), "Content-Type": "application/json"}, data=json.dumps(command))
            self.assert200(
                res)
            time.sleep(1)
            i += 1

    @ordered
    def test_pass_spindle_brake(self):
        command = {"command": "brake_engaged"}
        res = self.client.post(
            '/machinekit/spindle/brake', headers={"API_KEY": config['security'].get("token"), "Content-Type": "application/json"}, data=json.dumps(command))
        self.assert200(res)

    @ordered
    def test_pass_spindle_off(self):
        command = {"command": "spindle_off"}
        res = self.client.post(
            '/machinekit/spindle/enabled', headers={"API_KEY": config['security'].get("token"), "Content-Type": "application/json"}, data=json.dumps(command))
        self.assert200(res)

    @ordered
    def test_pass_enable_estop(self):
        command = {"command": "estop"}
        res = self.client.post(
            '/machinekit/status', headers={"API_KEY": config['security'].get("token"), "Content-Type": "application/json"}, data=json.dumps(command))
        self.assert200(res)


if __name__ == '__main__':
    unittest.main()
