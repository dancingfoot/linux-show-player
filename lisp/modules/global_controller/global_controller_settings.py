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
from PyQt5.QtWidgets import QGroupBox, QVBoxLayout, QComboBox, QGridLayout, QLabel, QSpinBox

from lisp.modules import check_module
from lisp.core.configuration import config
from lisp.ui.settings.settings_page import SettingsPage
from lisp.ui.ui_utils import translate


class GlobalControllerSettings(SettingsPage):
    Name = QT_TRANSLATE_NOOP('SettingsPageName', 'MIDI input')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setLayout(QVBoxLayout())
        self.layout().setAlignment(Qt.AlignTop)

        # Midi Input
        self.midiInputGroup = QGroupBox(self)
        self.midiInputGroup.setTitle(
            translate('GlobalControllerSettings', 'MIDI Input'))
        self.midiInputGroup.setLayout(QGridLayout())
        self.layout().addWidget(self.midiInputGroup)

        self.channelLabel = QLabel(translate('GlobalControllerSettings', 'Channel'),
                                   self.midiInputGroup)
        self.midiInputGroup.layout().addWidget(self.channelLabel, 0, 0)
        self.channelSpinbox = QSpinBox(self.midiInputGroup)
        self.channelSpinbox.setRange(0, 127)
        self.midiInputGroup.layout().addWidget(self.channelSpinbox, 0, 2)

        self.goLabel = QLabel(translate('GlobalControllerSettings', 'Go'),
                              self.midiInputGroup)
        self.midiInputGroup.layout().addWidget(self.goLabel, 1, 0)
        self.goCombo = QComboBox(self.midiInputGroup)
        self.goCombo.addItems(['note_on', 'note_off'])
        self.midiInputGroup.layout().addWidget(self.goCombo, 1, 1)
        self.goSpinbox = QSpinBox(self.midiInputGroup)
        self.goSpinbox.setRange(0, 127)
        self.midiInputGroup.layout().addWidget(self.goSpinbox, 1, 2)

        self.stopLabel = QLabel(translate('GlobalControllerSettings', 'Stop'),
                                self.midiInputGroup)
        self.midiInputGroup.layout().addWidget(self.stopLabel, 2, 0)
        self.stopCombo = QComboBox(self.midiInputGroup)
        self.stopCombo.addItems(['note_on', 'note_off'])
        self.midiInputGroup.layout().addWidget(self.stopCombo, 2, 1)
        self.stopSpinbox = QSpinBox(self.midiInputGroup)
        self.stopSpinbox.setRange(0, 127)
        self.midiInputGroup.layout().addWidget(self.stopSpinbox, 2, 2)

        if not check_module('Midi'):
            self.midiInputGroup.setEnabled(False)

    def get_settings(self):
        conf = {}

        if self.isEnabled():
            conf['channel'] = str(self.channelSpinbox.value())
            conf['go'] = ', '.join([self.goCombo.currentText(), str(self.goSpinbox.value())])
            conf['stop_all'] = ', '.join([self.stopCombo.currentText(), str(self.stopSpinbox.value())])

        return {'MidiInput': conf}

    def load_settings(self, settings):
        channel = int(config['MidiInput'].get('channel', 0))
        go = tuple(config['MidiInput'].get('go', '').replace(' ', '').split(','))
        stop_all = tuple(config['MidiInput'].get('stop_all', '').replace(' ', '').split(','))

        self.channelSpinbox.setValue(channel)

        if len(go) > 1:
            self.goCombo.setCurrentText(go[0])
            self.goSpinbox.setValue(int(go[1]))
        else:
            self.goCombo.setCurrentText('note_on')
            self.goSpinbox.setValue(0)

        if len(stop_all) > 1:
            self.stopCombo.setCurrentText(stop_all[0])
            self.stopSpinbox.setValue(int(stop_all[1]))
