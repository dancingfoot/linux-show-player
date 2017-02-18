# -*- coding: utf-8 -*-
#
# This file is part of Linux Show Player
#
# Copyright 2012-2016 Francesco Ceruti <ceppofrancy@gmail.com>
#
# Linux Show Player is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Linux Show Player is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Linux Show Player.  If not, see <http://www.gnu.org/licenses/>.


from lisp.core.singleton import ABCSingleton
from enum import Enum, Flag, auto
from lisp.core.signal import Signal
from lisp.core.configuration import config
from lisp.ui import elogging
from lisp.modules.global_controller import protocols


class ControllerProtocol(Flag):
    NONE = auto()
    KEYBOARD = auto()
    MIDI = auto()
    OSC = auto()
    ALL = KEYBOARD | MIDI | OSC


class Controller:
    def __init__(self, *arg_types):
        super().__init__()
        self.__signal = Signal()
        self.__protocols = ControllerProtocol.NONE
        self.__arg_types = arg_types

    def execute(self, protocol, *args):
        if self.__protocols & protocol:
            # TODO: better Error handling
            if len(args) < len(self.__arg_types):
                # TODO: for number of arguments when adding callback, to avoid this error
                raise RuntimeError("global_controller_common.Controller: wrong args number")
            self.__signal.emit(*(self.__arg_types[i](args[i]) for i in range(len(self.__arg_types))))

    def add_callback(self, protocol, func):
        if isinstance(protocol, ControllerProtocol):
            # TODO: check number of arguments against number of arguments protocol supports
            self.__protocols = protocol
            if self.__protocols is not ControllerProtocol.NONE:
                self.__signal.connect(func)
            else:
                raise elogging.error("GlobalController: Controller controller allready connected")

    @property
    def params(self):
        return self.__arg_types


class GlobalAction(Enum):
    GO = Controller()
    PAUSE_ALL = Controller()
    RESUME_ALL = Controller()
    STOP_ALL = Controller()
    INTERRUPT_ALL = Controller()
    SELECT_NEXT = Controller()
    SELECT_PREV = Controller()
    RESET = Controller()
    PAUSE_CURRENT = Controller()
    RESUME_CURRENT = Controller()
    STOP_CURRENT = Controller()
    INTERRUPT_CURRENT = Controller()
    START_NUM = Controller(int)
    PAUSE_NUM = Controller(int)
    RESUME_NUM = Controller(int)
    STOP_NUM = Controller(int)
    INTERRUPT_NUM = Controller(int)
    SELECT_NUM = Controller(int)
    # VOLUME = Controller(float)

    def get_controller(self):
        return self.value


class CommonController(metaclass=ABCSingleton):
    """module provides global controls through protocol plugins"""

    def __init__(self):
        self.__keys__ = {}
        self.__protocols = {}

        self.controller_event = Signal()  # key, list(wildcard keys)
        self.notify_key_changed = Signal()  # GlobalAction, ControllerProtocol, str
        self.notify_new_session = Signal()
        self.notify_del_session = Signal()

        self.notify_key_changed.connect(self.change_key_str)
        self.notify_new_session.connect(self.__new_session)
        self.notify_del_session.connect(self.__del_session)

        protocols.load()

        for protocol_class in protocols.Protocols:
            protocol = protocol_class()
            p_name = protocol_class.__name__.upper()
            if hasattr(ControllerProtocol, p_name):
                self.__protocols[ControllerProtocol[p_name]] = protocol
            protocol.protocol_event.connect(self.perform_action)

        self.get_settings()

    @property
    def protocols(self):
        return self.__protocols.values()

    @property
    def protocol_types(self):
        return self.__protocols.keys()

    def __new_session(self):
        for protocol in self.protocols:
            protocol.init()

    def __del_session(self):
        for protocol in self.protocols:
            protocol.reset()

    def query_protocol(self, p_str):
        if p_str.upper() in ControllerProtocol.__members__.keys() \
                and ControllerProtocol[p_str.upper()] in self.__protocols:
            return ControllerProtocol[p_str.upper()]
        else:
            return None

    def get_protocol(self, p_type):
        return self.__protocols[p_type] if p_type in self.__protocols else None

    def change_key_str(self, action, protocol, new_key):
        # TODO: get rid of this reverse dict search
        keys = [key for key, val in self.__keys__.items() if
                val[1] == action.get_controller() and val[0] is protocol]
        for old_key in keys:
            self.__keys__[new_key] = self.__keys__.pop(old_key)

    def get_settings(self):
        self.__keys__.clear()

        if ControllerProtocol.MIDI in self.__protocols:
            channel = config['MidiInput'].get('channel', 0)

            for action in GlobalAction:
                # TODO: use protocol methods
                protocol = self.get_protocol(ControllerProtocol.MIDI)
                values = protocol.values_from_key(config['MidiInput'].get(action.name.lower(), ''))
                key_str = protocol.key_from_values(values[0], channel, *values[1:])
                if key_str:
                    self.set_key(action, ControllerProtocol.MIDI, key_str)

        if ControllerProtocol.KEYBOARD in self.__protocols:
            # we bypass all action, using only gokey from ListLayout
            key = config['ListLayout'].get('gokey', '')
            if key:
                self.set_key(GlobalAction.GO, ControllerProtocol.KEYBOARD, key)

        if ControllerProtocol.OSC in self.__protocols:
            # TODO add OSC
            pass

    def terminate(self):
        pass

    @staticmethod
    def set_controller(action, protocols, func):
        controller = action.get_controller()
        controller.add_callback(protocols, func)

    def set_key(self, action, protocol, key):
        if isinstance(action, GlobalAction) and isinstance(protocol, ControllerProtocol):
            self.__keys__[key] = (protocol, action.get_controller())

    def perform_action(self, key, protocol_name, *args):
        protocol_type = self.query_protocol(protocol_name)
        protocol = self.get_protocol(protocol_type)
        wildcards = protocol.wildcard_keys(key)

        for wildcard in wildcards:
            if wildcard not in self.__keys__:
                wildcards.remove(wildcard)

        if wildcards:
            for wildcard in wildcards:
                self.__keys__[wildcard][1].execute(protocol_type, *args)
        else:
            if key in self.__keys__.keys():
                self.__keys__[key][1].execute(protocol_type, *args)

        # forward key to other listeners (e.g. controller plugins)
        self.controller_event.emit(key, wildcards)
