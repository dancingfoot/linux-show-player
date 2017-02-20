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

from lisp.core.signal import Signal
from abc import abstractmethod, ABCMeta


class Protocol(metaclass=ABCMeta):
    """Base interface for protocols.

    The init() and reset() functions are called when the respective functions
    of the main-plugin are called.

    When an event that can trigger a cue is "detected", the protocol_event
    signal should be emitted with the event representation.

    To be loaded correctly the class should follow the ClassesLoader
    specification.
    To define the settings, only define a class with same name plus 'Settings'
    as suffix (e.g. Protocol -> ProtocolSettings), in the same file.
    """

    def __init__(self):
        self.protocol_event = Signal()  # message -> str, protocol -> str

    def init(self):
        pass

    def reset(self):
        pass

    @staticmethod
    @abstractmethod
    # TODO: change arguments to *args (osc)
    def key_from_message(message):
        """
        creates a unique key string from the given message
        :param message: message received by a protocol plugin
        :type message:
        """

    @staticmethod
    @abstractmethod
    def key_from_values(*args):
        """
        creates a unique key string from arguments
        :param args: arguments of protocol plugin messsage
        :type args: arguments
        """

    @staticmethod
    @abstractmethod
    def values_from_key(key):
        """
        unpacks values from a message key string
        :param key: unique message key string
        :type key: str
        """

    @staticmethod
    @abstractmethod
    def wildcard_keys(key):
        """
        creates possible wildcard keys of this key
        wildcard: any = -1
        :param key: key
        :type key: str
        """
