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

from PyQt5.QtCore import Qt, QT_TRANSLATE_NOOP
from PyQt5.QtWidgets import QGroupBox, QVBoxLayout, QComboBox, QGridLayout, QLabel, QSpinBox, QLineEdit, QDoubleSpinBox

from lisp.modules import check_module
from lisp.core.configuration import config
from lisp.core.protocol import Protocol
from lisp.ui.settings.settings_page import SettingsPage
from lisp.ui.ui_utils import translate
from lisp.modules.global_controller.global_controller_common import GlobalAction, CommonController, ControllerProtocol
from lisp.modules.midi.midi_utils import ATTRIBUTES_RANGE, MSGS_ATTRIBUTES


class MidiControllerSettings(SettingsPage):
    Name = QT_TRANSLATE_NOOP('SettingsPageName', 'MIDI input')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setLayout(QVBoxLayout())
        self.layout().setAlignment(Qt.AlignTop)

        self.__widgets = {}

        # Midi Input
        self.oscInputGroup = QGroupBox(self)
        self.oscInputGroup.setTitle(
            translate('GlobalControllerSettings', 'MIDI Input'))
        self.oscInputGroup.setLayout(QGridLayout())
        self.layout().addWidget(self.oscInputGroup)

        self.channelLabel = QLabel(translate('GlobalControllerSettings', 'Channel'),
                                   self.oscInputGroup)
        self.oscInputGroup.layout().addWidget(self.channelLabel, 0, 0)
        self.channelSpinbox = QSpinBox(self.oscInputGroup)
        self.channelSpinbox.setRange(0, 15)
        self.oscInputGroup.layout().addWidget(self.channelSpinbox, 0, 3)

        row = 1
        for action in GlobalAction:
            self.create_widget(action, row)
            row += 1

        if not check_module('Midi'):
            self.oscInputGroup.setEnabled(False)

    def __msg_changed(self, action):
        channel = str(self.channelSpinbox.value())
        if self.__widgets[action][2].value() < 0:
            key = ' '.join((self.__widgets[action][0].currentText(),
                            channel,
                            str(self.__widgets[action][1].value())))
            CommonController().notify_key.emit(action, ControllerProtocol.MIDI, key)
        else:
            key = ' '.join((self.__widgets[action][0].currentText(),
                            channel,
                            str(self.__widgets[action][1].value()),
                            str(self.__widgets[action][2].value())))
            CommonController().notify_key.emit(action, ControllerProtocol.MIDI, key)

    def __msg_type_changed(self, msg_type, action):
        # if you allow use other midi message than note_on/off, programm_change, control_change
        # adapt this test
        arguments = MSGS_ATTRIBUTES[msg_type]
        if None in arguments:
            arguments.remove(None)

        if len(arguments) < 3:
            self.__widgets[action][2].setValue(-1)
            self.__widgets[action][2].setEnabled(False)
        else:
            self.__widgets[action][2].setEnabled(True)

        self.__msg_changed(action)

    def create_widget(self, action, row):
        label = QLabel(translate('GlobalControllerSettings', action.name.replace('_',' ').capitalize()),
                       self.oscInputGroup)
        self.oscInputGroup.layout().addWidget(label, row, 0)
        combo = QComboBox(self.oscInputGroup)
        combo.addItems(['note_on', 'note_off', 'control_change', 'program_change'])
        combo.currentTextChanged.connect(lambda msg_type:  self.__msg_type_changed(msg_type, action))
        self.oscInputGroup.layout().addWidget(combo, row, 1)
        spinbox1 = QSpinBox(self.oscInputGroup)
        spinbox1.setRange(0, 127)
        spinbox1.valueChanged.connect(lambda:  self.__msg_changed(action))
        self.oscInputGroup.layout().addWidget(spinbox1, row, 2)
        spinbox2 = QSpinBox(self.oscInputGroup)
        spinbox2.setRange(-1, 127)
        spinbox2.setSpecialValueText("none")
        spinbox2.valueChanged.connect(lambda:  self.__msg_changed(action))
        self.oscInputGroup.layout().addWidget(spinbox2, row, 3)

        self.__widgets[action] = [combo, spinbox1, spinbox2]

    def get_settings(self):
        conf = {}

        if self.isEnabled():
            conf['channel'] = str(self.channelSpinbox.value())
            for action, widget in self.__widgets.items():
                protocol = CommonController().get_protocol(ControllerProtocol.MIDI)

                conf[action.name.lower()] = protocol.key_from_values(widget[0].currentText(),
                                                                     widget[1].value(),
                                                                     widget[2].value())


        return {'MidiInput': conf}

    def load_midi_actions(self):
        for action in GlobalAction:
            # values = tuple(config['MidiInput'].get(action.name.lower(), '').replace(' ', '').split(','))
            protocol = CommonController().get_protocol(ControllerProtocol.MIDI)
            values = protocol.values_from_key(config['MidiInput'].get(action.name.lower(), ''))

            if len(values) > 1:
                self.__widgets[action][0].setCurrentText(values[0])
                self.__widgets[action][1].setValue(int(values[1]))

            if len(values) > 2:
                self.__widgets[action][2].setValue(int(values[2]))
            else:
                self.__widgets[action][2].setValue(-1)

    def load_settings(self, settings):
        channel = int(config['MidiInput'].get('channel', 0))
        self.channelSpinbox.setValue(channel)
        self.load_midi_actions()


