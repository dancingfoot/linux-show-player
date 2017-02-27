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


class Protocol:
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
        self.protocol_event = Signal()

    def init(self):
        pass

    def reset(self):
        pass

    @staticmethod
    @abstractmethod
    def id_from_message(*args):
        """
        creates a message id from the given message
        :param message: message received by a protocol plugin
        :type message:
        """

    @staticmethod
    @abstractmethod
    def str_from_values(*args):
        """
        creates a unique message string from arguments
        :param args: arguments of protocol plugin messsage
        :type args: arguments
        """

    @staticmethod
    @abstractmethod
    def values_from_str(message_str):
        """
        unpacks values from a message string
        :param key: message key string
        :type key: str
        """

    @staticmethod
    @abstractmethod
    def parse_id(message_str):
        """
        unpacks message id from a message string
        :param message_str: key
        :type message_str: str
        """

    @staticmethod
    @abstractmethod
    def parse_mask(message_str):
        """
        unpacks message mask from a message string
        :param message_str: value mask
        :type message_str: tuple
        """