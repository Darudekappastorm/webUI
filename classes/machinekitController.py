#!/usr/bin/python
import linuxcnc
import sys

def checkerrors(f):
    """ Decorator that checks if the machine returned any errors."""
    def wrapper(*args, **kwargs):
        errors = f(*args, **kwargs)
        if 'errors' in errors:
            raise RuntimeError({"message": errors['errors'], "status": 502})
        else:
            return {"success": "Command executed"}
    return wrapper

class MachinekitController():
    """ The Machinekit python interface in a class """

    def __init__(self, ini):
            self.s = linuxcnc.stat()
            self.c = linuxcnc.command()
            self.e = linuxcnc.error_channel()
            self.axes = self.set_axes()
            self.axes_with_cords = {}
            self.ini = linuxcnc.ini(ini)
            
            self.max_feed_override = self.ini.find("DISPLAY", "MAX_FEED_OVERRIDE")
            self.max_spindle_override = self.ini.find("DISPLAY", "MAX_SPINDLE_OVERRIDE")
            self.max_velocity = self.s.max_velocity * 60


    # Class is split up in getters and setters 

    def set_axes(self):
        self.s.poll()
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
            pos = round(self.s.axis[i]['input'], 3)
            self.axes_with_cords[self.axes[i]] = {"pos": pos, "homed": homed}
            i += 1
        return self.axes_with_cords

    def errors(self):
        """ Check the machine error channel """
        error = self.e.poll()
        if error:
            kind, text = error
            if kind in (linuxcnc.NML_ERROR, linuxcnc.OPERATOR_ERROR):
                typus = "error"
            else:
                typus = "info"
                typus, text

        if error is not None:
            return {"errors": error[1]}
        else:
            return {}

    def ready_for_mdi_commands(self):
        """ Returns bool that represents if the machine is ready for MDI commands """
        self.s.poll()
        return not self.s.estop and self.s.enabled and self.s.homed and (self.s.interp_state == linuxcnc.INTERP_IDLE)

    def rcs_state(self):
        modes = ["RCS_DONE", "RCS_EXEC", "RCS_ERROR"]
        return modes[self.s.state -1]

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
                "max_velocity": self.max_velocity,
                "max_acceleration": self.s.max_acceleration,
                "max_feed_override": self.max_feed_override,
                "max_spindle_override": self.max_spindle_override
            }
        }
    
    # SETTERS
    @checkerrors
    def machine_status(self, command):
        """ Toggle estop and power with command estop || power"""
        if command != "estop" and command != "power":
            raise ValueError({"message": "Unknown command " + command, "status": 400, "type": "ValueError"})

        self.s.poll()
        if command == "estop":
            if self.s.estop == linuxcnc.STATE_ESTOP:
                self.c.state(linuxcnc.STATE_ESTOP_RESET)
            else:
                self.c.state(linuxcnc.STATE_ESTOP)

            self.c.wait_complete()
            return self.errors()

        if command == "power":
            if self.s.estop == linuxcnc.STATE_ESTOP:
                return {"errors": "Can't turn on machine while it is in E_STOP modus"}
            if self.s.enabled:
                self.c.state(linuxcnc.STATE_OFF)
            else:
                self.c.state(linuxcnc.STATE_ON)
            self.c.wait_complete()
            return self.errors()

    @checkerrors
    def mdi_command(self, command):
        print("called")
        """ Send a MDI movement command to the machine, example "Y1 X1 Z-1" """
        # Check if the machine is ready for mdi commands
        self.s.poll()
        if self.s.interp_state is not linuxcnc.INTERP_IDLE:
            return {"errors": "Cannot execute command when machine interp state isn't idle"}

        mdi_command = "G0 " + command

        self.ensure_mode(linuxcnc.MODE_MDI)
        self.c.mdi(str(mdi_command))
        return self.errors()

    @checkerrors
    def manual_control(self, axes, speed, increment):
        """ Manual continious transmission. axes=int speed=int in mm increment=int in mm"""
        self.s.poll()
        if self.s.interp_state is not linuxcnc.INTERP_IDLE:
            raise RuntimeError(
                {"message": "Cannot execute command when machine interp state isn't idle", "status": 502})

        self.ensure_mode(linuxcnc.MODE_MANUAL)

        self.c.jog(linuxcnc.JOG_INCREMENT, int(axes), float(speed), int(increment))
        return self.errors()


    @checkerrors
    def home_all_axes(self, command):
        """ Set all axes home """
        if command != "home" and command != "unhome":
            raise ValueError({"message": "Unknown command " + command, "status": 400, "type": "ValueError"})
      
        if command == "unhome":
            return self.unhome_all_axes()
            
        self.ensure_mode(linuxcnc.MODE_MANUAL)
        self.c.home(-1)
        self.c.wait_complete()
        return self.errors()

    @checkerrors
    def unhome_all_axes(self):
        """ Unhome all axes """
        self.ensure_mode(linuxcnc.MODE_MANUAL)
        self.c.unhome(-1)
        self.c.wait_complete()
        return self.errors()

    def run_program(self, command):
        """ Command = start || pause || stop || resume = default"""
        if command != "start" and command != "pause" and command != "stop" and command != "resume":
            raise ValueError(
                {"message": "Unknown command " + command, "status": 400, "type": "ValueError"})

        self.ensure_mode(linuxcnc.MODE_AUTO, linuxcnc.MODE_MDI)

        if command == "start":
            return self.task_run(9)
        elif command == "pause":
            return self.task_pause()
        elif command == "stop":
            return self.task_stop()
        else:
            return self.task_resume()

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
        
        if self.s.interp_state is not linuxcnc.INTERP_IDLE:
            return {"errors": "Cannot execute command when machine interp state isn't idle"}

        self.ensure_mode(linuxcnc.MODE_MANUAL)
        self.c.brake(brake_command)

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

        self.ensure_mode(linuxcnc.MODE_MANUAL)
        self.c.spindle(commands[command])
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
        self.ensure_mode(linuxcnc.MODE_MANUAL)
        self.c.spindle(commands[command])
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

        self.ensure_mode(linuxcnc.MODE_MANUAL)
        self.c.spindle(commands[command])
        return self.errors()
    
    @checkerrors
    def spindleoverride(self, value):
        """ Spindle override floatyboii betweem 0 and 1"""
        if value > 1 or value < 0:
            return {"errors": "Value outside of limits"}

        self.c.spindleoverride(value)
        self.c.wait_complete()
        return self.errors()

    @checkerrors
    def maxvel(self, maxvel):
        """ Takes int of maxvel min"""
        self.c.maxvel(maxvel / 60.)
        self.c.wait_complete()

        return self.errors()
    

    @checkerrors
    def feedoverride(self, value):
        """ Feed override float between 0 and 1.2"""
        if value > 1.2 or value < 0:
            raise ValueError(
                {"message": "Value is outside of range. min 0 max 1.2", "status": 400, "type": "ValueError"})
                
        self.s.poll()
        self.c.feedrate(value)
        self.c.wait_complete()

        return self.errors()

    @checkerrors
    def open_file(self, path):
        """ Open file in the /files dir on the beagleboi """ 
        self.s.poll()

        if self.s.interp_state is not linuxcnc.INTERP_IDLE:
            return {"errors": "Cannot execute command when interp is not idle"}

        self.ensure_mode(linuxcnc.MODE_MDI)
        self.c.reset_interpreter()
        self.c.wait_complete()
        self.c.program_open(path)
        self.c.wait_complete()

        return self.errors()

    @checkerrors
    def set_offset(self):
        self.s.poll()

        if self.s.interp_state is not linuxcnc.INTERP_IDLE:
            return {"errors": "Cannot execute command when interp is not idle"}
     
        #toolno, z_offset,  x_offset, diameter, frontangle, backangle, orientation
        #self.s.tool_offset(int, float, float, float, float, float, int)
        return self.errors()


