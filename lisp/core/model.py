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
from collections.abc import Sized, Iterable, Container

from lisp.core.signal import Signal


class Model(Sized, Iterable, Container):
    """A model is a data container that provide signal to observe changes.

    Subclasses can provide:
     * get() get an item by index/key
     * pop() remove an return an item by index/key
    """

    def __init__(self):
        self.item_added = Signal()
        self.item_removed = Signal()
        self.cleared = Signal()

    @abstractmethod
    def add(self, item):
        pass

    @abstractmethod
    def remove(self, item):
        pass

    @abstractmethod
    def clear(self):
        pass


class ModelException(Exception):
    """Exception for illegal operations on models"""
