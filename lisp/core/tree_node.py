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


class TreeNode(Sequence):
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
        :rtype: TreeNode
        """
        return self._parent

    def set_parent(self, parent):
        """Set the node parent.

        :param parent: The new parent
        :type parent: TreeNode, None
        """
        self._parent = parent

    def row(self):
        """
        :return: the node position/index in the parent
        :rtype: int
        """
        if self._parent is not None:
            return self._parent.index(self)

        return -1

    def add_child(self, child):
        """Append a child.

        :param child: The node to be added as child
        :type child: TreeNode
        """
        self.insert_child(len(self._children), child)

    def insert_child(self, index, child):
        """Insert a child to a specif index.

        :param index: Index where to insert the child
        :type index: int
        :param child: The node to insert
        :type child: TreeNode
        """
        if not 0 <= index <= len(self._children):
            index = len(self._children)

        self._children.insert(index, child)
        child.set_parent(self)

    def remove(self, index):
        """Remove the child at the give index, if exists.

        :param index: index of the child to be removed
        :type index: int
        """
        if abs(index) < len(self._children):
            child = self._children.pop(index)
            child.set_parent(None)

    def remove_child(self, child):
        """Remove the given child, if exists.

        :param child: The child node to be removed
        :type child: TreeNode
        """
        self._children.remove(child)
        child.set_parent(None)

    def clear(self):
        """Remove all the children from the node."""
        for _ in range(len(self._children)):
            self.remove(-1)

    def index_path(self):
        """
        :return: A list of indices representing the node path from the root.
        :rtype: list[int]
        """
        chain = []
        if self._parent is not None:
            chain.extend(self._parent.index_path())
            chain.append(self.row())

        return chain
