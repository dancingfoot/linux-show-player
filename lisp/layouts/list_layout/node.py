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

from collections.abc import Sequence


class Node(Sequence):
    """Node to build tree data structures.

    Implements the `Sequence` ABC.
    """
    def __init__(self, parent=None):
        super().__init__()

        self._children = []
        self._parent = parent

        if parent is not None:
            parent.add_child(self)

    def __getitem__(self, index):
        return self._children[index]

    def __len__(self):
        return len(self._children)

    def parent(self):
        """
        :rtype: Node
        """
        return self._parent

    def set_parent(self, parent):
        """
        :type parent: Node
        """
        self._parent = parent

    def row(self):
        if self._parent is not None:
            return self._parent.index(self)

        return -1

    def add_child(self, child):
        """Append a child.

        :param child: The node to be added as child
        :type child: Node
        """
        self.insert_child(len(self._children), child)

    def insert_child(self, index, child):
        """Insert a child to this node.

        :param index: Index where to insert the child.
        :type index: int
        :param child: The node to be added as child.
        :type child: Node
        """
        if not 0 <= index <= len(self._children):
            index = len(self._children)

        self._children.insert(index, child)
        child.set_parent(self)

    def remove_child(self, index):
        """Remove the child at the give index, if exists.

        :param index: index of the child to be removed.
        :type index: int
        :return: True if a child as ben remove, False otherwise.
        :rtype bool
        """
        if abs(index) < len(self._children):
            child = self._children.pop(index)
            child.set_parent(None)
            return True

        return False

    def clear(self):
        for _ in range(len(self._children)):
            self.remove_child(-1)

    def child_index(self, child):
        return self._children.index(child)

    def log(self, prefix='', root=False, last=False):
        output = prefix

        if not root:
            output += '├── ' if not last else '└── '
        output += str(self) + '\n'

        for child in self._children[:-1]:
            if not root:
                output += child.log(prefix=prefix + '|\t')
            else:
                output += child.log(prefix=prefix)

        if self._children:
            if not (root or last):
                prefix += '|'
            if not root:
                prefix += '\t'
            output += self._children[-1].log(prefix=prefix, last=True)

        return output


class CueNode(Node):
    """Node extension that handle cue(s) as data type.

    .. warning:
        Only CueNode(s) objects can be used as parent and children.
    """

    def __init__(self, cue, parent=None):
        super().__init__(parent)

        self._cue = cue

    @property
    def cue(self):
        """
        :rtype: lisp.cues.cue.Cue
        """
        return self._cue

    def cues(self):
        """Iterate over the children cues."""
        for child in self._children:
            yield child.cue

    def parent(self):
        return super().parent()

    def set_parent(self, parent):
        if not isinstance(parent, (CueNode, None.__class__)):
            raise TypeError('CueNode parent must be a CueNode not {}'.format(
                parent.__class__.__name__))

        super().set_parent(parent)
        self._cue.parent = parent.cue.id if parent is not None else None

    def insert_child(self, index, child):
        if not isinstance(child, CueNode):
            raise TypeError('CueNode children must be CueNode(s) not {}'.format(
                child.__class__.__name__))

        super().insert_child(index, child)
        self._sync_cues_indices(index)

    def remove_child(self, index):
        if super().remove_child(index):
            self._sync_cues_indices(index)

    def _sync_cues_indices(self, start, stop=-1):
        """Updates the children-cues indices to be in sync.

        :param start: Start index (included)
        :type start: int
        :param stop: End index (excluded)
        :type stop: int
        """

        if not 0 <= stop <= len(self._children):
            stop = len(self._children)

        if start < stop:
            for index in range(start, stop):
                self._children[index].cue.index = index
