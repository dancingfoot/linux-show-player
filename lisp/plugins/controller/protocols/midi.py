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

import inspect

from PyQt5.QtCore import Qt, QT_TRANSLATE_NOOP
from PyQt5.QtWidgets import QGroupBox, QPushButton, QComboBox, QVBoxLayout, \
    QMessageBox, QTableView, QTableWidget, QHeaderView, QGridLayout, QLabel, \
    QSpinBox, QSizePolicy

from lisp.modules import check_module
from lisp.core.configuration import config
from lisp.layouts.list_layout.layout import ListLayout
from lisp.layouts.cart_layout.layout import CartLayout
from lisp.modules.midi.midi_input import MIDIInput
from lisp.modules.midi.midi_utils import MSGS_ATTRIBUTES
from lisp.plugins.controller.protocols.protocol import Protocol
from lisp.ui.qdelegates import ComboBoxDelegate, SpinBoxDelegate, \
    CueActionDelegate
from lisp.ui.qmodels import SimpleTableModel
from lisp.ui.settings.settings_page import CueSettingsPage, SettingsPage
from lisp.ui.ui_utils import translate
from lisp.plugins.controller.controller_common import ControllerCommon, SessionAction, SessionCallbacks
from lisp.ui import elogging


class Midi(Protocol):
    def __init__(self):
        super().__init__()

        if check_module('midi'):
            midi_input = MIDIInput()
            if not midi_input.is_open():
                midi_input.open()
            MIDIInput().new_message.connect(self.__new_message)

    def __new_message(self, message):
        elogging.debug("Protocol: Midi message: {}".format(message))
        types = {'note_on', 'note_off', 'program_change', 'control_change', 'sysex'}
        if message.type in types:
            # self.protocol_event.emit(Midi.key_from_message(message), Midi.__name__, message.bytes().pop())
            # TODO use id from message
            self.protocol_event.emit(Midi.__name__.lower(), message.type, message.channel, *message.bytes()[1:])

    @staticmethod
    def id_from_message(*args):
        if len(args):
            message = args[0]
            return message.type
        else:
            return None

        # message = args[0]
        # attr = MSGS_ATTRIBUTES[message.type]
        # val_lst = [message.type]
        # val_lst.extend([getattr(message, i) for i in attr if i is not None])
        # return Midi.key_from_values(*val_lst)

    # TODO: update this method
    # if -1 is at last position -> skip it in message
    # if -1 in between -> set None
    @staticmethod
    def str_from_values(*args):
        if -1 in args:
            if all(i < 0 for i in args[args.index(-1):]):
                return '{0} {1}'.format(args[0], ' '.join((str(i) for i in args[1:] if i > -1)))
            else:
                elogging.error("Protocol Midi: cannot create key from value {}".format(args),
                               details='wildcards should only appear at the end of the message')
                return ''
        else:
            return ' '.join((str(i) for i in args))

    @staticmethod
    def values_from_str(message_str):
        if message_str:
            values = message_str.split()
            return (values[0], *(int(i) for i in values[1:]))
        else:
            return ()

    @staticmethod
    def parse_id(message_str):
        if message_str:
            values = message_str.split()
            return values[0]
        else:
            return ''

    @staticmethod
    def parse_mask(message_str):
        if message_str:
            values = message_str.split()
            return tuple(int(i) for i in values[1:])
        else:
            return ()


