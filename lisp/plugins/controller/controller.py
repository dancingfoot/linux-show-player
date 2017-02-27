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

from lisp.application import Application
from lisp.core.has_properties import Property
from lisp.core.plugin import Plugin
from lisp.cues.cue import Cue, CueAction
from lisp.plugins.controller import protocols
from lisp.plugins.controller.controller_settings import ControllerSettings
from lisp.ui.settings.cue_settings import CueSettingsRegistry

# SessionController
from enum import Enum
from lisp.layouts.list_layout.layout import ListLayout
from lisp.layouts.cart_layout.layout import CartLayout


class SessionActionType(Enum):
    GO = 'Go'
    STOP = 'STOP'
    PAGE = 'PAGE'


class Handler:
    def __init__(self, controlled_inst, action):
        self.__instance = controlled_inst
        self.__action = action


class SessionController:
    __CMD_LIST = {
        SessionActionType.GO: ListLayout.go,
        SessionActionType.STOP: ListLayout.stop_all
    }

    __CMD_CART = {
        SessionActionType.PAGE: CartLayout.set_current_index
    }

    def __init__(self):
        self.__layout = None
        self.__cmd_dict = {}

    def init(self):
        # setup commands dependend on layout
        self.__layout = Application().layout.__class__
        print("Controller.init Layout: ", self.__layout)

        # set command dict
        if isinstance(Application().layout, ListLayout):
            self.__cmd_dict = SessionController.__CMD_LIST
        elif isinstance(Application().layout, CartLayout):
            self.__cmd_dict = SessionController.__CMD_CART

    def reset(self):
        # clear command dict
        self.__cmd_dict = {}

    def execute(self, action):
        cmd = self.__cmd_dict.get(action)
        print("SessionController execute: ", action, self.__cmd_dict[cmd])


class Controller(Plugin):

    Name = 'Controller'

    def __init__(self):
        super().__init__()
        self.__map = {}
        self.__actions_map = {}
        self.__protocols = {}

        # test
        self.__session_controller = SessionController()

        # Register a new Cue property to store settings
        Cue.register_property('controller', Property(default={}))

        # Listen cue_model changes
        Application().cue_model.item_added.connect(self.__cue_added)
        Application().cue_model.item_removed.connect(self.__cue_removed)

        # Register settings-page
        CueSettingsRegistry().add_item(ControllerSettings)
        # Load available protocols
        self.__load_protocols()

        # Common Input Controller Module
        # InputController().action_changed.connect(self.session_action_changed)

    def init(self):
        for protocol in self.__protocols.values():
            protocol.init()

        self.__session_controller.init()

    def reset(self):
        self.__map.clear()
        self.__actions_map.clear()

        for protocol in self.__protocols.values():
            protocol.reset()

        self.__session_controller.reset()

    def session_action_changed(self, key, action):
        self.delete_from_map(self.__session_controller)

        if key not in self.__map:
            self.__map[key] = set()

        self.__map[key].add(self.__session_controller)
        self.__actions_map[(key, self.__session_controller)] = action

    # Note:
    # MessageDict stores weakrefs of Handler Objects (cue, action) in a Weakset, which are stored
    # by the Controller Plugin in
    # dict (key : dict) -> dict (cue : handler)
    #
    # add (cue_changed):
    #
    #
    # remove(cue) -> for key in self.__map: self.__map[key].pop(cue)
    # InputController().remove(key) -> parse_key, parse_mask ???? => protocol !!!!
    #

    def cue_changed(self, cue, property_name, value):
        if property_name == 'controller':
            self.delete_from_map(cue)

            for protocol in self.__protocols:
                for key, action in value.get(protocol, []):
                    if key not in self.__map:
                        self.__map[key] = set()

                    self.__map[key].add(cue)
                    self.__actions_map[(key, cue)] = CueAction(action)

    def delete_from_map(self, cue):
        for key in self.__map:
            self.__map[key].discard(cue)
            self.__actions_map.pop((key, cue), None)

    def perform_action(self, key):
        for cue in self.__map.get(key, []):
            cue.execute(self.__actions_map[(key, cue)])

    def __cue_added(self, cue):
        cue.property_changed.connect(self.cue_changed)
        self.cue_changed(cue, 'controller', cue.controller)

    def __cue_removed(self, cue):
        cue.property_changed.disconnect(self.cue_changed)
        self.delete_from_map(cue)

    def __load_protocols(self):
        protocols.load()

        for protocol_class in protocols.Protocols:
            try:
                protocol = protocol_class()
                protocol.protocol_event.connect(self.perform_action)

                self.__protocols[protocol_class.__name__.lower()] = protocol
            except Exception as e:
                import logging
                import traceback

                logging.error('CONTROLLER: cannot setup protocol "{}"'.format(
                    protocol_class.__name__))
                logging.debug(traceback.format_exc())
