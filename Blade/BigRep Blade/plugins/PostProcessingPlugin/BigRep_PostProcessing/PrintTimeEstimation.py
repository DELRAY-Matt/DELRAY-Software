# coding=utf-8

# Copyright (c) 2018 BigRep GmbH

from __future__ import (print_function, absolute_import)

import sys
import re
from math import sqrt
import warnings

"""
Standard 3d printer simulator, tracks machine status as the g-code is interpreted
"""


class PrintTimeEstimation:
    """
    Standard 3d printer simulator
    Tracks machine position, temperatures, current extruder, used filament per extruder and other as gcode is passed
    through
    """
    # TODO: implement motion simulator? (for more accurate time tracking)

    REGEX_TAG_TEMPLATE = r'^{var}[+-]?[\d.]+$|^{var}$'
    REGEX_TAG_VALUE_TEMPLATE = r'{var}(?P<val>[+-]?[\d.]+)'

    machine_start_settings = dict(
        dist=float('inf'),
        file_pos=0,
        machine=dict(
            target_temps=dict(
                tool0=.0,
                tool1=.0,
                bed=.0
            ),
            X=.0,
            Y=.0,
            Z=.0,
            E=.0,
            F0=.0,
            F1=.0,
            tool=0
        )
    )

    def __init__(self, printer_type=None, callback_function=warnings.warn):
        """
        Setup machine startup position and settings,
        Initialize list of gcodes accepted,
        Set the warning_callback function, replacing the default 'warnings.warn'
        ex.: octoprint logger
        :param callback_function: function to call for when warning occur, input must be string
        """
        # TODO: init with specific machine settings?

        # start machine related variables with default values
        self.position = None
        self.absolutes = None
        self.current_tool = None
        self.target_temps = None
        self.fan_status = None
        self.new_position = None
        self.machine_units = None
        self.feedrate_multiplier = 100
        self.flowrate_multiplier = 100
        self.reset_machine()  # set default values

        self.mechanics = MechanicalPrinter(printer_type)

        # setup GCode interpretation
        self.valid_gcode = {
            'G0': (lambda line: self.move('0', line)),
            'G1': (lambda line: self.move('1', line)),
            'G20': (lambda line: self.set_units('in')),
            'G21': (lambda line: self.set_units('mm')),
            'G28': self.home,
            'G90': (lambda line: self.change_absolute(True, True)),
            'G91': (lambda line: self.change_absolute(False, False)),
            'G92': (lambda line: self.set_position(line)),

            'M82': (lambda line: self.change_absolute(None, True)),
            'M83': (lambda line: self.change_absolute(None, False)),
            'M104': (lambda line: self.set_temp(line, 'tool')),
            'M105': self.no_op_gcode_execution,
            'M106': self.set_fan,
            'M107': (lambda line: self.set_fan(line + ' S0')),  # M107 == M106 S0
            'M109': (lambda line: self.set_temp(line, 'tool')),
            'M110': self.no_op_gcode_execution,
            'M114': self.no_op_gcode_execution,
            'M140': (lambda line: self.set_temp(line, 'bed')),
            'M190': (lambda line: self.set_temp(line, 'bed')),
            'M220': self.set_multiplier,  # TODO: store feedrate?
            'M221': self.set_multiplier,  # TODO: store flowrate?
            'M600': self.no_op_gcode_execution,
            'M601': self.no_op_gcode_execution,
            'M602': self.no_op_gcode_execution,
            'M603': self.no_op_gcode_execution,
            'M604': self.no_op_gcode_execution,
            'M800': (lambda line: self.start_print()),
            'M801': (lambda line: self.end_print()),

            'T0': (lambda line: self.change_tool(0)),
            'T1': (lambda line: self.change_tool(1)),
            'T2': (lambda line: self.change_tool(2))
        }

        # default callback for warnings
        self.warning_callback = callback_function

        self.new_position = False
        self.new_setting = False

    def start_print(self):
        self.mechanics.start_print()

    def end_print(self):
        self.mechanics.wait_empty_queue()

    def set_warning_callback(self, callback_function):
        """
        set the warning_callback function, replacing the default 'warnings.warn'
        ex.: octoprint logger
        :param callback_function: function to call for when warning occur, input must be string
        :return:
        """
        self.warning_callback = callback_function

    def reset_machine(self):
        """
        set machine variables to starting value
        :return: None
        """
        self.position = {'X': .0, 'Y': .0, 'Z': .0, 'E': .0, 'F0': .0, 'F1': .0}
        self.absolutes = [True, True]  # cartesian, extruder
        self.current_tool = 0
        self.target_temps = dict(
            tool0=.0,
            tool1=.0,
            bed=.0
        )
        self.fan_status = dict(
            tool0=0,
            tool1=0,
        )
        self.new_position = False
        self.new_setting = False
        self.machine_units = 'mm'
        self.feedrate_multiplier = 100
        self.flowrate_multiplier = 100

    def process(self, line):
        """
        Processes file lines
        Strips comments and individual command lines, raises warning if unrecognized tags pop up (bad comments)
        :param line: Gcode line
        :return:
        """
        self.new_position = False
        self.new_setting = False

        tags = line.split(';')[0].split()  # excludes comments and split individual tags or words
        # tags is list of G-Code tags. Example ['G1', 'X100', Y110', 'E3000' ]

        for individual_command, individual_command_line in self.split_command_line(tags):
            if individual_command in self.valid_gcode:
                self.valid_gcode[individual_command](individual_command_line)
            else:
                self.warning_callback("Gcode not implemented: '%s'" % individual_command_line)

    def split_command_line(self, tags):
        """
        Separates G-Code commands and keeps they're variables together
        :param tags: All gcode tags, Example ['G1', 'X100', Y110', 'E3000' ]
        :return: G-Code command and Full G-Code command line with variables
        """

        individual_command_line = None
        individual_command = None

        while len(tags) > 0:
            possible_command = tags.pop(0)
            if individual_command_line is not None:
                if re.match(self.REGEX_TAG_TEMPLATE.format(var='[GMT]'), possible_command) is not None:
                    yield (individual_command, individual_command_line)
                    individual_command = possible_command
                    individual_command_line = possible_command
                elif re.match(self.REGEX_TAG_TEMPLATE.format(var='[A-Z]'), possible_command) is not None:
                    individual_command_line += " " + possible_command
                else:
                    self.warning_callback("Not a valid variable '%s'" % possible_command)

            else:
                if re.match(self.REGEX_TAG_TEMPLATE.format(var='[GMT]'), possible_command) is not None:
                    individual_command = possible_command
                    individual_command_line = possible_command
                else:
                    self.warning_callback("Not a valid gcode start '%s'" % possible_command)

        if individual_command_line is not None:
            yield (individual_command, individual_command_line)

    @staticmethod
    def no_op_gcode_execution(cmd):
        """
        dummy function for gcodes that don't change any internal state
        :param cmd:
        :return:
        """
        pass

    def set_multiplier(self, line):
        """

        :param line:
        :return:
        """
        value = None
        try:
            value = int(self.get_tag('S', line))
        except:
            pass
        else:
            self.new_setting = True
            if "M220" in line:
                self.feedrate_multiplier = value
            elif "M221" in line:
                self.flowrate_multiplier = value

    def set_temp(self, line, heater='tool'):
        """
        Processes set temperature G-Code
        :param heater: type of heater, 'tool' or 'bed'
        :param line: Full G-Code line with temperature settings, Ex.: 'M104 S205'
        :return:
        """
        if heater == 'tool':
            heater = str(self.current_tool)
            value = self.get_tag('H', line)
            if value is not None:
                heater = str(value)
            heater = 'tool' + heater

        new_temp = None
        try:
            new_temp = float(self.get_tag('S', line))
        except:
            pass
        else:
            if heater == 'tool0' or heater == 'tool1' or heater == 'bed':
                self.new_setting = new_temp != self.target_temps[heater]
                self.target_temps[heater] = new_temp

    def set_fan(self, cmd):
        """
        Updates fan value for extruder on set on line, or current one
        :param cmd:
        :return:
        """

        fan = 'tool' + str(self.current_tool)
        value = self.get_tag('P', cmd)
        if value is not None:
            fan = 'tool' + str(value)

        try:
            new_fan_value = int(self.get_tag('S', cmd))
        except:
            fan_value = 255  # default value for M106, no S tag
        else:
            fan_value = new_fan_value

        self.new_setting = self.fan_status[fan] != fan_value
        self.fan_status[fan] = fan_value

    def set_units(self, units):
        """
        set machine units to inch or mm (G20 or G21)
        :param units:
        :return:
        """
        self.mechanics.wait_empty_queue()
        self.machine_units = units

    def change_tool(self, new_tool):
        """
        processes tool changes
        :param new_tool: tool index
        :return:
        """
        self.mechanics.wait_empty_queue()
        self.mechanics.print_time += 2.8  # for the ONE
        self.current_tool = int(new_tool)

        self.new_setting = True

    def set_position(self, cmd):
        """
        G92
        :param cmd:
        :return:
        """
        self.mechanics.wait_empty_queue()
        for axis in self.position:
            try:
                value = float(self.get_tag(axis, cmd))
            except:
                pass
            else:
                self.position[axis] = value

        self.new_position = True

    def change_absolute(self, cartesian, extruder):
        """
        Change to absolute/relative mode is done here
        :param cartesian:
        :param extruder:
        :return:
        """
        self.mechanics.wait_empty_queue()
        if cartesian is not None:
            self.absolutes[0] = cartesian
        self.absolutes[1] = extruder

        self.new_setting = True

    def home(self, cmd):
        """
        Home command is processed here
        :param cmd:
        :return:
        """
        self.mechanics.wait_empty_queue()
        full = True
        for axis in ['X', 'Y', 'Z']:
            if axis in cmd:
                self.mechanics.print_time += 10.
                self.position[axis] = 0.
                full = False
        if full:
            for axis in ['X', 'Y', 'Z']:
                self.mechanics.print_time += 10.
                self.position[axis] = 0.

        self.new_position = True

    @staticmethod
    def get_tag(tag, line):
        """
        Gets value of tag in G-Code line (Z.b. E100 returns '100' )
        :param tag: tag in to search for in G-Code
        :param line: actual command line
        :return: match value if found, None otherwise
        """
        match = re.search(PrintTimeEstimation.REGEX_TAG_VALUE_TEMPLATE.format(var=tag), line)
        if match is None:
            return None
        return match.group('val')

    def move(self, tag, cmd):
        """
        Moves hare processed here
        :param tag: GCode tag (0 or 1)
        :param cmd: full command line
        :return:
        """
        # Fill values in dict as we can
        last_X = self.position['X']
        last_Y = self.position['Y']
        last_Z = self.position['Z']
        last_E = self.position['E']

        values_in_cmd = {'X': None, 'Y': None, 'Z': None, 'E': None, 'F': None}
        for axis in values_in_cmd:
            try:
                value = float(self.get_tag(axis, cmd))
            except:
                pass
            else:
                values_in_cmd[axis] = value

        for axis in ['X', 'Y', 'Z']:
            if values_in_cmd[axis] is not None:
                if self.absolutes[0]:
                    self.position[axis] = values_in_cmd[axis]
                else:
                    self.position[axis] += values_in_cmd[axis]

        axis = 'E'
        if values_in_cmd[axis] is not None:
            if self.absolutes[1]:
                self.position[axis] = values_in_cmd[axis]
            else:
                self.position[axis] += values_in_cmd[axis]

        axis = 'F'
        if values_in_cmd[axis] is not None:
            self.position[axis + tag] = values_in_cmd[axis]

        X = last_X - self.position['X']
        Y = last_Y - self.position['Y']
        Z = last_Z - self.position['Z']
        E = last_E - self.position['E'] * float(self.flowrate_multiplier) / 100.
        F = self.position['F' + tag] * float(self.feedrate_multiplier) / 100.
        self.mechanics.move_to(X, Y, Z, E, F)

        self.new_position = True

    def search(self, filename, position=dict(), threshold=dict(Z=1., XY=None), n=1):
        """
        Search in file for a given xyz position within a certain threshold
        :param filename: file path
        :param position: dictionary with X, Y and Z position
        :param threshold: dictionary with threshold in Z axis and XY plane
        :param n: number of points to return
        :return: dictionary with file position and machine settings on closest point (including position)
        """
        f = open(filename, 'r')

        continue_info = [self.machine_start_settings.copy() for i in range(n)]

        try:
            file_pos = f.tell()
            for line in f:
                self.process(line)
                if abs(self.position['Z']-position['Z']) < threshold['Z']:
                    if self.new_position:
                        new_dist = .0
                        for axis in ['X', 'Y', 'Z']:
                            new_dist += (self.position[axis]-position[axis])**2
                        new_dist = sqrt(new_dist)
                        if new_dist < continue_info[0]['dist'] and (True if threshold['XY'] is None else new_dist < threshold['XY']):
                            continue_info[0]['dist'] = new_dist
                            continue_info[0]['file_pos'] = file_pos
                            continue_info[0]['machine']['tool'] = self.current_tool
                            continue_info[0]['machine']['target_temps'] = self.target_temps
                            for axis in self.position:
                                continue_info[0]['machine'][axis] = self.position[axis]
                            max_dist = continue_info[0]['dist']
                            saved_i = 0
                            for i in range(1, len(continue_info)):
                                if max_dist < continue_info[i]['dist']:
                                    saved_i = i
                                    max_dist = continue_info[i]['dist']
                            aux = continue_info[0]['dist']
                            continue_info[0]['dist'] = continue_info[saved_i]['dist']
                            continue_info[saved_i]['dist'] = aux
                elif self.position['Z'] > position['Z'] + 10 * threshold['Z']:
                    break

                file_pos = f.tell()

        finally:
            f.close()
        return continue_info

    def small_moves_check(self, filename, threshold=0.1, E_threshold=0, z_min=0.0, z_max=float('inf')):

        last_position = {'X': .0, 'Y': .0, 'Z': .0, 'E': .0}
        for axis in ['X', 'Y', 'Z', 'E']:
            last_position[axis] = self.position[axis]
        last_line = '\n'
        with open(filename) as f:
            counter = 0
            smallest = ('', '', float('inf'), float('inf'), 0.0)
            for line in f:
                self.process(line)
                if self.new_position and z_min <= self.position['Z'] <= z_max:
                    dist = 0.0
                    for axis in ['X', 'Y', 'Z', 'E']:
                        dist += (last_position[axis] - self.position[axis]) ** 2
                    dist = sqrt(dist)
                    E_dist = abs(last_position['E'] - self.position['E'])
                    if 0 < dist <= threshold:
                        if dist < smallest[2]:
                            smallest = (line, last_line, dist, E_dist, self.position['Z'])
                        print("\n{}{}D:{} E:{} @ Z:{}".format(line, last_line, dist, E_dist, self.position['Z']))
                        counter += 1
                    for axis in ['X', 'Y', 'Z', 'E']:
                        last_position[axis] = self.position[axis]
                    last_line = line
            print("\n{} lines < {}mm\n".format(counter, threshold))
            print("\nSmallest:\n{}{}D:{} E:{} @ Z:{}".format(*smallest))

    def get_print_time(self, filename):
        self.start_print()
        with open(filename) as f:
            for line in f:
                self.process(line)
        self.end_print()
        return self.mechanics.print_time