class OscControllerSettings(SettingsPage):
    Name = QT_TRANSLATE_NOOP('SettingsPageName', 'OSC input')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setLayout(QVBoxLayout())
        self.layout().setAlignment(Qt.AlignTop)

        self.__widgets = {}

        # OSC Input
        self.oscInputGroup = QGroupBox(self)
        self.oscInputGroup.setTitle(
            translate('GlobalControllerSettings', 'OSC Input'))
        self.oscInputGroup.setLayout(QGridLayout())
        self.layout().addWidget(self.oscInputGroup)

        row = 1
        for action in GlobalAction:
            self.create_widget(action, row)
            row += 1

        if not check_module('Osc'):
            self.oscInputGroup.setEnabled(False)

    def __msg_changed(self, action):
        pass
        # channel = str(self.channelSpinbox.value())
        # if self.__widgets[action][2].value() < 0:
        #     key = ' '.join((self.__widgets[action][0].currentText(),
        #                     channel,
        #                     str(self.__widgets[action][1].value())))
        #     CommonController().notify_key.emit(action, GlobalProtocol.MIDI, key)
        # else:
        #     key = ' '.join((self.__widgets[action][0].currentText(),
        #                     channel,
        #                     str(self.__widgets[action][1].value()),
        #                     str(self.__widgets[action][2].value())))
        #     CommonController().notify_key.emit(action, GlobalProtocol.MIDI, key)

    def __msg_path_changed(self, msg_type, action):
        pass
        # arguments = MSGS_ATTRIBUTES[msg_type]
        # if None in arguments:
        #     arguments.remove(None)
        # 
        # if len(arguments) < 3:
        #     self.__widgets[action][2].setValue(-1)
        #     self.__widgets[action][2].setEnabled(False)
        # else:
        #     self.__widgets[action][2].setEnabled(True)
        # 
        # self.__msg_changed(action)

    def create_widget(self, action, row):
        label = QLabel(translate('GlobalControllerSettings', action.name.replace('_',' ').capitalize()),
                       self.oscInputGroup)
        self.oscInputGroup.layout().addWidget(label, row, 0)
        line_edit = QLineEdit(self.oscInputGroup)
        line_edit.editingFinished.connect(lambda path:  self.__msg_path_changed(path, action))
        self.oscInputGroup.layout().addWidget(line_edit, row, 1)
        if int in action.get_controller().arg_types:
            spinbox = QSpinBox(self.oscInputGroup)
            spinbox.setRange(0, 127)
            spinbox.valueChanged.connect(lambda:  self.__msg_changed(action))
            self.oscInputGroup.layout().addWidget(spinbox, row, 2)
            self.__widgets[action] = [line_edit, spinbox]
        elif float in action.get_controller().arg_types:
            spinbox = QSpinBox(self.oscInputGroup)
            spinbox.setRange(0, 127)
            spinbox.valueChanged.connect(lambda:  self.__msg_changed(action))
            self.oscInputGroup.layout().addWidget(spinbox, row, 2)
            self.__widgets[action] = [line_edit, spinbox]
        else:
            self.__widgets[action] = [line_edit]

    def get_settings(self):
        conf = {}

        if self.isEnabled():
            for action, widget in self.__widgets.items():
                if int in action.get_controller().arg_types:
                    # set key from path, value
                    pass
                if float in action.get_controller().arg_types:
                    # set key from path, value
                    pass
                else:
                    # set key from path
                    pass

        return {'OscInput': conf}

    def load_osc_actions(self):
        for action in self.__widgets:
            # *get key from setting
            # *fillin widget values
            pass

    def load_settings(self, settings):
        channel = int(config['MidiInput'].get('channel', 0))
        self.load_osc_actions()

