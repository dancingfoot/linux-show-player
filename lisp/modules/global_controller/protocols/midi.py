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
from PyQt5.QtWidgets import QGroupBox, QPushButton, QComboBox, QVBoxLayout, \
    QMessageBox, QTableView, QTableWidget, QHeaderView, QGridLayout

from lisp.modules import check_module
from lisp.modules.midi.midi_input import MIDIInput
from lisp.modules.midi.midi_utils import MSGS_ATTRIBUTES
from lisp.core.protocol import Protocol
from lisp.ui.qdelegates import ComboBoxDelegate, SpinBoxDelegate, \
    CueActionDelegate
from lisp.ui.qmodels import SimpleTableModel
from lisp.ui.settings.settings_page import CueSettingsPage
from lisp.ui.ui_utils import translate
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
            self.protocol_event.emit(Midi.key_from_message(message), Midi.__name__, message.bytes().pop())

    @staticmethod
    def key_from_message(message):
        attr = MSGS_ATTRIBUTES[message.type]
        val_lst = [message.type]
        val_lst.extend([getattr(message, i) for i in attr if i is not None])
        return Midi.key_from_values(*val_lst)

    @staticmethod
    def key_from_values(*args):
        return ' '.join((str(i) for i in args))

    @staticmethod
    def values_from_key(message_str):
        if message_str:
            values = message_str.split()
            return (values[0], *(int(i) for i in values[1:]))
        else:
            return ()

    # TODO: dont use -1 as wildcard, we can leave it blank, so it will not break .lsp file format
    @staticmethod
    def wildcard_keys(key):
        """
        method returns possible wildcard keys of a midi message
        rule: last element of a midi message can be wildcarded by using -1
        if length > 3 msg type is not an sysex

        :return: list of possible wildcard string to test against
        :rtype: list
        """
        spl_msg = key.split()
        if len(spl_msg) > 3 and spl_msg[0] is not 'sysex':
            spl_msg.pop()
            spl_msg.append('-1')
            return [' '.join((i for i in spl_msg))]
        else:
            return []


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
                # values from model + wildcard (-1) for velocity
                message = Midi.key_from_values(row[0], row[1]-1, row[2], -1)
                messages.append((message, row[-1]))

            if messages:
                settings['midi'] = messages

        return settings

    def load_settings(self, settings):
        if 'midi' in settings:
            for options in settings['midi']:
                m_type, channel, note, velocity = Midi.values_from_key(options[0])
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
