#!/usr/bin/python
def checkerrors(f):
    """ Decorator that checks if the machine returned any errors."""
    def wrapper(*args, **kwargs):
        errors = f(*args, **kwargs)
        if 'errors' in errors:
            raise RuntimeError({"message": errors['errors'], "status": 502})
        else:
            return {"success": "Command executed"}
    return wrapper


class linuxcnc():
    INTERP_IDLE = 1
    INTERP_READING = 2
    INTERP_PAUSED = 3
    INTERP_WAITING = 4

    RCS_DONE = 1
    RCS_EXEC = 2
    RCS_ERROR = 3

    MODE_MDI = 1
    MODE_AUTO = 2
    MODE_MANUAL = 3

    STATE_ESTOP = True
    STATE_ESTOP_RESET = False

    STATE_DISABLED = False
    STATE_ENABLED = True

    SPINDLE_FORWARD = 1
    SPINDLE_REVERSE = -1
    SPINDLE_OFF = 0
    SPINDLE_ON = 1
    SPINDLE_INCREASE = 100
    SPINDLE_DECREASE = -100
    SPINDLE_CONSTANT = 50

    BRAKE_ENGAGE = 1
    BRAKE_RELEASE = 0
    class stat():
        def __init__(self):
            print("Hello from stat")
            self.axes = 3
            self.enabled = 1
            self.estop = linuxcnc.STATE_ESTOP_RESET
            self.power = linuxcnc.STATE_ENABLED
            self.homed = 1

            self.interp_state = linuxcnc.INTERP_IDLE
            self.state = linuxcnc.RCS_DONE

            self.task_mode = linuxcnc.MODE_MDI
            self.axis = self.generateAxis()

            self.spindle_speed = 300
            self.spindle_enabled = 1
            self.spindle_brake = 0
            self.spindle_direction = 1
            self.spindle_increasing = 0
            self.spindle_override_enabled = 0
            self.spindlerate = 1
            self.tool_in_spindle = 0

            self.file = "/dir/files/smile.nc"
            self.feedrate = 1
            self.velocity = 1200
            self.max_velocity = 50
            self.max_acceleration = 5000
            self.pocket_prepped = -1

        def state(self, command):
            if command == "power":
                print(self.power)
            else:
                print(self.estop)

        def poll(self):
            return True

        def generateAxis(self):
            i = 0
            axis = {}

            while i < self.axes:
                axis.update({i: {"homed": 0, "pos": 0}})
                i += 1
            return axis

    class command():
        def __init__(self):
            print("Hello from command")
        
        def wait_complete(self):
            return True
        
        def state(self, command):
            print()

    class error_channel():
        def __init__(self):
            print("Hello from error channel")

        def poll(self):
            return True



