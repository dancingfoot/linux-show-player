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

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QListWidget, QListWidgetItem

from lisp.core.signal import Connection
from lisp.layouts.list_layout.playing_mediawidget import PlayingMediaWidget


class PlayingListWidget(QListWidget):

    def __init__(self, playing_model, **kwargs):
        super().__init__(**kwargs)

        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setFocusPolicy(Qt.NoFocus)
        self.setSelectionMode(self.NoSelection)

        self._playing_items = {}
        self._playing_model = playing_model
        self._playing_model.item_added.connect(
            self._item_added, Connection.QtQueued)
        self._playing_model.item_removed.connect(
            self._item_removed, Connection.QtQueued)
        self._playing_model.model_reset.connect(
            self._model_reset, Connection.QtQueued)

        self.__dbmeter_visible = False
        self.__seek_visible = False
        self.__accurate_time = False

    @property
    def dbmeter_visible(self):
        return self.__dbmeter_visible

    @dbmeter_visible.setter
    def dbmeter_visible(self, visible):
        self.__dbmeter_visible = visible
        for item in self._playing_items.values():
            self.itemWidget(item).set_dbmeter_visible(visible)

    @property
    def seek_visible(self):
        return self.__seek_visible

    @seek_visible.setter
    def seek_visible(self, visible):
        self.__seek_visible = visible
        for item in self._playing_items.values():
            self.itemWidget(item).set_seek_visible(visible)

    @property
    def accurate_time(self):
        return self.__accurate_time

    @accurate_time.setter
    def accurate_time(self, accurate):
        self.__accurate_time = accurate
        for item in self._playing_items.values():
            self.itemWidget(item).set_accurate_time(accurate)

    def _item_added(self, cue):
        widget = PlayingMediaWidget(cue, parent=self)
        widget.set_dbmeter_visible(self.__dbmeter_visible)
        widget.set_seek_visible(self.__seek_visible)
        widget.set_accurate_time(self.__accurate_time)

        item = QListWidgetItem()
        item.setSizeHint(widget.size())

        self.addItem(item)
        self.setItemWidget(item, widget)
        self._playing_items[cue] = item

    def _item_removed(self, cue):
        item = self._playing_items.pop(cue)
        widget = self.itemWidget(item)
        row = self.indexFromItem(item).row()

        self.removeItemWidget(item)
        self.takeItem(row)

        widget.deleteLater()

    def _model_reset(self):
        for cue in list(self._playing_items.keys()):
            self._item_removed(cue)
