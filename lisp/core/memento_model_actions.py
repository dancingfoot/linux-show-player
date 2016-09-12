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

from abc import abstractmethod

from lisp.core.action import Action


class MementoAction(Action):
    """Actions created by the MementoModel to register model changes."""

    __slots__ = ('_m_model', '_model')

    def __init__(self, m_model, model):
        super().__init__()
        self._m_model = m_model
        self._model = model

    def do(self):
        pass

    def undo(self):
        try:
            self._m_model.lock()
            self.__undo__()
        finally:
            self._m_model.unlock()

    def redo(self):
        try:
            self._m_model.lock()
            self.__redo__()
        finally:
            self._m_model.unlock()

    @abstractmethod
    def __undo__(self):
        pass

    @abstractmethod
    def __redo__(self):
        pass


class AddItemAction(MementoAction):

    __slots__ = '__item'

    def __init__(self, m_model, model, item):
        super().__init__(m_model, model)
        self.__item = item

    def __undo__(self):
        self._model.remove(self.__item)

    def __redo__(self):
        self._model.add(self.__item)

    def log(self):
        return 'Add item'


class RemoveItemAction(MementoAction):

    __slots__ = '__item'

    def __init__(self, m_model, model, item):
        super().__init__(m_model, model)
        self.__item = item

    def __undo__(self):
        self._model.add(self.__item)

    def __redo__(self):
        self._model.remove(self.__item)

    def log(self):
        return 'Remove item'


class MoveItemAction(MementoAction):

    __slots__ = ('__src_row', '__src_parent', '__to_row', '__to_parent')

    def __init__(self, m_model, model, src_row, src_parent, to_row, to_parent):
        super().__init__(m_model, model)
        self.__src_row = src_row
        self.__src_parent = src_parent
        self.__to_row = to_row
        self.__to_parent = to_parent

    def __undo__(self):
        self._model.move(self.__to_row,
                         self.__to_parent,
                         self.__src_row,
                         self.__src_parent)

    def __redo__(self):
        self._model.move(self.__src_row,
                         self.__src_parent,
                         self.__to_row,
                         self.__to_parent)


    def log(self):
        return 'Move item'