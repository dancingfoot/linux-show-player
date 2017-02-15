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


class GlobalProtocol(Flag):
    NONE = auto()
    KEYBOARD = auto()
    MIDI = auto()
    OSC = auto()
    ALL = KEYBOARD | MIDI | OSC


class Controller:
    def __init__(self, *arg_types):
        super().__init__()
        self.__signal = Signal()
        self.__protocols = GlobalProtocol.NONE
        self.__arg_types = arg_types

    def execute(self, *args, **kwargs):
        protocol = kwargs.pop('protocol')
        if self.__protocols & GlobalProtocol[protocol.upper()]:
            self.__signal.emit(*args, **kwargs)

    def add_callback(self, protocol, func):
        if isinstance(protocol, GlobalProtocol):
            self.__protocols = protocol
            self.__signal.connect(func)


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
    VOLUME = Controller(float)

    def get_controller(self):
        return self.value


class CommonController(metaclass=ABCSingleton):
    """module provides global controls through protocol plugins"""
    def __init__(self):
        self.__keys__ = {}
        self.__protocols = set()

        self.controller_event = Signal()
        self.notify_key = Signal()
        self.controller_event.connect(self.perform_action)
        self.notify_key.connect(self.notify_key_changed)

    @staticmethod
    def create_midi_key_from_settings(action_str, channel):
        key_str = tuple(config['MidiInput'].get(action_str, '').replace(' ', '').split(','))
        if len(key_str) > 1:
            return '{} {} {}'.format(key_str[0], int(channel), int(key_str[1]))
        else:
            return ''

    @staticmethod
    def create_keyboard_key_from_settings(action_str):
        if action_str is 'go':
            return config['ListLayout'].get('gokey', '')
        else:
            return ''

    @staticmethod
    def create_osc_key_from_settings(action_str, path):
        return ''

    def populate_protcols(self, protocols):
        protocols = [p.__name__.upper() for p in protocols]

        for i in GlobalProtocol:
            if i.name in protocols:
                self.__protocols.add(GlobalProtocol[i.name])

        self.get_settings()

    def notify_key_changed(self, action, protocol, new_key):
        keys = {key: val for key, val in self.__keys__.items() if val[1] == action.get_controller() and val[0] is protocol}
        for old_key in keys:
            self.__keys__[new_key] = self.__keys__.pop(old_key)

    def get_settings(self):
        print("CommonController get_settings")
        self.__keys__.clear()

        if GlobalProtocol.MIDI in self.__protocols:
            channel = config['MidiInput'].get('channel', 0)

            for action in GlobalAction:
                key = self.create_midi_key_from_settings(action.name.lower(), channel)
                if key:
                    self.set_key(action, GlobalProtocol.MIDI, key)

        if GlobalProtocol.KEYBOARD in self.__protocols:
            # we bypass all action, using only gokey from ListLayout
            key = self.create_keyboard_key_from_settings('go')
            if key:
                self.set_key(GlobalAction.GO, GlobalProtocol.KEYBOARD, key)

        if GlobalProtocol.OSC in self.__protocols:
            # TODO add OSC
            pass

    def terminate(self):
        pass

    @staticmethod
    def set_controller(action, protocols, func):
        controller = action.get_controller()
        controller.add_callback(protocols, func)

    def set_key(self, action, protocol, key):
        if isinstance(action, GlobalAction) and isinstance(protocol, GlobalProtocol):
            self.__keys__[key] = (protocol, action.get_controller())

    def perform_action(self, key, *args, **kwargs):
        if key in self.__keys__:
            self.__keys__[key][1].execute(*args, **kwargs)