class ConstAccBlock:

    def __init__(self, direction, distance, max_entry_speed, nominal_speed, max_jump_speed, acceleration):
        self.dt = 0.02

        self.t = 0.0

        self.ts = ()
        self.a0 = ()
        self.a1 = ()
        self.a2 = ()

        self.lock = False

        self.distance = distance
        self.direction = direction

        self.max_entry_speed = max_entry_speed
        self.nominal_speed = nominal_speed
        self.max_exit_speed = max_jump_speed
        self.max_jump_speed = max_jump_speed
        self.max_acceleration = acceleration

        self.entry_speed = self.max_entry_speed
        self.exit_speed = self.max_jump_speed
        self.acceleration = self.max_acceleration

        self.entry_speed, self.exit_speed = self.calc_trapezoid()

    @property
    def move_time(self):
        if isinstance(self.ts, float):
            self.ts = (self.ts,)
            return self.ts[-1]
        else:
            return self.ts[-1]

    @property
    def trajectory_on_next_t(self):
        self.t += self.dt

        for idx, final_t in enumerate(self.ts):
            if self.t < final_t:
                if idx > 0:
                    t = self.t - self.ts[idx - 1]
                else:
                    t = self.t
                position_on_t = self.a0[idx] + self.a1[idx] * t + (self.a2[idx] * t ** 2) / 2. + \
                    (self.a3[idx] * t ** 3) / 6.
                speed_on_t = self.a1[idx] + self.a2[idx] * t + (self.a3[idx] * t ** 2) / 2.

                return position_on_t, speed_on_t

        return None

    def calc_trapezoid(self, entry_speed=None, exit_speed=None, pass_dir=-1):
        if entry_speed is None:
            if pass_dir == -1:
                entry_speed = self.max_entry_speed
            else:
                entry_speed = self.entry_speed
        if exit_speed is None:
            if pass_dir == 1:
                exit_speed = self.max_exit_speed
            else:
                exit_speed = self.exit_speed

        if entry_speed > self.nominal_speed:
            entry_speed = self.nominal_speed
        if exit_speed > self.nominal_speed:
            exit_speed = self.nominal_speed

        cruising_speed = self.nominal_speed

        acc_time = (cruising_speed - entry_speed) / self.acceleration
        dec_time = (cruising_speed - exit_speed) / self.acceleration

        acc_dist = entry_speed * acc_time + self.acceleration * (acc_time ** 2) / 2.
        dec_dist = exit_speed * dec_time + self.acceleration * (dec_time ** 2) / 2.

        if entry_speed == self.nominal_speed and exit_speed == self.nominal_speed and cruising_speed > 0.0:  # all at cruise speed
            self.ts = (self.distance / cruising_speed,)
            self.a0 = (0.0,)
            self.a1 = (entry_speed,)
            self.a2 = (0.0,)

        elif entry_speed == self.nominal_speed and self.distance >= dec_dist and cruising_speed > 0.0:  # starts at max speed
            cruising_dist = self.distance - dec_dist
            cruising_time = cruising_dist / cruising_speed
            self.ts = (cruising_time, cruising_time + dec_time)
            self.a0 = (0.0, cruising_dist)
            self.a1 = (entry_speed, cruising_speed)
            self.a2 = (0.0, -self.acceleration)

        elif exit_speed == self.nominal_speed and self.distance >= dec_dist and cruising_speed > 0.0:  # finishes at max speed
            cruising_dist = self.distance - dec_dist
            cruising_time = cruising_dist / cruising_speed
            self.ts = (acc_time, acc_time + cruising_time)
            self.a0 = (0.0, acc_dist)
            self.a1 = (entry_speed, cruising_speed)
            self.a2 = (self.acceleration, 0.0)

        elif (acc_dist + dec_dist) <= self.distance and cruising_speed > 0.0:  # feasible
            cruise_time = (self.distance - (acc_dist + dec_dist)) / cruising_speed
            self.ts = (acc_time, acc_time + cruise_time, acc_time + cruise_time + dec_time)
            self.a0 = (0.0, acc_dist, self.distance - dec_dist)
            self.a1 = (entry_speed, cruising_speed, cruising_speed)
            self.a2 = (self.acceleration, 0.0, -self.acceleration)

        else:
            # calc new target_speed
            aux1 = self.distance * self.acceleration + (entry_speed ** 2 + exit_speed ** 2) / 2.
            cruising_speed = sqrt(aux1)
            if cruising_speed >= entry_speed and cruising_speed >= exit_speed:  # feasible
                acc_time = (cruising_speed - entry_speed) / self.acceleration
                dec_time = (cruising_speed - exit_speed) / self.acceleration

                acc_dist = entry_speed * acc_time + self.acceleration * (acc_time ** 2) / 2.

                self.ts = (acc_time, acc_time + dec_time)
                self.a0 = (0.0, acc_dist)
                self.a1 = (entry_speed, cruising_speed)
                self.a2 = (self.acceleration, -self.acceleration)

            else:  # Need to reduce one
                if pass_dir < 0:  # adjust entry_speed
                    entry_speed = sqrt(exit_speed ** 2. + 2. * self.distance * self.acceleration)

                else:  # adjust exit_speed
                    exit_speed = sqrt(entry_speed ** 2. + 2. * self.distance * self.acceleration)

                time = abs(entry_speed - exit_speed) / self.acceleration
                self.ts = (time,)
                self.a0 = (0.0,)
                self.a1 = (entry_speed,)

                if entry_speed < exit_speed:
                    self.a2 = (self.acceleration,)
                else:
                    self.a2 = (-self.acceleration,)

        self.entry_speed = entry_speed
        self.exit_speed = exit_speed
        return entry_speed, exit_speed


