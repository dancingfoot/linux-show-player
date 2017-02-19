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
from PyQt5.QtWidgets import QGroupBox, QVBoxLayout, QComboBox, QGridLayout, QLabel, QSpinBox, QLineEdit, QSizePolicy

from lisp.modules import check_module
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
        self.inputGroup = QGroupBox(self)
        self.inputGroup.setTitle(
            translate('GlobalControllerSettings', 'MIDI Input'))
        self.inputGroup.setLayout(QGridLayout())
        self.layout().addWidget(self.inputGroup)

        self.channelLabel = QLabel(translate('GlobalControllerSettings', 'Channel'),
                                   self.inputGroup)
        self.inputGroup.layout().addWidget(self.channelLabel, 0, 0)
        self.channelSpinbox = QSpinBox(self.inputGroup)
        self.channelSpinbox.setRange(0, 15)
        self.inputGroup.layout().addWidget(self.channelSpinbox, 0, 3)

        row = 1
        for action in GlobalAction:
            self.create_widget(action, row)
            row += 1

        if not check_module('Midi'):
            self.inputGroup.setEnabled(False)

    def __msg_changed(self, action):
        protocol = CommonController().get_protocol(ControllerProtocol.MIDI)
        key = protocol.key_from_values(self.__widgets[action][0].currentText(),
                                       self.channelSpinbox.value(),
                                       self.__widgets[action][1].value(),
                                       self.__widgets[action][2].value())
        if not key:
            self.__widgets[action][1].setValue(0)
            self.__widgets[action][2].setValue(0)

        CommonController().notify_key_changed.emit(action, ControllerProtocol.MIDI, key)

    def __calc_arg_length(self, msg_type, action):
        arguments = MSGS_ATTRIBUTES[msg_type]
        params = len(action.get_controller().params)
        if None in arguments:
            arguments.remove(None)

        arg_size = len(arguments) - 1 # ignore channel

        self.__widgets[action][1].blockSignals(True)
        self.__widgets[action][2].blockSignals(True)

        if arg_size == 1:
            if params:
                for i in range(1, 3):
                    self.__widgets[action][i].setEnabled(False)
                    self.__widgets[action][i].setRange(-1, 127)
                    self.__widgets[action][i].setSpecialValueText("*")
                    self.__widgets[action][i].setValue(-1)
            else:
                self.__widgets[action][1].setEnabled(True)
                self.__widgets[action][1].setRange(0, 127)
                self.__widgets[action][1].setSpecialValueText("")
                self.__widgets[action][2].setEnabled(False)
                self.__widgets[action][2].setRange(-1, 127)
                self.__widgets[action][2].setSpecialValueText("*")
                self.__widgets[action][2].setValue(-1)
        elif arg_size == 2:
            if params:
                self.__widgets[action][1].setEnabled(True)
                self.__widgets[action][1].setRange(0, 127)
                self.__widgets[action][1].setSpecialValueText("")
                self.__widgets[action][2].setEnabled(False)
                self.__widgets[action][2].setRange(-1, 127)
                self.__widgets[action][2].setSpecialValueText("*")
                self.__widgets[action][2].setValue(-1)
            else:
                self.__widgets[action][1].setEnabled(True)
                self.__widgets[action][1].setRange(0, 127)
                self.__widgets[action][1].setSpecialValueText("")
                self.__widgets[action][2].setEnabled(True)
                self.__widgets[action][2].setRange(-1, 127)
                self.__widgets[action][2].setSpecialValueText("*")
                self.__widgets[action][2].setValue(-1)
        else:
            # TODO: catch this earlier, if there are Actions with more than one argument (arg_size < 1)
            raise RuntimeError("MidiControllerSettings: too much args for message type: {}".format(msg_type))

        self.__widgets[action][1].blockSignals(False)
        self.__widgets[action][2].blockSignals(False)

    def __msg_type_changed(self, msg_type, action):
        self.__calc_arg_length(msg_type, action)
        self.__msg_changed(action)

    def create_widget(self, action, row):
        label = QLabel(translate('GlobalControllerSettings', action.name.replace('_', ' ').capitalize()),
                       self.inputGroup)
        self.inputGroup.layout().addWidget(label, row, 0)
        combo = QComboBox(self.inputGroup)
        combo.addItems(['note_on', 'note_off', 'control_change', 'program_change'])
        combo.currentTextChanged.connect(lambda msg_type: self.__msg_type_changed(msg_type, action))
        combo.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed);
        self.inputGroup.layout().addWidget(combo, row, 1)
        spinbox1 = QSpinBox(self.inputGroup)
        spinbox1.setRange(0, 127)
        spinbox1.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed);
        spinbox1.valueChanged.connect(lambda: self.__msg_changed(action))
        self.inputGroup.layout().addWidget(spinbox1, row, 2)
        spinbox2 = QSpinBox(self.inputGroup)
        spinbox2.setRange(-1, 127)
        spinbox2.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed);
        spinbox2.setSpecialValueText("*")
        spinbox2.valueChanged.connect(lambda: self.__msg_changed(action))
        self.inputGroup.layout().addWidget(spinbox2, row, 3)

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

    def load_midi_actions(self, settings):
        for action in GlobalAction:
            protocol = CommonController().get_protocol(ControllerProtocol.MIDI)
            # values = protocol.values_from_key(config['MidiInput'].get(action.name.lower(), ''))
            values = protocol.values_from_key(settings.get(action.name.lower(), ''))

            if len(values):
                # message type
                self.__widgets[action][0].setCurrentText(values[0])

                # set ranges and arg length
                self.__calc_arg_length(values[0], action)

                # fill in values
                for i in range(1, 3):
                    if len(values) > i:
                        self.__widgets[action][i].setValue(int(values[i]))

    def load_settings(self, settings):
        settings = settings.get('MidiInput', {})

        channel = int(settings.get('channel', 0))
        self.channelSpinbox.setValue(channel)

        self.load_midi_actions(settings)