class MidiSettings(CueSettingsPage):
    Name = QT_TRANSLATE_NOOP('SettingsPageName', 'MIDI Controls')

    def __init__(self, cue_class, **kwargs):
        super().__init__(cue_class, **kwargs)
        self.setLayout(QVBoxLayout())
        self.layout().setAlignment(Qt.AlignTop)

        self.midiGroup = QGroupBox(self)
        self.midiGroup.setTitle(translate('ControllerMidiSettings', 'MIDI'))
        # self.midiGroup.setEnabled(check_module('midi'))
        self.midiGroup.setLayout(QGridLayout())
        self.layout().addWidget(self.midiGroup)

        self.midiModel = SimpleTableModel([
            translate('ControllerMidiSettings', 'Type'),
            translate('ControllerMidiSettings', 'Channel'),
            translate('ControllerMidiSettings', 'Note'),
            translate('ControllerMidiSettings', 'Action')])

        self.midiView = MidiView(cue_class, parent=self.midiGroup)
        self.midiView.setModel(self.midiModel)
        self.midiGroup.layout().addWidget(self.midiView, 0, 0, 1, 2)

        self.addButton = QPushButton(self.midiGroup)
        self.addButton.clicked.connect(self.__new_message)
        self.midiGroup.layout().addWidget(self.addButton, 1, 0)

        self.removeButton = QPushButton(self.midiGroup)
        self.removeButton.clicked.connect(self.__remove_message)
        self.midiGroup.layout().addWidget(self.removeButton, 1, 1)

        self.midiCapture = QPushButton(self.midiGroup)
        self.midiCapture.clicked.connect(self.capture_message)
        self.midiGroup.layout().addWidget(self.midiCapture, 2, 0)

        self.msgTypeCombo = QComboBox(self.midiGroup)
        self.msgTypeCombo.addItem(
            translate('ControllerMidiSettings', 'Filter "note on"'))
        self.msgTypeCombo.setItemData(0, 'note_on', Qt.UserRole)
        self.msgTypeCombo.addItem(
            translate('ControllerMidiSettings', 'Filter "note off"'))
        self.msgTypeCombo.setItemData(1, 'note_off', Qt.UserRole)
        self.midiGroup.layout().addWidget(self.msgTypeCombo, 2, 1)

        self.retranslateUi()

        self._default_action = self._cue_class.CueActions[0].name

    def retranslateUi(self):
        self.addButton.setText(translate('ControllerSettings', 'Add'))
        self.removeButton.setText(translate('ControllerSettings', 'Remove'))
        self.midiCapture.setText(translate('ControllerMidiSettings', 'Capture'))

    def enable_check(self, enabled):
        self.midiGroup.setCheckable(enabled)
        self.midiGroup.setChecked(False)

    def get_settings(self):
        settings = {}
        checkable = self.midiGroup.isCheckable()

        if not (checkable and not self.midiGroup.isChecked()):
            messages = []

            for row in self.midiModel.rows:
                message = Midi.str_from_values(row[0], row[1]-1, row[2])
                messages.append((message, row[-1]))

            if messages:
                settings['midi'] = messages

        return settings

    def load_settings(self, settings):
        if 'midi' in settings:
            for options in settings['midi']:
                m_type, channel, note = Midi.values_from_str(options[0])
                self.midiModel.appendRow(m_type, channel+1, note, options[1])

    def capture_message(self):
        handler = MIDIInput()
        handler.alternate_mode = True
        handler.new_message_alt.connect(self.__add_message)

        QMessageBox.information(self, '',
                                translate('ControllerMidiSettings',
                                          'Listening MIDI messages ...'))

        handler.new_message_alt.disconnect(self.__add_message)
        handler.alternate_mode = False

    def __add_message(self, msg):
        if self.msgTypeCombo.currentData(Qt.UserRole) == msg.type:
            self.midiModel.appendRow(msg.type, msg.channel+1, msg.note,
                                     self._default_action)

    def __new_message(self):
        message_type = self.msgTypeCombo.currentData(Qt.UserRole)
        self.midiModel.appendRow(message_type, 1, 0, self._default_action)

    def __remove_message(self):
        self.midiModel.removeRow(self.midiView.currentIndex().row())


class MidiView(QTableView):
    def __init__(self, cue_class, **kwargs):
        super().__init__(**kwargs)

        self.delegates = [
            ComboBoxDelegate(options=['note_on', 'note_off']),
            SpinBoxDelegate(minimum=1, maximum=16),
            SpinBoxDelegate(minimum=0, maximum=127),
            CueActionDelegate(cue_class=cue_class,
                              mode=CueActionDelegate.Mode.Name)
        ]

        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setSelectionMode(QTableView.SingleSelection)

        self.setShowGrid(False)
        self.setAlternatingRowColors(True)

        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().setHighlightSections(False)

        self.verticalHeader().sectionResizeMode(QHeaderView.Fixed)
        self.verticalHeader().setDefaultSectionSize(24)
        self.verticalHeader().setHighlightSections(False)

        for column, delegate in enumerate(self.delegates):
            self.setItemDelegateForColumn(column, delegate)