class Queue:
    def __init__(self, queue_size):
        self.blocks = []
        self.queue_size = queue_size

    def __len__(self):
        return len(self.blocks)

    def __getitem__(self, item):
        return self.blocks[item]

    def __iter__(self):
        return self.blocks.__iter__()

    @property
    def is_empty(self):
        return len(self.blocks) == 0

    @property
    def is_full(self):
        return len(self.blocks) == self.queue_size

    @property
    def first_block(self):
        if len(self.blocks) == 0:
            return None
        return self.blocks[0]

    @property
    def last_block(self):
        if len(self.blocks) == 0:
            return None
        return self.blocks[-1]

    def append_block(self, block):
        if len(self.blocks) < self.queue_size:
            self.blocks.append(block)
            return True
        return False

    def pop_block(self):
        if len(self.blocks) == 0:
            return None
        return self.blocks.pop(0)


class MechanicalPrinter:

    def __init__(self, printer_type):
        self.accelerations = dict(X=400., Y=400., Z=10., E=500.)
        self.max_jump_speed = dict(X=12., Y=8., Z=0.1, E=10.)
        self.max_speed = dict(X=1666.66, Y=583.33, Z=5., E=50.)
        if printer_type == "STUDIO":
            self.accelerations = dict(X=600., Y=600., Z=2.5, E=500.)
            self.max_jump_speed = dict(X=6., Y=6., Z=0.1, E=10.)
            self.max_speed = dict(X=300., Y=300., Z=5., E=50.)
        elif printer_type == "PRO":
            self.accelerations = dict(X=2000., Y=2000., Z=1200, E=500.)
            self.max_jump_speed = dict(X=6., Y=6., Z=0.1, E=10.)
            self.max_speed = dict(X=36000., Y=36000., Z=100., E=50.)

        self.print_time = 0.0
        self.acc_time = dict(X=0., Y=0., Z=0., E=0.)
        self.dec_time = dict(X=0., Y=0., Z=0., E=0.)
        self.cruise_time = dict(X=0., Y=0., Z=0., E=0.)

        self.queue = Queue(16)

        self.last_nominal_speed = 0.0
        self.last_direction = dict(X=0., Y=0., Z=0., E=0.)

        self.axes = dict(X=0, Y=1, Z=2, E=3)

    @staticmethod
    def reset_position():
        return dict(X=0., Y=0., Z=0., E=0., F=1200.)

    def start_print(self):
        self.print_time = 0.0
        self.acc_time = dict(X=0., Y=0., Z=0., E=0.)
        self.dec_time = dict(X=0., Y=0., Z=0., E=0.)
        self.cruise_time = dict(X=0., Y=0., Z=0., E=0.)

    def wait_empty_queue(self):
        while not self.queue.is_empty:
            self.print_time += self.queue.first_block.move_time
            direction = self.queue.first_block.direction
            last_dt = 0.0
            for i, ts in enumerate(self.queue.first_block.ts):
                ac = self.queue.first_block.a2[i]
                for axis in direction:
                    if direction[axis] == 0:
                        continue
                    if ac > 0.:
                        self.acc_time[axis] += ts - last_dt
                    elif ac < 0.:
                        self.dec_time[axis] += ts - last_dt
                    else:
                        self.cruise_time[axis] += ts - last_dt
                last_dt = ts

            self.queue.pop_block()

    def move_to(self, X, Y, Z, E, F):
        to_move = dict(X=X, Y=Y, Z=Z, E=E)

        nominal_speed = F / 60.

        if self.queue.is_full:
            self.print_time += self.queue.first_block.move_time
            direction = self.queue.first_block.direction
            last_dt = 0.0
            for i, ts in enumerate(self.queue.first_block.ts):
                ac = self.queue.first_block.a2[i]
                for axis in direction:
                    if direction[axis] == 0:
                        continue
                    if ac > 0.:
                        self.acc_time[axis] += ts - last_dt
                    elif ac < 0.:
                        self.dec_time[axis] += ts - last_dt
                    else:
                        self.cruise_time[axis] += ts - last_dt
                last_dt = ts

            self.queue.pop_block()

        prep = self.prepare_move(to_move)
        if prep is None:
            return

        distance, direction = prep

        max_jump_speed = nominal_speed
        max_acceleration = 10000000.
        for axis in direction.keys():
            if abs(direction[axis] * nominal_speed) > self.max_speed[axis]:
                nominal_speed = self.max_speed[axis] / abs(direction[axis])

            if abs(direction[axis] * max_acceleration) > self.accelerations[axis]:
                max_acceleration = self.accelerations[axis] / abs(direction[axis])

            if abs(direction[axis] * max_jump_speed) > self.max_jump_speed[axis]:
                max_jump_speed = self.max_jump_speed[axis] / abs(direction[axis])

        if self.queue.is_empty:
            max_entry_speed = max_jump_speed
        else:
            if nominal_speed > self.last_nominal_speed:
                max_entry_speed, last_max_exit_speed = self.adjust_junction_speed(
                    self.last_direction, self.last_nominal_speed, direction, nominal_speed)
            else:
                last_max_exit_speed, max_entry_speed = self.adjust_junction_speed(
                    direction, nominal_speed, self.last_direction, self.last_nominal_speed)
            self.queue.last_block.max_exit_speed = last_max_exit_speed

        new_block = ConstAccBlock(direction, distance, max_entry_speed, nominal_speed, max_jump_speed, max_acceleration)
        self.queue.append_block(new_block)

        # recalculate queue
        self.recalculate_queue()

        self.last_direction = direction
        self.last_nominal_speed = nominal_speed

    def adjust_junction_speed(self, dir1, speed1, dir2, speed2):
        """
        try to lock speed1
        :param dir1:
        :param speed1:
        :param dir2:
        :param speed2:
        :return:
        """
        for axis in dir1:
            axis_speed1 = dir1[axis] * speed1
            axis_speed2 = dir2[axis] * speed2
            diff_speed = abs(axis_speed1 - axis_speed2)

            if diff_speed > self.max_jump_speed[axis]:
                aux = self.max_jump_speed[axis] / diff_speed
                speed1 *= aux
                speed2 *= aux
        return speed1, speed2

    def recalculate_queue(self):

        entry_speed = self.queue.last_block.entry_speed
        direction = self.queue.last_block.direction
        for i in range(len(self.queue)-2, 0, -1):
            exit_speed, entry_speed = self.adjust_junction_speed(
                direction, entry_speed, self.queue[i].direction, self.queue[i].exit_speed)
            entry_speed, exit_speed = self.queue[i].calc_trapezoid(exit_speed=entry_speed, pass_dir=-1)
            direction = self.queue[i].direction

        exit_speed = self.queue.first_block.exit_speed
        direction = self.queue.first_block.direction

        for i in range(1, len(self.queue)):
            entry_speed, exit_speed = self.adjust_junction_speed(
                direction, exit_speed, self.queue[i].direction, self.queue[i].entry_speed)
            entry_speed, exit_speed = self.queue[i].calc_trapezoid(entry_speed=exit_speed, pass_dir=1)
            direction = self.queue[i].direction

    @staticmethod
    def prepare_move(axis_movement):
        distance = axis_movement['X'] ** 2 + axis_movement['Y'] ** 2 + axis_movement['Z'] ** 2

        if distance == 0.0:
            distance = abs(axis_movement['E'])
        else:
            distance = sqrt(distance)

        if distance == 0.0:
            return None

        direction = dict()
        for axis in ['X', 'Y', 'Z', 'E']:
            direction[axis] = axis_movement[axis] / distance

        return distance, direction

# Convert seconds to 'D days, HH:MM:SS.FFF'


def sec2time(sec, n_msec=3):
    if hasattr(sec, '__len__'):
        return [sec2time(s) for s in sec]
    m, s = divmod(sec, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)
    if n_msec > 0:
        pattern = '%%02d:%%02d:%%0%d.%df' % (n_msec+3, n_msec)
    else:
        pattern = r'%02d:%02d:%02d'
    if d == 0:
        return pattern % (h, m, s)
    return ('%d days, ' + pattern) % (d, h, m, s)