class OscControllerSettings(SettingsPage):
    Name = QT_TRANSLATE_NOOP('SettingsPageName', 'OSC input')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setLayout(QVBoxLayout())
        self.layout().setAlignment(Qt.AlignTop)

        self.__widgets = {}

        # OSC Input
        self.inputGroup = QGroupBox(self)
        self.inputGroup.setTitle(
            translate('GlobalControllerSettings', 'OSC Input'))
        self.inputGroup.setLayout(QGridLayout())
        self.layout().addWidget(self.inputGroup)

        row = 1
        for action in GlobalAction:
            self.create_widget(action, row)
            row += 1

        if not check_module('Osc'):
            self.inputGroup.setEnabled(False)

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
        label = QLabel(translate('GlobalControllerSettings', action.name.replace('_', ' ').capitalize()),
                       self.inputGroup)
        self.inputGroup.layout().addWidget(label, row, 0)
        line_edit = QLineEdit(self.inputGroup)
        line_edit.editingFinished.connect(lambda path: self.__msg_path_changed(path, action))
        self.inputGroup.layout().addWidget(line_edit, row, 1)
        if int in action.get_controller().params:
            spinbox = QSpinBox(self.inputGroup)
            spinbox.setRange(0, 127)
            spinbox.valueChanged.connect(lambda: self.__msg_changed(action))
            self.inputGroup.layout().addWidget(spinbox, row, 2)
            self.__widgets[action] = [line_edit, spinbox]
        elif float in action.get_controller().params:
            spinbox = QSpinBox(self.inputGroup)
            spinbox.setRange(0, 127)
            spinbox.valueChanged.connect(lambda: self.__msg_changed(action))
            self.inputGroup.layout().addWidget(spinbox, row, 2)
            self.__widgets[action] = [line_edit, spinbox]
        else:
            self.__widgets[action] = [line_edit]

    def get_settings(self):
        conf = {}

        if self.isEnabled():
            for action, widget in self.__widgets.items():
                if int in action.get_controller().params:
                    # set key from path, value
                    pass
                if float in action.get_controller().params:
                    # set key from path, value
                    pass
                else:
                    # set key from path
                    pass

        return {'OscInput': conf}

    def load_osc_actions(self, settings):
        for action in self.__widgets:
            # *get key from setting
            # *fillin widget values
            pass

    def load_settings(self, settings):
        settings = settings.get('OscInput', {})
        self.load_osc_actions(settings)
