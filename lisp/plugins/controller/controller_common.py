# -*- coding: utf-8 -*-
#
# This file is part of Linux Show Player
#
# Copyright 2012-2016 Francesco Ceruti <ceppofrancy@gmail.com>
# Copyright 2016 Thomas Achtner <info@offtools.de>
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
from enum import Enum
from lisp.layouts.list_layout.layout import ListLayout
from lisp.layouts.cart_layout.layout import CartLayout
from lisp.core.signal import Signal


class SessionAction(Enum):
    GO = 'Go'
    PAUSE_ALL = 'Pause all'
    RESUME_ALL = 'Resume all'
    STOP_ALL = 'Stop all'
    INTERRUPT_ALL = 'Interrupt all'
    SELECT_NEXT = 'Select next'
    SELECT_PREV = 'Select previous'
    RESET = 'Reset'
    PAUSE_SELECTED = 'Pause selected'
    RESUME_SELECTED = 'Resume selected'
    STOP_SELECTED = 'Stop selected'
    INTERRUPT_SELECTED = 'Interrupt selected'
    GO_NUM = 'Go [Cue index]'
    PAUSE_NUM = 'Pause [Cue index]'
    RESUME_NUM = 'Resume [Cue index]'
    STOP_NUM = 'Stop [Cue index]'
    INTERRUPT_NUM = 'Interrupt [Cue index]'
    SELECT_NUM = 'Select [Cue index]'
    PAGE = 'Page [Page index]'


class SessionCallbacks:
    __CMD_LIST = {
        SessionAction.GO: ("go", ()),
        SessionAction.PAUSE_ALL: ("pause_all", ()),
        SessionAction.RESUME_ALL: ("restart_all", ()),
        SessionAction.STOP_ALL: ("stop_all", ()),
        SessionAction.INTERRUPT_ALL: ("interrupt_all", ()),
        SessionAction.SELECT_NEXT: ("select_next", ()),
        SessionAction.SELECT_PREV: ("select_prev", ()),
        SessionAction.RESET: ("reset", ()),
        SessionAction.PAUSE_SELECTED: ("pause_selected", ()),
        SessionAction.RESUME_SELECTED: ("resume_selected", ()),
        SessionAction.STOP_SELECTED: ("stop_selected", ()),
        SessionAction.INTERRUPT_SELECTED: ("interrupt_selected", ()),
        SessionAction.GO_NUM: ("go_num", (int,)),
        SessionAction.PAUSE_NUM: ("pause_at_index", (int,)),
        SessionAction.RESUME_NUM: ("restart_at_index", (int,)),
        SessionAction.STOP_NUM: ("stop_at_index", (int,)),
        SessionAction.INTERRUPT_NUM: ("interrupt_at_index", (int,)),
        SessionAction.SELECT_NUM: ("set_current_index", (int,))
    }

    __CMD_CART = {
        SessionAction.PAGE: ("setCurrentIndex", (int,))
    }

    @classmethod
    def get_list_layout(cls):
        return SessionCallbacks.__CMD_LIST

    @classmethod
    def get_cart_layout(cls):
        return SessionCallbacks.__CMD_CART

    @classmethod
    def parameter(cls, layout, action):
        if layout is ListLayout:
            if action in SessionCallbacks.__CMD_LIST:
                return SessionCallbacks.__CMD_LIST[action][1]
            else:
                raise TypeError("SessionCallbacks: Callback for SessionAction {0} not found".format(action))
        elif layout is CartLayout:
            if action in SessionCallbacks.__CMD_CART:
                return SessionCallbacks.__CMD_CART[action][1]

            else:
                raise TypeError("SessionCallbacks: Callback for SessionAction {0} not found".format(action))
        else:
            raise TypeError("SessionCallbacks: parameter need a Session Layout")


class ControllerCommon(metaclass=ABCSingleton):
    """
    little helper class can notifiy Controller changed SessionActions and provide protocols
    for the App Setting Pages
    """
    def __init__(self):
        self.session_action_changed = Signal()
        self.__protocols = {}

    def populate_protocol(self, p_name, protocol):
        self.__protocols[p_name.lower()] = protocol

    def get_protocol(self, p_name):
        if p_name.lower() not in self.__protocols:
            raise KeyError("ControllerCommon: protocol {} not found".format(p_name))
        return self.__protocols[p_name.lower()]