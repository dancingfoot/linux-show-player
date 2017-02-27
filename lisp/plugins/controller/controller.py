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
from lisp.core.configuration import config
from lisp.layouts.list_layout.layout import ListLayout
from lisp.layouts.cart_layout.layout import CartLayout
from lisp.ui import elogging
from lisp.core.message_dispatcher import MessageDispatcher
from lisp.plugins.controller.controller_common import SessionAction, SessionCallbacks, ControllerCommon
from lisp.ui.settings.app_settings import AppSettings


class CueHandler:
    def __init__(self, target, action):
        if not isinstance(target, Cue):
            raise TypeError("CueHandler: wrong argument type for handler target {0}".format(type(target)))
        if not type(action) is CueAction:
            raise TypeError("CueHandler: wrong argument type for action {0}".format(type(action)))

        self.target = target
        self.action = action

    def execute(self, *args):
        self.target.execute(self.action)


class SessionHandler:
    def __init__(self, func, num_args):
        self.__func = func
        self.__num_args = num_args

    def execute(self, *args):
        if self.__num_args <= len(args):
            self.__func(*args[:self.__num_args])
        else:
            elogging.warning("SessionHandler: could not execute SessionAction - wrong number of Arguments")


class SessionController:
    def __init__(self):
        self.__layout = None
        self.__cmd_dict = {}

    def init(self):
        # setup commands dependend on layout
        self.__layout = Application().layout.__class__

        # set command dict
        if isinstance(Application().layout, ListLayout):
            self.__cmd_dict = SessionCallbacks.get_list_layout()
        elif isinstance(Application().layout, CartLayout):
            self.__cmd_dict = SessionCallbacks.get_cart_layout()

    def reset(self):
        # clear command dict
        self.__cmd_dict = {}

    def factory(self, action):
        if action in self.__cmd_dict:
            func = getattr(Application().layout, self.__cmd_dict[action][0])
            return SessionHandler(func, len(self.__cmd_dict[action][1]))
        else:
            None


class Controller(Plugin):

    Name = 'Controller'

    def __init__(self):
        super().__init__()
        self.__protocols = {}

        # clear these on every new session
        self.__cue_map = {}
        self.__handler_map = {}
        self.__dispatcher = MessageDispatcher()

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

        # Register app settings
        for settings in protocols.ProtocolsAppSettings:
            AppSettings.register_settings_widget(settings)

        # ControllerCommon connect to app settings changes
        ControllerCommon().session_action_changed.connect(self.session_action_changed)

    def init(self):
        for protocol in self.__protocols.values():
            protocol.init()

        self.__session_controller.init()

        # load settings
        for p_name in self.__protocols:
            if p_name == 'midi':
                if 'MidiInput' in config:
                    for action in SessionAction:
                        msg_str = config['MidiInput'].get(action.name.lower(), '')
                        if msg_str:
                            self.session_action_changed(p_name, msg_str, action)
                else:
                    elogging.error("CommonController: no Midi Input settings found in application settings")

    def reset(self):
        # self.__map.clear()
        # self.__actions_map.clear()
        self.__cue_map.clear()
        self.__dispatcher.clear()

        for protocol in self.__protocols.values():
            protocol.reset()

        self.__session_controller.reset()

    def session_action_changed(self, p_name, msg_str, action):
        if action in self.__handler_map:
            self.__handler_map.pop(action)

        msg_id = self.__protocols[p_name].parse_id(msg_str)
        mask = self.__protocols[p_name].parse_mask(msg_str)

        handler = self.__session_controller.factory(action)
        if handler:
            self.__handler_map[action] = handler
            self.__dispatcher.add(msg_id, handler, mask)

    # Note:
    # MessageDispatcher stores weakrefs of CueHandler Objects (cue, action) in a Weakset, which are stored
    # by the Controller Plugin in
    # dict (key : dict) -> dict (cue : handler)
    #
    # add (cue_changed):
    #
    #
    # remove(cue) -> for key in self.__messages: self.__messages[key].pop(cue)
    # InputController().remove(key) -> parse_key, parse_mask ???? => protocol !!!!
    #

    def cue_changed(self, cue, property_name, value):
        if property_name == 'controller':
            self.delete_from_map(cue)

            for protocol in self.__protocols:
                for msg_str, action in value.get(protocol, []):

                    # 1.) store handler with target and action, self.__messages
                    if msg_str not in self.__cue_map:
                        self.__cue_map[msg_str] = {}
                    handler = CueHandler(cue, CueAction(action))
                    self.__cue_map[msg_str][cue] = handler

                    # 2.) create msg_id and value mask for message and put handler into MessageDispatcher
                    #     MessageDispatcher only holds weakrefs, if the handler is deleted from self.__messages,
                    #     its also removed from the MessageDispatcher
                    msg_id = self.__protocols[protocol].parse_id(msg_str)
                    mask = self.__protocols[protocol].parse_mask(msg_str)
                    self.__dispatcher.add(msg_id, handler, mask)

    def delete_from_map(self, cue):
        for msg_str in self.__cue_map:
            if cue in self.__cue_map[msg_str]:
                self.__cue_map[msg_str].pop(cue)

        # TODO: cleanup __dispatcher
        # self.__dispatcher.clean_up()

    # def perform_action(self, key):
    def perform_action(self, protocol, msg_id, *args):
        print(protocol, msg_id, *args)

        items, mask = self.__dispatcher.item(msg_id, args)

        if not items:
            # no handler for incoming message
            return

        args = self.__dispatcher.filter(mask, *args)

        for handler in items:
            handler.execute(*args)

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
                ControllerCommon().populate_protocol(protocol_class.__name__.lower(), protocol)
            except Exception as e:
                import logging
                import traceback

                logging.error('CONTROLLER: cannot setup protocol "{}"'.format(
                    protocol_class.__name__))
                logging.debug(traceback.format_exc())
