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

from PyQt5 import QtCore
from PyQt5.QtCore import QMimeData, QPoint, pyqtSignal, Qt, QT_TRANSLATE_NOOP
from PyQt5.QtGui import QDrag, QKeyEvent, QContextMenuEvent
from PyQt5.QtWidgets import QApplication, QTreeWidget, QHeaderView, qApp

from lisp.core.signal import Connection
from lisp.cues.cue_factory import CueFactory
from lisp.layouts.list_layout.cue_list_item import CueListItem
from lisp.layouts.list_layout.listwidgets import CueStatusIcon, PreWaitWidget, \
    CueTimeWidget, NextActionIcon, PostWaitWidget

from lisp.ui.ui_utils import translate


class CueListView(QTreeWidget):

    key_event = pyqtSignal(QKeyEvent)
    context_event = pyqtSignal(QContextMenuEvent)
    drop_move_event = QtCore.pyqtSignal(int, int)
    drop_copy_event = QtCore.pyqtSignal(int, int)

    HEADER_NAMES = ['', '#',
                    QT_TRANSLATE_NOOP('ListLayoutHeader', 'Cue'),
                    QT_TRANSLATE_NOOP('ListLayoutHeader', 'Pre wait'),
                    QT_TRANSLATE_NOOP('ListLayoutHeader', 'Action'),
                    QT_TRANSLATE_NOOP('ListLayoutHeader', 'Post wait'),
                    '']
    HEADER_WIDGETS = [CueStatusIcon, None, None, PreWaitWidget, CueTimeWidget,
                      PostWaitWidget, NextActionIcon]

    def __init__(self, cue_model, parent=None):
        """
        :type cue_model: lisp.layouts.list_layout.cue_list_model.CueTreeModel
        """
        super().__init__(parent)
        self._model = cue_model
        self._model.item_added.connect(self.__cue_added, Connection.QtQueued)
        self._model.item_moved.connect(self.__cue_moved, Connection.QtQueued)
        self._model.item_removed.connect(self.__cue_removed, Connection.QtQueued)
        self._model.cleared.connect(self.__model_cleared)

        self.__items = {None: self.invisibleRootItem()}
        self.__guard = False

        self.setHeaderLabels(
            [translate('ListLayoutHeader', h) for h in CueListView.HEADER_NAMES])
        self.header().setDragEnabled(False)
        self.header().setStretchLastSection(False)
        self.header().setSectionResizeMode(QHeaderView.Fixed)
        self.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.header().setSectionResizeMode(2, QHeaderView.Stretch)

        self.setColumnWidth(0, 40)
        self.setColumnWidth(len(CueListView.HEADER_NAMES) - 1, 18)
        self.setSelectionMode(self.SingleSelection)
        self.setDragDropMode(self.InternalMove)
        self.setAlternatingRowColors(True)
        self.setVerticalScrollMode(self.ScrollPerItem)

        #self.setIndentation(0)

        self.currentItemChanged.connect(self.__current_changed)

        self.verticalScrollBar().rangeChanged.connect(self.__update_range)

    def dropEvent(self, event):
        start_item = self.currentItem()
        if start_item is None:
            return

        src_row = start_item.cue.index
        src_parent = start_item.cue.parent
        target = self.itemAt(event.pos())

        if target is not None:
            drop_pos = self.dropIndicatorPosition()
            if drop_pos == QTreeWidget.OnItem:
                dest_parent = target.cue.id
                dest_row = 0
            elif drop_pos == QTreeWidget.AboveItem:
                dest_parent = target.cue.parent
                dest_row = target.cue.index
            else:
                dest_parent = target.cue.parent
                dest_row = target.cue.index + 1
        else:
            dest_parent = None
            dest_row = self.topLevelItemCount() - 1

        #if not 0 <= row <= len():
        #    new_index = len(self._model)

        if qApp.keyboardModifiers() == Qt.ControlModifier:
            new_cue = CueFactory.clone_cue(target.cue)

            self._model.insert(new_cue, dest_row, dest_parent)
        else:
            self._model.move(src_row, src_parent, dest_row, dest_parent)

    def contextMenuEvent(self, event):
        if self.itemAt(event.pos()) is not None:
            self.context_event.emit(event)
        else:
            super().contextMenuEvent(event)

    def keyPressEvent(self, event):
        self.key_event.emit(event)

        if qApp.keyboardModifiers() == Qt.ControlModifier:
            # Prevent items to be deselected
            event.ignore()
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event):
        if qApp.keyboardModifiers() == Qt.ControlModifier:
            # Prevent items to be deselected
            event.ignore()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        if qApp.keyboardModifiers() == Qt.ControlModifier:
            # Prevent items to be deselected
            if self.state() == self.DragSelectingState:
                item = self.itemAt(event.pos())
                self.setCurrentItem(item)

    def current_cue(self):
        item = self.currentItem()
        if item is not None:
            return item.cue

        return None

    def __current_changed(self, current_item, previous_item):
        self.scrollToItem(current_item)

    def __cue_added(self, cue):
        item = CueListItem(cue)
        if cue.parent is not None:
            item.setFlags(item.flags() & ~Qt.ItemIsDropEnabled)
        parent = self.__items[cue.parent]
        parent.insertChild(cue.index, item)

        self.__items[cue.id] = item
        self.__init_item(item, cue)

        # Select the added item and scroll to it
        self.setCurrentItem(item)
        # Ensure that the focus is set
        self.setFocus()

    def __cue_moved(self, old_row, old_parent, new_row, new_parent):
        old_parent_item = self.__items[old_parent]
        item = old_parent_item.takeChild(old_row)

        new_parent_item = self.__items[new_parent]
        new_parent_item.insertChild(new_row, item)

        self.setCurrentItem(item)
        self.__init_item(item, self._model.get(new_row, new_parent))

    def __cue_removed(self, cue):
        parent = self.__items[cue.parent]
        parent.takeChild(cue.index)

        # TODO:
        index = cue.index
        if index > 0:
            index -= 1

        self.setCurrentIndex(self.model().index(index, 0))

    def __model_cleared(self):
        self.reset()
        self.clear()

    def __init_item(self, item, cue):
        item.name_column = CueListView.HEADER_NAMES.index('Cue')
        for index, widget in enumerate(CueListView.HEADER_WIDGETS):
            if widget is not None:
                self.setItemWidget(item, index, widget(cue))

        self.updateGeometries()

    def __update_range(self, min_, max_):
        if not self.__guard:
            self.__guard = True
            self.verticalScrollBar().setMaximum(max_ + 1)
            self.__guard = False