class MachinekitController():
    """ The Machinekit python interface in a class """

    def __init__(self):
        self.s = linuxcnc.stat()
        self.c = linuxcnc.command()
        self.e = linuxcnc.error_channel()
        self.axes = self.set_axes()
        self.axes_with_cords = {}

    # Class is split up in getters and setters

    def set_axes(self):
        axesDict = {
            0: "x",
            1: "y",
            2: "z",
            3: "a",
            4: "b",
            5: "c",
            6: "u",
            7: "v",
            8: "w",
        }
        i = 0
        axesInMachine = []
        while i < self.s.axes:
            axesInMachine.append(axesDict[i])
            i += 1
        return axesInMachine

    def interp_state(self):
        self.s.poll()
        modes = ["INTERP_IDLE", "INTERP_READING",
                 "INTERP_PAUSED", "INTERP_WAITING"]
        state = self.s.interp_state
        return modes[state - 1]

    def task_mode(self):
        modes = ["MODE_MANUAL", "MODE_AUTO", "MODE_MDI"]
        return modes[self.s.task_mode - 1]

    def axes_position(self):
        """ Loop over axes and return position: {"[axe]": {"homed": bool, "pos": float}} """
        i = 0
        while i < len(self.axes):
            homed = bool(self.s.axis[i]["homed"])
            pos = round(self.s.axis[i]['pos'], 3)
            self.axes_with_cords[self.axes[i]] = {"pos": pos, "homed": homed}
            i += 1

        return self.axes_with_cords

    def errors(self):
        """ Check the machine error channel """
        return {}

    def ready_for_mdi_commands(self):
        """ Returns bool that represents if the machine is ready for MDI commands """
        self.s.poll()
        return not self.s.estop and self.s.enabled and self.s.homed and (self.s.interp_state == linuxcnc.INTERP_IDLE)

    def rcs_state(self):
        modes = ["RCS_DONE", "RCS_EXEC", "RCS_ERROR"]
        return modes[self.s.state - 1]

    def get_all_vitals(self):
        self.s.poll()
        return {
            "power": {
                "enabled": self.s.enabled,
                "estop": bool(self.s.estop)
            },
            "position": self.axes_position(),
            "spindle": {
                "spindle_speed": self.s.spindle_speed,
                "spindle_enabled": self.s.spindle_enabled,
                "spindle_brake": self.s.spindle_brake,
                "spindle_direction": self.s.spindle_direction,
                "spindle_increasing": self.s.spindle_increasing,
                "spindle_override_enabled": self.s.spindle_override_enabled,
                "spindlerate": self.s.spindlerate,
                "tool_in_spindle": self.s.tool_in_spindle
            },
            "program": {
                "file": self.s.file,
                "interp_state": self.interp_state(),
                "task_mode": self.task_mode(),
                "feedrate": self.s.feedrate,
                "rcs_state": self.rcs_state(),
                "tool_change": self.s.pocket_prepped
            },
            "values": {
                "velocity": self.s.velocity,
                "max_velocity": self.s.max_velocity * 60,
                "max_acceleration": self.s.max_acceleration
            }
        }

    # SETTERS
    @checkerrors
    def machine_status(self, command):
        """ Toggle estop and power with command estop || power"""
        if command != "estop" and command != "power":
            raise ValueError({"message": "Unknown command " +
                              command, "status": 400, "type": "ValueError"})

        self.s.poll()
        if command == "estop":
            if self.s.estop == linuxcnc.STATE_ESTOP:
                self.s.estop = linuxcnc.STATE_ESTOP_RESET
            else:
                self.s.estop = linuxcnc.STATE_ESTOP

            self.c.wait_complete()
            return self.errors()

        if command == "power":
            if self.s.estop == linuxcnc.STATE_ESTOP:
                return {"errors": "Can't turn on machine while it is in E_STOP modus"}
            print(self.s.enabled)
            if self.s.enabled:
                self.s.enabled = linuxcnc.STATE_DISABLED
            else:
                self.s.enabled = linuxcnc.STATE_ENABLED

            self.c.wait_complete()
            return self.errors()

    @checkerrors
    def mdi_command(self, command):
        """ Send a MDI movement command to the machine, example "Y1 X1 Z-1" """
        # Check if the machine is ready for mdi commands
        self.s.poll()
        if self.s.interp_state is not linuxcnc.INTERP_IDLE:
            return {"errors": "Cannot execute command when machine interp state isn't idle"}
        i = 0
        axe = 1
        lastMatch = 0
        values = []
        for letter in command:
            i += 1
            if letter == "X" or letter == "Y" or letter == "Z":
                #set last found element to i
                if lastMatch is not 0:
                    self.s.axis[axe - 2]['pos'] = float(command[lastMatch: i - 1].replace(" ", ""))
                    if axe == 3:
                        self.s.axis[axe - 1]['pos'] = float(command[i: len(command)])
                lastMatch = i
                axe += 1

        return self.errors()

    @checkerrors
    def manual_control(self, axes, speed, increment):
        """ Manual continious transmission. axes=int speed=int in mm increment=int in mm"""
        self.s.poll()
        if self.s.interp_state is not linuxcnc.INTERP_IDLE:
            raise RuntimeError(
                {"message": "Cannot execute command when machine interp state isn't idle", "status": 502})

        self.s.axis[int(axes)]['pos'] += int(increment)
        return self.errors()

    @checkerrors
    def home_all_axes(self, command):
        """ Set all axes home """
        if command != "home" and command != "unhome":
            raise ValueError({"message": "Unknown command " +
                              command, "status": 400, "type": "ValueError"})

        if command == "unhome":
            return self.unhome_all_axes()

        self.c.wait_complete()
      
        for key in self.s.axis:
            self.s.axis[key]['homed'] = True

        return self.errors()

    @checkerrors
    def unhome_all_axes(self):
        """ Unhome all axes """
        for key in self.s.axis:
            self.s.axis[key]['homed'] = False
        self.c.wait_complete()
        return self.errors()

    def run_program(self, command):
        """ Command = start || pause || stop || resume = default"""
        if command != "start" and command != "pause" and command != "stop" and command != "resume":
            raise ValueError(
                {"message": "Unknown command " + command, "status": 400, "type": "ValueError"})

        self.ensure_mode(linuxcnc.MODE_AUTO, linuxcnc.MODE_MDI)

        if command == "start":
            self.s.interp_state = linuxcnc.INTERP_READING
            return {"success": "Command executed"}
        elif command == "pause":
            self.s.interp_state = linuxcnc.INTERP_PAUSED
            return {"success": "Command executed"}
        elif command == "stop":
            self.s.interp_state = linuxcnc.INTERP_IDLE
            return {"success": "Command executed"}
        else:
            self.s.interp_state = linuxcnc.INTERP_WAITING
            return {"success": "Command executed"}
            

    @checkerrors
    def task_run(self, start_line):
        """ Run program from line """
        self.s.poll()
        if self.s.task_mode not in (linuxcnc.MODE_AUTO, linuxcnc.MODE_MDI) or self.s.interp_state in (linuxcnc.INTERP_READING, linuxcnc.INTERP_WAITING, linuxcnc.INTERP_PAUSED):
            return {"errors": "Can't start machine because it is currently running or paused in a project"}
        self.ensure_mode(linuxcnc.MODE_AUTO)
        self.c.auto(linuxcnc.AUTO_RUN, 9)

        return self.errors()

    @checkerrors
    def task_pause(self):
        """ Pause current program """
        self.s.poll()
        if self.s.interp_state is linuxcnc.INTERP_PAUSED:
            return {"errors": "Machine is already paused."}
        if self.s.task_mode not in (linuxcnc.MODE_AUTO, linuxcnc.MODE_MDI) or self.s.interp_state not in (linuxcnc.INTERP_READING, linuxcnc.INTERP_WAITING):
            return {"errors": "Machine not ready to recieve pause command. Probably because its currently not working on a program"}
        self.ensure_mode(linuxcnc.MODE_AUTO)
        self.c.auto(linuxcnc.AUTO_PAUSE)

        return self.errors()

    @checkerrors
    def task_resume(self):
        """ Resume current program """
        self.s.poll()
        if self.s.task_mode not in (linuxcnc.MODE_AUTO, linuxcnc.MODE_MDI) or self.s.interp_state is not linuxcnc.INTERP_PAUSED:
            return {"errors": "Machine not ready to resume. Probably because the machine is not paused or not in auto modus"}
        self.ensure_mode(linuxcnc.MODE_AUTO)
        self.c.auto(linuxcnc.AUTO_RESUME)

        return self.errors()

    @checkerrors
    def task_stop(self):
        """ Stop/abort current program """
        self.c.abort()
        self.c.wait_complete()

        return self.errors()

    def ensure_mode(self, m, *p):
        """ Ensure that the machine is in given mode. If not switch the mode """
        self.s.poll()
        if self.s.task_mode == m or self.s.task_mode in p:
            return True
        if self.running(do_poll=False):
            return False
        self.c.mode(m)
        self.c.wait_complete()
        return True

    def running(self, do_poll=True):
        if do_poll:
            self.s.poll()
        return self.s.task_mode == linuxcnc.MODE_AUTO and self.s.interp_state is not linuxcnc.INTERP_IDLE

 
    @checkerrors
    def spindle_brake(self, command):
        """ Engage the spindle brake"""
        if "brake_engage" not in command and "brake_release" not in command:
            raise ValueError({"message": "unknown command", "status": 400, "type": "ValueError"})

        self.s.poll()
        brake_command = None

        if "brake_engage" in command:
            brake_command = linuxcnc.BRAKE_ENGAGE
        else:
            brake_command = linuxcnc.BRAKE_RELEASE

        if self.s.spindle_brake == brake_command:
            return {"errors": "Command could not be executed because the spindle_brake is already in this state"}
        
        if brake_command == linuxcnc.BRAKE_ENGAGE:
            self.s.spindle_direction = 0

        self.s.spindle_brake = brake_command
        return self.errors()

    @checkerrors
    def spindle_direction(self, command):
        """ Command takes parameters spindle_forward and spindle_reverse"""
        if "spindle_forward" not in command and "spindle_reverse" not in command:
            raise ValueError({"message": "unknown command",
                              "status": 400, "type": "ValueError"})

        self.s.poll() 
        commands = {
            "spindle_forward": linuxcnc.SPINDLE_FORWARD, 
            "spindle_reverse": linuxcnc.SPINDLE_REVERSE, 
            }

        if self.s.spindle_direction == commands[command]:
            return {"errors": "Command could not be executed because the spindle_direction is already in this state"}
        self.s.spindle_enabled = linuxcnc.SPINDLE_ON
        self.s.spindle_brake = linuxcnc.BRAKE_RELEASE
        self.s.spindle_direction = commands[command]
        return self.errors()

    @checkerrors
    def spindle_speed(self, command):
        """ Command takes parameters spindle_increase and spindle_decrease """
        if "spindle_increase" not in command and "spindle_decrease" not in command:
            raise ValueError({"message": "Unknown command", "status": 400, "type": "ValueError"})
    
        self.s.poll()

        if not self.s.spindle_enabled:
            return {"errors": "Command could not be executed because the spindle is not enabled"}

        commands = {
            "spindle_increase": linuxcnc.SPINDLE_INCREASE,
            "spindle_decrease": linuxcnc.SPINDLE_DECREASE
        }
        self.s.spindle_speed += commands[command]
        return self.errors()
        

    @checkerrors
    def spindle_enabled(self, command):
        if "spindle_off" not in command and "spindle_on" not in command:
            raise ValueError({"message": "Unknown command",
                              "status": 400, "type": "ValueError"})

        commands = {
            "spindle_off": linuxcnc.SPINDLE_OFF,
            "spindle_on": linuxcnc.SPINDLE_CONSTANT
        }

        self.s.spindle_enabled = commands[command]
        return self.errors()
    
    @checkerrors
    def spindleoverride(self, value):
        """ Spindle override floatyboii betweem 0 and 1"""
        if value > 1 or value < 0:
            return {"errors": "Value outside of limits"}
        self.s.spindlerate = value
        return self.errors()

    @checkerrors
    def maxvel(self, maxvel):
        """ Takes int of maxvel min"""
        self.s.max_velocity = (maxvel / 60)
        return self.errors()

    @checkerrors
    def feedoverride(self, value):
        """ Feed override float between 0 and 1.2"""
        if value > 1.2 or value < 0:
            raise ValueError(
                {"message": "Value is outside of range. min 0 max 1.2", "status": 400, "type": "ValueError"})

        self.s.poll()
        self.s.feedrate = value
        return self.errors()

    @checkerrors
    def open_file(self, path):
        """ Open file in the /files dir on the beagleboi """
        self.s.poll()

        if self.s.interp_state is not linuxcnc.INTERP_IDLE:
            return {"errors": "Cannot execute command when interp is not idle"}


        self.s.file = path
        return self.errors()

    @checkerrors
    def set_offset(self):
        self.s.poll()

        if self.s.interp_state is not linuxcnc.INTERP_IDLE:
            return {"errors": "Cannot execute command when interp is not idle"}

        # toolno, z_offset,  x_offset, diameter, frontangle, backangle, orientation
        # self.s.tool_offset(int, float, float, float, float, float, int)
        return self.errors()
