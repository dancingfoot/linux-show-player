# -*- coding: utf-8 -*-
#
# This file is part of Linux Show Player
#
# Copyright 2012-2016 Francesco Ceruti <ceppofrancy@gmail.com>
# Copyright 2012-2016 Thomas Achtner <info@offtools.de>
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

from collections import deque
from enum import Enum

from lisp.core.singleton import ABCSingleton
from liblo import ServerThread, Address, ServerError

from lisp.core.configuration import config
from lisp.layouts.list_layout.layout import ListLayout
from lisp.ui import elogging
from lisp.ui.mainwindow import MainWindow
from lisp.application import Application
from lisp.cues.cue import CueState
from lisp.core.signal import Signal


class OscMessageType(Enum):
    Int = 'Integer'
    Float = 'Float'
    Bool = 'Bool'
    String = 'String'


class OscCommon(metaclass=ABCSingleton):
    def __init__(self):
        self.__srv = None
        self.__listening = False
        self.__log = deque([], 10)
        self.__reg_counter = {}
        self.new_message = Signal()

    def start(self):
        if self.__listening:
            return

        try:
            self.__srv = ServerThread(int(config['OSC']['inport']))
            self.__srv.start()
            self.__srv.add_method(None, None, self.__new_message)
            self.__listening = True
            elogging.info('OSC: Server started ' + self.__srv.url, dialog=False)
        except ServerError as e:
            elogging.error(e, dialog=False)

    def stop(self):
        if self.__srv:
            if self.__listening:
                self.__srv.stop()
                self.__listening = False
            self.__srv.free()
            elogging.info('OSC: Server stopped', dialog=False)

    @property
    def listening(self):
        return self.__listening

    def send(self, path, *args):
        if self.__listening:
            target = Address(config['OSC']['hostname'], int(config['OSC']['outport']))
            self.__srv.send(target, path, *args)

    def __new_message(self, path, args, types):
        self.new_message.emit(path, args, types)