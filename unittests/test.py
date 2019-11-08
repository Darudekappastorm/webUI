import sys
import json
import time
import configparser
import unittest
import settings
from config.startup import app
from flask_testing import TestCase

with open("./jsonFiles/errorMessages.json") as f:
    MESSAGE = json.load(f)

settings.init()
CONFIG = configparser.ConfigParser()
CONFIG.read("default.ini")

global homed
global mock
global estop

estop = True
homed = False
mock = False

if CONFIG['server']['mock'] == 'true':
    from mock.machinekitController import MachinekitController
    settings.controller = MachinekitController()
    settings.machinekit_running = True
    mock = True
else:
    import linuxcnc
    from classes.machinekitController import MachinekitController

    try:
        settings.controller = MachinekitController(
            CONFIG["server"]["axis_config"])
        settings.machinekit_running = True
    except (linuxcnc.error) as e:
        print(
            "Machinekit is down please start machinekit and then restart the server"
        )
    except Exception as err:
        sys.exit({"errors": [err]})


def make_orderer():
    """Order all test methods. Usualy they are ordered by length which makes testing machinekit impossible"""
    order = {}

    def ordered(func):
        """Order functions"""
        order[func.__name__] = len(order)
        return func
    def compare(func1, func2):
        """Compare 2 functions"""
        return [1, -1][order[func1] < order[func2]]

    return ordered, compare


ordered, compare = make_orderer()
unittest.defaultTestLoader.sortTestMethodsUsing = compare

