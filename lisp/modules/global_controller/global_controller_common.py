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
from lisp.core.message_dict import MessageDict


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
        self.__protocol_flag = ControllerProtocol.NONE
        self.__arg_types = arg_types

    @property
    def flag(self):
        return self.__protocol_flag

    def execute(self, *args):
        num_args = len(self.__arg_types)
        if num_args <= len(args):
            self.__signal.emit(*args[:num_args])
        else:
            elogging.debug("global_controller_common.Controller: not enough arguments")

    def add_callback(self, protocol, func):
        if isinstance(protocol, ControllerProtocol):
            # TODO: check number of arguments against number of arguments protocol supports
            self.__protocol_flag = protocol
            if self.__protocol_flag is not ControllerProtocol.NONE:
                self.__signal.connect(func)
            else:
                raise elogging.error("GlobalController: Controller controller allready connected")

    @property
    def params(self):
        return self.__arg_types


# TODO: rename to SessionAction, to distinct them from CueActions
class GlobalAction(Enum):
    GO = Controller()
    PAUSE_ALL = Controller()  # ListLayout
    RESUME_ALL = Controller()  # ListLayout
    STOP_ALL = Controller()  # ListLayout
    INTERRUPT_ALL = Controller()  # ListLayout
    SELECT_NEXT = Controller()  # ListLayout
    SELECT_PREV = Controller()  # ListLayout
    RESET = Controller()  # ListLayout
    PAUSE_SELECTED = Controller()  # ListLayout
    RESUME_SELECTED = Controller()  # ListLayout
    STOP_SELECTED = Controller()  # ListLayout
    INTERRUPT_SELECTED = Controller()  # ListLayout
    GO_NUM = Controller(int)  # ListLayout
    PAUSE_NUM = Controller(int)  # ListLayout
    RESUME_NUM = Controller(int)  # ListLayout
    STOP_NUM = Controller(int)  # ListLayout
    INTERRUPT_NUM = Controller(int)  # ListLayout
    SELECT_NUM = Controller(int)  # ListLayout
    PAGE = Controller(int)  # CartLayout
    # VOLUME = Controller(float)

    def get_controller(self):
        return self.value

    def __str__(self):
        return self.name.lower()


class CommonController(metaclass=ABCSingleton):
    """module provides global controls through protocol plugins"""

    def __init__(self):
        # self.__keys__ = {}
        self.__masks__ = MessageDict()
        self.__protocols = {}

        self.controller_event = Signal()  # key, list(wildcard keys)
        # self.notify_key_changed = Signal()  # ControllerProtocol, str, str
        self.notify_new_session = Signal()
        self.notify_del_session = Signal()

        # self.notify_key_changed.connect(self.change_key_str)
        self.notify_new_session.connect(self.__new_session)
        self.notify_del_session.connect(self.__del_session)

        protocols.load()

        for protocol_class in protocols.Protocols:
            protocol = protocol_class()
            p_name = protocol_class.__name__.upper()
            if hasattr(ControllerProtocol, p_name):
                self.__protocols[ControllerProtocol[p_name]] = protocol
            protocol.protocol_event.connect(self.perform_action)

        self.__load_settings()

    @property
    def protocols(self):
        return self.__protocols.values()

    @property
    def protocol_types(self):
        return self.__protocols.keys()

    # @property
    # def keys(self):
    #     return self.__masks__.keys()

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

    def change_key(self, action, protocol_type, new_msg_str, old_msg_str):
        protocol = self.get_protocol(protocol_type)
        msg_id = protocol.parse_id(old_msg_str)
        mask = protocol.parse_mask(old_msg_str)

        # TODO: remove recursive to clean up mask dict
        self.__masks__.remove(msg_id, mask)
        self.__set_key(action, protocol, new_msg_str)

    def __set_key(self, action, protocol, message_str):
        if isinstance(action, GlobalAction):
            key = protocol.parse_id(message_str)
            mask = protocol.parse_mask(message_str)
            if not self.__masks__.add(key, action.get_controller(), mask):
                elogging.debug("CommonController: could not add key/mask: {} {}".format(key, mask))
            protocol.register_message_event.emit(message_str)

    def __load_settings(self):
        self.__masks__.clear()

        if ControllerProtocol.MIDI in self.__protocols:
            if 'MidiInput' in config:
                for action in GlobalAction:
                    protocol = self.get_protocol(ControllerProtocol.MIDI)

                    msg_str = config['MidiInput'].get(str(action), '')
                    if msg_str:
                        self.__set_key(action, protocol, msg_str)
            else:
                elogging.error("CommonController: no Midi Input settings found in application settings")

        if ControllerProtocol.KEYBOARD in self.__protocols:
            if 'ListLayout' in config and config['ListLayout'].get('gokey', ''):
                protocol = self.get_protocol(ControllerProtocol.KEYBOARD)
                # we bypass all action, using only gokey from ListLayout
                msg_str = config['ListLayout'].get('gokey', '')
                if msg_str:
                    self.__set_key(GlobalAction.GO, protocol, msg_str)

        if ControllerProtocol.OSC in self.__protocols:
            if 'MidiInput' in config:
                protocol = self.get_protocol(ControllerProtocol.OSC)
                for action in GlobalAction:
                    msg_str = config['OscInput'].get(str(action), '')
                    if msg_str:
                        self.__set_key(action, protocol, msg_str)

    def terminate(self):
        pass

    @staticmethod
    def set_controller(action, protocols, func):
        controller = action.get_controller()
        controller.add_callback(protocols, func)

    def perform_action(self, protocol_name, key, *args):
        protocol_type = self.query_protocol(protocol_name)

        contr, mask = self.__masks__.item(key, args)
        if contr and contr.flag & protocol_type:
            args = self.__masks__.filter(mask, *args)
            contr.execute(*args)

        # forward key to other listeners (e.g. controller plugins)
        # self.controller_event.emit(key, tagged_keys)

        # for tag in tagged_keys:
        #     if tag not in self.__keys__:
        #         tagged_keys.remove(tag)
        #
        # if tagged_keys:
        #     for wildcard in tagged_keys:
        #         self.__keys__[wildcard][1].execute(protocol_type, *args)
        # else:
        #     # TODO: check this again when implementing OSC
        #     # if wildcard is send, we drop the fully message if it appears
        #     if key in self.__keys__.keys():
        #         self.__keys__[key][1].execute(protocol_type, *args)

