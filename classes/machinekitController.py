#!/usr/bin/python
import os
import sys
import linuxcnc


def checkerrors(func):
    """ Decorator that checks if the machine returned any errors."""
    def wrapper(*args, **kwargs):
        errors = func(*args, **kwargs)
        if 'errors' in errors:
            raise RuntimeError(errors['errors'], 502, "RuntimeError")
        else:
            return {"success": "Command executed"}

    return wrapper


class MachinekitController():
    """ The Machinekit python interface in a class """
    def __init__(self, ini):
        """ Construct the class. Read values from passed .ini file"""
        self.s = linuxcnc.stat()
        self.c = linuxcnc.command()
        self.e = linuxcnc.error_channel()

        self.axes = self.set_axes()
        self.axes_with_cords = {}
        self.ini = linuxcnc.ini(ini)
        self.error_list = []

        self.max_feed_override = self.ini.find("DISPLAY", "MAX_FEED_OVERRIDE")
        self.max_spindle_override = self.ini.find("DISPLAY", "MAX_SPINDLE_OVERRIDE")
        self.max_velocity = self.ini.find("TRAJ", "MAX_VELOCITY")

    def set_axes(self):
        """Turn axe numbers into alphabetic values"""
        self.s.poll()
        axes_dict = {
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
        axes_in_machine = []
        while i < self.s.axes:
            axes_in_machine.append(axes_dict[i])
            i += 1
        return axes_in_machine

    def interp_state(self):
        """Return current interp state of machine. Ex: INTERP_IDLE"""
        modes = [
            "INTERP_IDLE", "INTERP_READING", "INTERP_PAUSED", "INTERP_WAITING"
        ]
        state = self.s.interp_state
        return modes[state - 1]

    def task_mode(self):
        """Return machine task mode"""
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
        """Read the error channel, return latest error as response and create an error list with all errors."""
        error = self.e.poll()
        if error:
            kind, text = error
            if kind in (linuxcnc.NML_ERROR, linuxcnc.OPERATOR_ERROR):
                typus = "error"
            else:
                typus = "info"
                typus, text

        if error is not None:
            if len(self.error_list) >= 50:
                self.error_list = []

            self.error_list.append(error[1])
            return {"errors": error[1]}
        else:
            return {}

    def ready_for_mdi_commands(self):
        """ Returns bool that represents if the machine is ready for MDI commands """
        self.s.poll()
        return not self.s.estop and self.s.enabled and self.s.homed and (
            self.s.interp_state == linuxcnc.INTERP_IDLE)

    def rcs_state(self):
        """ Return current rcs-state of the machine as string. Ex: RCS_DONE"""
        modes = ["RCS_DONE", "RCS_EXEC", "RCS_ERROR"]
        return modes[self.s.state - 1]

    def get_all_vitals(self):
        """Return most important machine values as dict"""
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
                "velocity": self.s.max_velocity,
                "max_acceleration": self.s.max_acceleration,
                "max_feed_override": self.max_feed_override,
                "max_spindle_override": self.max_spindle_override
            }
        }

    # SETTERS
    @checkerrors
    def machine_status(self, command):
        """ Toggle power/estop. takes 'estop' or 'power' as command"""
        self.s.poll()
        if command == "estop":
            if self.s.estop == linuxcnc.STATE_ESTOP:
                self.c.state(linuxcnc.STATE_ESTOP_RESET)
            else:
                self.c.state(linuxcnc.STATE_ESTOP)

            self.c.wait_complete()
            return self.errors()
        else:
            if self.s.estop == linuxcnc.STATE_ESTOP:
                return {
                    "errors":
                    "Can't turn on machine while it is in E_STOP modus"
                }
            if self.s.enabled:
                self.c.state(linuxcnc.STATE_OFF)
            else:
                self.c.state(linuxcnc.STATE_ON)

            self.c.wait_complete()
            return self.errors()

    @checkerrors
    def mdi_command(self, command):
        """ Send a MDI movement command to the machine, example "Y1 X1 Z-1" """
        # Check if the machine is ready for mdi commands
        self.s.poll()
        if self.s.interp_state is not linuxcnc.INTERP_IDLE:
            return {
                "errors":
                "Cannot execute command when machine interp state isn't idle"
            }

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
                "Cannot execute command when machine interp state isn't idle",
                502, "RuntimeError")

        self.ensure_mode(linuxcnc.MODE_MANUAL)

        self.c.jog(linuxcnc.JOG_INCREMENT, axes, speed, increment)
        return self.errors()

    @checkerrors
    def home_all_axes(self, command):
        """ Return all axes to the home position """
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
        """ Run the current file. Takes command as start || pause || stop || default=resume"""
        self.ensure_mode(linuxcnc.MODE_AUTO, linuxcnc.MODE_MDI)

        if command == "start":
            return self.task_run()
        elif command == "pause":
            return self.task_pause()
        elif command == "stop":
            return self.task_stop()
        else:
            return self.task_resume()

    @checkerrors
    def task_run(self):
        """ Run program from line 0"""
        self.s.poll()
        if self.s.task_mode not in (
                linuxcnc.MODE_AUTO,
                linuxcnc.MODE_MDI) or self.s.interp_state in (
                    linuxcnc.INTERP_READING, linuxcnc.INTERP_WAITING,
                    linuxcnc.INTERP_PAUSED):
            return {
                "errors":
                "Can't start machine because it is currently running or paused in a project"
            }

        self.ensure_mode(linuxcnc.MODE_AUTO)
        self.c.auto(linuxcnc.AUTO_RUN, 0)
        return self.errors()

    @checkerrors
    def task_pause(self):
        """ Pause current program """
        self.s.poll()
        if self.s.interp_state is linuxcnc.INTERP_PAUSED:
            return {"errors": "Machine is already paused."}
        if self.s.task_mode not in (
                linuxcnc.MODE_AUTO,
                linuxcnc.MODE_MDI) or self.s.interp_state not in (
                    linuxcnc.INTERP_READING, linuxcnc.INTERP_WAITING):
            return {
                "errors":
                "Machine not ready to recieve pause command. Probably because its currently not working on a program"
            }
        self.ensure_mode(linuxcnc.MODE_AUTO)
        self.c.auto(linuxcnc.AUTO_PAUSE)

        return self.errors()

    @checkerrors
    def task_resume(self):
        """ Resume current program """
        self.s.poll()
        if self.s.task_mode not in (
                linuxcnc.MODE_AUTO, linuxcnc.MODE_MDI
        ) or self.s.interp_state is not linuxcnc.INTERP_PAUSED:
            return {
                "errors":
                "Machine not ready to resume. Probably because the machine is not paused or not in auto modus"
            }
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
        self.s.poll()
        brake_command = None
        if "brake_engage" in command:
            brake_command = linuxcnc.BRAKE_ENGAGE
        else:
            brake_command = linuxcnc.BRAKE_RELEASE

        if self.s.spindle_brake == brake_command:
            return {
                "errors":
                "Command could not be executed because the spindle_brake is already in this state"
            }

        self.ensure_mode(linuxcnc.MODE_MANUAL)
        self.c.brake(brake_command)

        return self.errors()

    @checkerrors
    def spindle_direction(self, command):
        """ Command takes parameters spindle_forward and spindle_reverse"""
        self.s.poll()
        commands = {
            "spindle_forward": linuxcnc.SPINDLE_FORWARD,
            "spindle_reverse": linuxcnc.SPINDLE_REVERSE,
        }

        if self.s.spindle_direction == commands[command]:
            return {
                "errors":
                "Command could not be executed because the spindle_direction is already in this state"
            }

        self.ensure_mode(linuxcnc.MODE_MANUAL)
        self.c.spindle(commands[command])
        return self.errors()

    @checkerrors
    def spindle_speed(self, command):
        """ Command takes parameters spindle_increase and spindle_decrease """
        self.s.poll()

        if not self.s.spindle_enabled:
            return {
                "errors":
                "Command could not be executed because the spindle is not enabled"
            }

        commands = {
            "spindle_increase": linuxcnc.SPINDLE_INCREASE,
            "spindle_decrease": linuxcnc.SPINDLE_DECREASE
        }
        self.ensure_mode(linuxcnc.MODE_MANUAL)
        self.c.spindle(commands[command])
        return self.errors()

    @checkerrors
    def spindle_enabled(self, command):
        """Enable/disable spindle"""
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
        self.c.spindleoverride(value)
        self.c.wait_complete(0.3)
        return self.errors()

    @checkerrors
    def maxvel(self, maxvel):
        """ Takes int of maxvel min"""
        self.c.maxvel(maxvel / 60.)
        self.c.wait_complete(0.3)
        return self.errors()

    @checkerrors
    def feedoverride(self, value):
        """ Feed override float between 0 and 1.2"""
        # self.s.poll()
        self.c.feedrate(value)
        self.c.wait_complete(0.3)
        return self.errors()

    @checkerrors
    def open_file(self, path, file_name):
        """ Open file in the /files dir on the beagleboi """
        self.s.poll()

        if self.s.interp_state is not linuxcnc.INTERP_IDLE:
            return {"errors": "Cannot execute command when interp is not idle"}

        self.ensure_mode(linuxcnc.MODE_MDI)

        if not file_name:
            self.c.reset_interpreter()
            self.c.wait_complete()
            return self.errors()

        self.c.reset_interpreter()
        self.c.wait_complete()
        self.c.program_open(os.path.join(path + "/" + file_name))
        return self.errors()

    @checkerrors
    def set_offset(self):
        """Set offset"""
        self.s.poll()

        if self.s.interp_state is not linuxcnc.INTERP_IDLE:
            return {"errors": "Cannot execute command when interp is not idle"}

        #jointnum, home_pos, home_offset, home_final_velocity, home_search_velocity, home_final_velocity, use_index, ignore_limits, is_shared, home_sequence, volatile_home, locking_indexer
        self.c.set_home_parameters(0, 0, 0, 10, 10, 10, 10, 10, 1, 1, 2, 1)
        return self.errors()