class Startup(TestCase):
    """Machinekit startup testcases"""
    def create_app(self):
        """Setup the application"""
        application = app()
        return application

    @ordered
    def test_fail_authorization(self):
        """Test should fail authorization because it has no api key"""
        res = self.client.get("/machinekit/status")
        self.assertEqual(res.json, {"errors": MESSAGE['authorization']})
        self.assert401(res)

    @ordered
    def test_pass_authorization(self):
        """Test should pass authorization because it has a valid api key"""
        global homed
        global estop

        res = self.client.get(
            "/machinekit/status",
            headers={"API_KEY": CONFIG['security'].get("token")})

        axes = res.json['position']
        estop = res.json['power']['estop']
        for axe in axes:
            if axes[axe]['homed'] == True:
                homed = True
            else:
                homed = False
                break
        self.assert200(res)

    @ordered
    def test_fail_invalid_json(self):
        """Test should fail because it doesnt specify the content it is sending"""
        res = self.client.post(
            '/machinekit/status',
            headers={"API_KEY": CONFIG['security'].get("token")},
            data={"command": "power"})
        self.assertEqual(res.json, {"errors": MESSAGE['content-not-allowed']})

    @ordered
    def test_fail_invalid_key(self):
        """Test should fail because its key `commandq` is unknown"""
        command = {"commandq": "power"}
        res = self.client.post('/machinekit/status',
                               headers={
                                   "API_KEY": CONFIG['security'].get("token"),
                                   "Content-Type": "application/json"
                               },
                               data=json.dumps(command))
        self.assertEqual(
            res.json, {
                u'errors': {
                    u'keys': {
                        u'command': [u'Missing data for required field.']
                    },
                    u'status': 400,
                    u'type': u'ValidationError'
                }
            })
        self.assert400(res)

    @ordered
    def test_optional_enable_estop(self):
        if estop:
            self.skipTest("estop is already enable")
        command = {"command": "estop"}

        res = self.client.post('/machinekit/status',
                                headers={
                                    "API_KEY":
                                    CONFIG['security'].get("token"),
                                    "Content-Type": "application/json"
                                },
                                data=json.dumps(command))
        self.assert200(res)

    @ordered
    def test_fail_power_on_while_estop(self):
        """
           Test should fail because machine cannot be powered on while in estop.
           This should be skipped in mock
        """
        if mock:
            self.skipTest("Mock doesnt raise this error")
        command = {"command": "power"}
        res = self.client.post('/machinekit/status',
                               headers={
                                   "API_KEY": CONFIG['security'].get("token"),
                                   "Content-Type": "application/json"
                               },
                               data=json.dumps(command))
        self.assertEqual(
            res.json, {
                u'errors': {
                    u'status': 502,
                    u'message':
                    u"Can't turn on machine while it is in E_STOP modus",
                    u'type': u'RuntimeError'
                }
            }, "Shouldnt be able to turn on machine while in estop")


    @ordered
    def test_pass_disable_estop(self):
        """Test should pass and should disable estop modus"""
        command = {"command": "estop"}
        res = self.client.post('/machinekit/status',
                               headers={
                                   "API_KEY": CONFIG['security'].get("token"),
                                   "Content-Type": "application/json"
                               },
                               data=json.dumps(command))
        self.assert200(res)

    @ordered
    def test_pass_enable_power(self):
        """Test should pass and enable power"""
        command = {"command": "power"}
        res = self.client.post('/machinekit/status',
                               headers={
                                   "API_KEY": CONFIG['security'].get("token"),
                                   "Content-Type": "application/json"
                               },
                               data=json.dumps(command))
        self.assert200(res)

    @ordered
    def test_pass_home_axes(self):
        """
          Test should pass and home all axes. Should be skipped if already homed. 
          Bug doesn't allow unhoming and homing in sim
        """
        if homed:
            self.skipTest("Already homed")

        command = {"command": "home"}
        res = self.client.post('/machinekit/axes/home',
                               headers={
                                   "API_KEY": CONFIG['security'].get("token"),
                                   "Content-Type": "application/json"
                               },
                               data=json.dumps(command))
        time.sleep(10)
        self.assert200(
            res,
            "Should home machine axes. Probably returns error after first time homing! bug in machinekit"
        )

    @ordered
    def test_pass_mdi_command(self):
        """Test should pass and send x-y-z axes to position 1"""
        command = {"command": "Y1 X1 Z1"}
        res = self.client.post('/machinekit/position/mdi',
                               headers={
                                   "API_KEY": CONFIG['security'].get("token"),
                                   "Content-Type": "application/json"
                               },
                               data=json.dumps(command))
        time.sleep(2)
        self.assert200(
            res,
            "Should move axes to given position. Will not work if axes are not homed"
        )

    @ordered
    def test_pass_manual_control(self):
        """Test should pass and send x axe to position 2 since it is already at pos 1"""
        command = {"axes": 0, "speed": 10, "increment": 1}
        res = self.client.post('/machinekit/position/manual',
                               headers={
                                   "API_KEY": CONFIG['security'].get("token"),
                                   "Content-Type": "application/json"
                               },
                               data=json.dumps(command))
        time.sleep(2)
        self.assert200(
            res,
            "Should move axes to given position. Will not work if axes are not homed"
        )

    @ordered
    def test_pass_mdi_reset(self):
        """Test should pass and reset machine axes x-y-z to pos 0"""
        command = {"command": "Y0 X0 Z0"}
        res = self.client.post('/machinekit/position/mdi',
                               headers={
                                   "API_KEY": CONFIG['security'].get("token"),
                                   "Content-Type": "application/json"
                               },
                               data=json.dumps(command))
        self.assert200(
            res,
            "Should move axes to given position. Will not work if axes are not homed"
        )

    @ordered
    def test_pass_spindle_reverse(self):
        """Test should pass and start spinning the spindle counter clockwise"""
        command = {"command": "spindle_reverse"}
        res = self.client.post('/machinekit/spindle/direction',
                               headers={
                                   "API_KEY": CONFIG['security'].get("token"),
                                   "Content-Type": "application/json"
                               },
                               data=json.dumps(command))
        self.assert200(res)
        time.sleep(1)

    @ordered
    def test_pass_spindle_forward(self):
        """Test should pass and start spinning the spindle clockwise"""
        command = {"command": "spindle_forward"}
        res = self.client.post('/machinekit/spindle/direction',
                               headers={
                                   "API_KEY": CONFIG['security'].get("token"),
                                   "Content-Type": "application/json"
                               },
                               data=json.dumps(command))
        self.assert200(res)

    @ordered
    def test_pass_spindle_increase(self):
        """Test should pass and speed up the spindle 3 times with intervals of 1 second"""
        i = 0
        while i < 3:
            command = {"command": "spindle_increase"}
            res = self.client.post('/machinekit/spindle/speed',
                                   headers={
                                       "API_KEY":
                                       CONFIG['security'].get("token"),
                                       "Content-Type": "application/json"
                                   },
                                   data=json.dumps(command))
            self.assert200(res)
            time.sleep(1)
            i += 1

    @ordered
    def test_pass_spindle_decrease(self):
        """Test should pass and slow down the spindle 3 times with intervals of 1 second"""
        i = 0
        while i < 3:
            command = {"command": "spindle_decrease"}
            res = self.client.post('/machinekit/spindle/speed',
                                   headers={
                                       "API_KEY":
                                       CONFIG['security'].get("token"),
                                       "Content-Type": "application/json"
                                   },
                                   data=json.dumps(command))
            self.assert200(res)
            time.sleep(1)
            i += 1

    @ordered
    def test_pass_spindle_brake(self):
        """Test should pass and enable the spindle brake"""

        command = {"command": "brake_engaged"}
        res = self.client.post('/machinekit/spindle/brake',
                               headers={
                                   "API_KEY": CONFIG['security'].get("token"),
                                   "Content-Type": "application/json"
                               },
                               data=json.dumps(command))
        self.assert200(res)

    @ordered
    def test_pass_spindle_off(self):
        """Test should pass and turn the spindle off"""
        command = {"command": "spindle_off"}
        res = self.client.post('/machinekit/spindle/enabled',
                               headers={
                                   "API_KEY": CONFIG['security'].get("token"),
                                   "Content-Type": "application/json"
                               },
                               data=json.dumps(command))
        self.assert200(res)

    @ordered
    def test_pass_spindle_override(self):
        """Test should pass and control the spindle slider"""
        i = 0
        while i < 1:
            command = {"command": i}
            res = self.client.post('/machinekit/spindle/override',
                                   headers={
                                       "API_KEY":
                                       CONFIG['security'].get("token"),
                                       "Content-Type": "application/json"
                                   },
                                   data=json.dumps(command))
            i += 0.1
            self.assert200(res)

    @ordered
    def test_pass_feed_override(self):
        """Test should pass and control the feed slider"""

        i = 0
        while i <= 1.2:
            command = {"command": i}
            res = self.client.post('/machinekit/feed',
                                   headers={
                                       "API_KEY":
                                       CONFIG['security'].get("token"),
                                       "Content-Type": "application/json"
                                   },
                                   data=json.dumps(command))
            i += 0.1
            self.assert200(res)

    @ordered
    def test_pass_maxvel_override(self):
        """Test should pass and control the maxvel slider"""

        i = 0
        while i <= 3000:
            command = {"command": i}
            res = self.client.post('/machinekit/maxvel',
                                   headers={
                                       "API_KEY":
                                       CONFIG['security'].get("token"),
                                       "Content-Type": "application/json"
                                   },
                                   data=json.dumps(command))
            i += 300
            self.assert200(res)

    @ordered
    def test_pass_enable_estop(self):
        """Test should pass and put the machine back in estop modus"""
        command = {"command": "estop"}
        res = self.client.post('/machinekit/status',
                               headers={
                                   "API_KEY": CONFIG['security'].get("token"),
                                   "Content-Type": "application/json"
                               },
                               data=json.dumps(command))
        self.assert200(res)

if __name__ == '__main__':
    unittest.main()
