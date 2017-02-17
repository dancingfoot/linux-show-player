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

    def execute(self, *args, **kwargs):
        protocol = kwargs.pop('protocol')
        if self.__protocols & ControllerProtocol[protocol.upper()]:
            self.__signal.emit(*args, **kwargs)

    def add_callback(self, protocol, func):
        if isinstance(protocol, ControllerProtocol):
            self.__protocols = protocol
            if self.__protocols is not ControllerProtocol.NONE:
                self.__signal.connect(func)
            else:
                raise elogging.error("GlobalController: Controller controller allready connected")

    @property
    def arg_types(self):
        return self.__arg_types


class GlobalAction(Enum):
    GO = Controller()
    STOP_ALL = Controller()
    PAUSE_ALL = Controller()
    INTERRUPT_ALL = Controller()
    SELECT_NEXT = Controller()
    SELECT_PREV = Controller()
    RESET = Controller()
    GO_CURRENT = Controller(int)
    PAUSE_CURRENT = Controller(int)
    STOP_CURRENT = Controller(int)
    INTERRUPT_CURRENT = Controller(int)
    # VOLUME = Controller(float)

    def get_controller(self):
        return self.value


class CommonController(metaclass=ABCSingleton):
    """module provides global controls through protocol plugins"""
    def __init__(self):
        self.__keys__ = {}
        self.__protocols = {}

        self.controller_event = Signal()
        self.notify_key = Signal()
        self.controller_event.connect(self.perform_action)
        self.notify_key.connect(self.notify_key_changed)

    def populate_protcols(self, protocols):
        for protocol in protocols:
            p_name = protocol.__name__.upper()
            if hasattr(ControllerProtocol, p_name):
                self.__protocols[ControllerProtocol[p_name]] = protocol

        self.get_settings()

    def query_protocol(self, p_str):
        if p_str.upper() in ControllerProtocol.__members__.keys() and ControllerProtocol[p_str.upper()] in self.__protocols:
            return ControllerProtocol[p_str.upper()]
        else:
            return None

    def get_protocol(self, p_type):
        return self.__protocols[p_type] if p_type in self.__protocols else None

    def notify_key_changed(self, action, protocol, new_key):
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
                key = tuple(config['MidiInput'].get(action.name.lower(), '').replace(' ', '').split(','))
                key_str = self.get_protocol(ControllerProtocol.MIDI).key_from_values(key[0], channel, *key[:1])
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

    def perform_action(self, key, *args, **kwargs):
        if key in self.__keys__:
            self.__keys__[key][1].execute(*args, **kwargs)