class MidiAppSettings(SettingsPage):
    Name = QT_TRANSLATE_NOOP('SettingsPageName', 'MIDI input')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setLayout(QVBoxLayout())
        self.layout().setAlignment(Qt.AlignTop)

        self.__widgets = {}

        # Midi Input
        self.inputGroup = QGroupBox(self)
        self.inputGroup.setTitle(
            translate('ControllerMidiSettings', 'MIDI Input'))
        self.inputGroup.setLayout(QGridLayout())
        self.layout().addWidget(self.inputGroup)

        self.channelLabel = QLabel(translate('ControllerMidiSettings', 'Channel'),
                                   self.inputGroup)
        self.inputGroup.layout().addWidget(self.channelLabel, 0, 0)
        self.channelSpinbox = QSpinBox(self.inputGroup)
        self.channelSpinbox.setRange(0, 15)
        self.inputGroup.layout().addWidget(self.channelSpinbox, 0, 3)

        row = 1
        for action in SessionAction:
            self.create_widget(action, row)
            row += 1

        if not check_module('Midi'):
            self.inputGroup.setEnabled(False)

    # TODO: add layout as param
    def __calc_arg_length(self, msg_type, action):
        arguments = MSGS_ATTRIBUTES[msg_type]

        if action in SessionCallbacks.get_cart_layout():
            params = SessionCallbacks.parameter(CartLayout, action)
        elif action in SessionCallbacks.get_list_layout():
            params = SessionCallbacks.parameter(ListLayout, action)
        else:
            raise KeyError("MidiAppSettings: no parameter list for action {0} found".format(action))

        if None in arguments:
            arguments.remove(None)

        arg_size = len(arguments) - 1  # ignore channel

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
        label = QLabel(translate('GlobalControllerSettings', action.value),
                       self.inputGroup)
        self.inputGroup.layout().addWidget(label, row, 0)
        combo = QComboBox(self.inputGroup)
        combo.addItems(['note_on', 'note_off', 'control_change', 'program_change'])
        # combo.currentTextChanged.connect(lambda msg_type: self.__msg_type_changed(msg_type, action))
        combo.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.inputGroup.layout().addWidget(combo, row, 1)
        spinbox1 = QSpinBox(self.inputGroup)
        spinbox1.setRange(0, 127)
        spinbox1.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        # spinbox1.valueChanged.connect(lambda: self.__msg_changed(action))
        self.inputGroup.layout().addWidget(spinbox1, row, 2)
        spinbox2 = QSpinBox(self.inputGroup)
        spinbox2.setRange(-1, 127)
        spinbox2.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        spinbox2.setSpecialValueText("*")
        # spinbox2.valueChanged.connect(lambda: self.__msg_changed(action))
        self.inputGroup.layout().addWidget(spinbox2, row, 3)

        self.__widgets[action] = [combo, spinbox1, spinbox2]

    def get_settings(self):
        conf = {}

        if self.isEnabled():
            protocol = ControllerCommon().get_protocol('midi')
            for action, widget in self.__widgets.items():
                msg_str = protocol.str_from_values(widget[0].currentText(),
                                                   self.channelSpinbox.value(),
                                                   widget[1].value(),
                                                   widget[2].value())
                conf[action.name.lower()] = msg_str
                old_str = config['MidiInput'][action.name.lower()]
                if msg_str != old_str:
                    ControllerCommon().session_action_changed.emit('midi', msg_str, action)

        return {'MidiInput': conf}

    def load_midi_actions(self, settings):
        protocol = ControllerCommon().get_protocol('midi')
        for action in SessionAction:
            values = protocol.values_from_str(settings.get(action.name.lower(), ''))

            if len(values):
                # message type

                self.channelSpinbox.setValue(values[1])

                self.__widgets[action][0].setCurrentText(values[0])

                # set ranges and arg length
                self.__calc_arg_length(values[0], action)

                # fill in values:
                if len(values) > 2:
                    self.__widgets[action][1].setValue(int(values[2]))
                if len(values) > 3:
                    self.__widgets[action][2].setValue(int(values[3]))

    def load_settings(self, settings):
        settings = settings.get('MidiInput', {})
        self.load_midi_actions(settings)
