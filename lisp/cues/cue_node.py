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

from lisp.core.tree_node import TreeNode


class CueNode(TreeNode):
    """TreeNode extension that handle cue(s) as data type.

    .. Warning:
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
        """Set the node parent.

        :param parent: The new parent.
        :type parent: CueNode
        """
        if not isinstance(parent, CueNode):
            raise TypeError('CueNode parent must be a CueNode not {}'.format(
                parent.__class__.__name__))

        super().set_parent(parent)
        self._cue.parent = parent.cue.id

    def insert_child(self, index, child):
        """Insert a child to a specif index

        :param index: Index where to insert the child
        :type index: int
        :param child: TreeNode child to insert
        :type child: CueNode
        """
        if not isinstance(child, CueNode):
            raise TypeError('CueNode children must be CueNode(s) not {}'.format(
                child.__class__.__name__))

        super().insert_child(index, child)
        self._sync_cues_indices(index)

    def remove_child(self, index):
        super().remove_child(index)
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
