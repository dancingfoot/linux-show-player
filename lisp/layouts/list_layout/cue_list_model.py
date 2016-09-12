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

from lisp.core.model_adapter import ModelAdapter
from lisp.core.proxy_model import ReadOnlyProxyModel
from lisp.cues.cue_node import CueNode
from lisp.cues.media_cue import MediaCue


class _FakeCue:
    id = None
    index = -1
    parent = None


class CueTreeModel(ModelAdapter):
    def __init__(self, model):
        super().__init__(model)

        self.__root = CueNode(_FakeCue())
        self.__nodes = {None: self.__root}

    def __iter__(self):
        for child in self.__root:
            yield from child.cues()

    def get(self, row, parent=None):
        parent_node = self.__nodes.get(parent)
        if parent_node is not None and 0 <= row < len(parent_node):
            return parent_node[row].cue

    def insert(self, item, row, parent=None):
        # The actual insert is implemented in _item_added
        item.index = row
        item.parent = parent
        self.add(item)

    def pop(self, row, parent=None):
        # The actual pop/remove is implemented in _item_removed
        cue = self.get(row, parent=parent)

        if cue is None:
            raise IndexError('Invalid index: {} - {}'.format(row, parent))

        self.model.remove(cue)
        return cue

    def move(self, src_row, src_parent, to_row, to_parent):
        src_parent = self.__nodes.get(src_parent)
        to_parent = self.__nodes.get(to_parent)

        # Check if the row is valid
        if not 0 <= to_row < len(to_parent):
            return

        if src_parent == to_parent and src_row == to_row:
            # If a no-op (same index) do nothing
            return

        node = src_parent[src_row]

        src_parent.remove(src_row)
        to_parent.insert_child(to_row, node)

        self.item_moved.emit(src_row, src_parent, to_row, to_parent)

    def _cleared(self):
        self.__root.clear()
        self.cleared.emit()

    def _item_added(self, item):
        node = CueNode(item)
        parent_node = self.__nodes.get(item.parent, self.__root)

        if not 0 <= item.index <= len(parent_node):
            item.index = len(parent_node)

        parent_node.insert_child(item.index, node)
        self.__nodes[item.id] = node

        self.item_added.emit(item)

    def _item_removed(self, item):
        parent_node = self.__nodes.get(item.parent)
        parent_node.remove(self.__nodes.pop(item.id))

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
