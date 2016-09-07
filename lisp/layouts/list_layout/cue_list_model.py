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

from PyQt5.QtCore import Qt, QModelIndex, QAbstractItemModel
from lisp.core.qmeta import QABCMeta

from lisp.core.model_adapter import ModelAdapter
from lisp.core.proxy_model import ReadOnlyProxyModel
from lisp.cues.media_cue import MediaCue
from lisp.layouts.list_layout.node import Node, CueNode


class CueTreeModel(ModelAdapter, QAbstractItemModel, metaclass=QABCMeta):
    def __init__(self, model):
        ModelAdapter.__init__(self, model)
        QAbstractItemModel.__init__(self)

        self._root = Node()

    def __iter__(self):
        for child in self._root:
            yield from child.cues()

    def rowCount(self, parent):
        if not parent.isValid():
            return len(self._root)

        return len(parent.internalPointer())

    def columnCount(self, parent):
        return 1

    def data(self, index, role):
        if not index.isValid():
            return None

        node = index.internalPointer()
        if role == Qt.DisplayRole or role == Qt.EditRole:
            if index.column() == 0:
                return node.cue.name

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                if section == 0:
                    return 'Name'

    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def parent(self, index):
        parentNode = self.node(index).parent()

        if parentNode is self._root:
            return QModelIndex()

        return self.createIndex(parentNode.row(), 0, parentNode)

    def index(self, row, column, parent):
        node = self.node(parent)[row]

        if node is not None:
            return self.createIndex(row, column, node)
        else:
            return QModelIndex()

    def node(self, index):
        if index.isValid():
            node = index.internalPointer()
            if node is not None:
                return node

        return self._root

    def get(self, index):
        pass

    def insert(self, item, index):
        item.index = index
        self.add(item)

    def pop(self, index):
        cue = self.get(index)
        self.model.remove(cue)
        return cue

    def move(self, old_index, new_index):
        raise NotImplemented

    def _cleared(self):
        self._root.clear()
        self.cleared.emit()

    def _item_added(self, item):
        node_row = item.index
        parent_cue = self.model.get(item.parent)

        if parent_cue is None:
            parent_index = QModelIndex()
        else:
            # TODO
            parent_index = QModelIndex()

        parent_node = self.node(parent_index)

        if not 0 <= node_row <= len(parent_node):
            node_row = len(parent_node)

        self.beginInsertRows(parent_index, node_row, node_row)
        parent_node.insert_child(node_row, CueNode(item))
        self.endInsertRows()

        self.item_added.emit(item)

    def _item_removed(self, item):
        self.item_removed.emit(item)


class PlayingMediaCueModel(ReadOnlyProxyModel):
    def __init__(self, model):
        super().__init__(model)
        self.__cues = {}
        self.__playing = []

    def _item_added(self, item):
        if isinstance(item, MediaCue):
            self.__cues[item.media] = item

            item.media.on_play.connect(self._add)
            item.media.stopped.connect(self._remove)
            item.media.eos.connect(self._remove)
            item.media.interrupted.connect(self._remove)

    def _item_removed(self, item):
        if isinstance(item, MediaCue):
            item.media.on_play.disconnect(self._add)
            item.media.stopped.disconnect(self._remove)
            item.media.eos.disconnect(self._remove)
            item.media.interrupted.disconnect(self._remove)

            if item.media in self.__playing:
                self._remove(item.media)

            self.__cues.pop(item.media)

    def _cleared(self):
        for cue in self.__cues:
            self._item_removed(cue)

        self.cleared.emit()

    def _add(self, media):
        if media not in self.__playing:
            self.__playing.append(media)
            self.item_added.emit(self.__cues[media])

    def _remove(self, media):
        self.__playing.remove(media)
        self.item_removed.emit(self.__cues[media])

    def __len__(self):
        return len(self.__playing)

    def __iter__(self):
        for media in self.__playing:
            yield self.__cues[media]

    def __contains__(self, item):
        if isinstance(item, MediaCue):
            return item.media in self.__cues

        return False
