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


class _FakeCue:
    def __init__(self):
        self.id = None
        self.index = -1
        self.parent = None


class CueTreeModel(ModelAdapter, QAbstractItemModel, metaclass=QABCMeta):
    def __init__(self, model):
        ModelAdapter.__init__(self, model)
        QAbstractItemModel.__init__(self)

        self.__root = CueNode(_FakeCue())
        self.__nodes = {None: self.__root}

    def __iter__(self):
        for child in self.__root:
            yield from child.cues()

    def rowCount(self, parent):
        if not parent.isValid():
            return len(self.__root)

        return len(parent.internalPointer())

    def columnCount(self, parent):
        return 1

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        node = index.internalPointer()
        if role == Qt.DisplayRole or role == Qt.EditRole:
            if index.column() == 0:
                return node.cue.name

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                if section == 0:
                    return 'Name'

    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def parent(self, index):
        parent_node = self.node(index).parent()

        if parent_node is self.__root or parent_node is None:
            return QModelIndex()

        return self.createIndex(parent_node.row(), 0, parent_node)

    def index(self, row, column, parent=QModelIndex()):
        if self.hasIndex(row, column, parent):
            return self.createIndex(row, column, self.node(parent)[row])

        return QModelIndex()

    def moveRow(self, src_parent, src_row, dest_parent, dest_child):
        return self.moveRows(src_parent, src_row, 1, dest_parent, dest_child)

    def moveRows(self, src_parent, src_row, rows, dest_parent, dest_child):
        # Check if the row is valid
        if not 0 <= dest_child < len(self.node(dest_parent)):
            return

        dest_row = dest_child
        if src_parent == dest_parent:
            # If a no-op (same index) do nothing
            if src_row == dest_child:
                return

            # If moving down (to higher indices) in the same parent we need to
            # take care of some Qt bullshit, otherwise we get a SEGFAULT
            if dest_child > src_row:
                dest_row += rows

        if self.beginMoveRows(src_parent, src_row, rows, dest_parent, dest_row):

            for n in range(src_row, rows):
                src_row += 1
                node = self.node(self.index(src_row, 0, src_parent))

                src_parent = self.node(src_parent)
                src_parent.remove_child(src_row)

                dest_parent = self.node(dest_parent)
                dest_parent.insert_child(dest_child, node)

            self.endMoveRows()
            return True

        return False

    def index_by_id(self, id):
        """
        :param id: The cue id
        :type id: str
        :return: The QModelIndex of the cue
        :rtype: QModelIndex
        """
        node = self.__nodes.get(id)
        index = self.createIndex(node.row(), 0, node)
        return index

    def node(self, index):
        if index.isValid():
            node = index.internalPointer()
            if node is not None:
                return node

        return self.__root

    def get(self, row, parent=None):
        return self.node(self.index_by_id(parent))[row].cue

    def insert(self, item, row, parent=None):
        item.index = row
        item.parent = parent
        self.add(item)

    def pop(self, row, parent=None):
        cue = self.get(row, parent=parent)
        self.model.remove(cue)
        return cue

    def move(self, item, dest_row, dest_parent=None):
        src_parent = self.index_by_id(item.parent)
        dest_parent = self.index_by_id(dest_parent)

        self.moveRow(src_parent, item.index, dest_parent, dest_row)

    def _cleared(self):
        self.beginResetModel()
        self.__root.clear()
        self.endResetModel()
        self.cleared.emit()

    def _item_added(self, item):
        row = item.index
        parent_index = self.index_by_id(item.parent)

        parent_node = self.node(parent_index)
        child_node = CueNode(item)

        if not 0 <= row <= len(parent_node):
            row = len(parent_node)

        self.beginInsertRows(parent_index, row, row)
        parent_node.insert_child(row, child_node)
        self.__nodes[item.id] = child_node
        self.endInsertRows()

        self.item_added.emit(item)

    def _item_removed(self, item):
        row = item.index
        parent_index = self.index_by_id(item.parent)
        parent_node = self.node(parent_index)

        self.beginRemoveRows(parent_index, row, row)
        parent_node.remove_child(row)
        self.__nodes.pop(item.id)
        self.endRemoveRows()

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
