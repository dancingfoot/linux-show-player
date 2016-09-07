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

from lisp.core.model import Model, ModelException


class ProxyModel(Model):
    """Model that act as a proxy to another model."""

    def __init__(self, model):
        super().__init__()
        self._model = None
        self.model = model

    def add(self, item):
        self._model.add(item)

    def remove(self, item):
        self._model.remove(item)

    def clear(self):
        self._model.clear()

    @property
    def model(self):
        return self._model

    @model.setter
    def model(self, model):
        if not isinstance(model, Model):
            raise TypeError('ProxyModel model must be a Model object, not {0}'
                            .format(model.__class__.__name__))

        if self._model is not None:
            self._model.item_added.disconnect(self._item_added)
            self._model.item_removed.disconnect(self._item_removed)
            self._model.cleared.disconnect(self._cleared)

        self._model = model
        self._model.item_added.connect(self._item_added)
        self._model.item_removed.connect(self._item_removed)
        self._model.cleared.connect(self._cleared)

    @abstractmethod
    def _item_added(self, item):
        pass

    @abstractmethod
    def _item_removed(self, item):
        pass

    @abstractmethod
    def _cleared(self):
        pass

    def __iter__(self):
        return self._model.__iter__()

    def __len__(self):
        return len(self._model)

    def __contains__(self, item):
        return item in self._model


class ReadOnlyProxyModel(ProxyModel):
    def add(self, item):
        raise ModelException('cannot add items into a read-only model')

    def remove(self, item):
        raise ModelException('cannot remove items from a read-only model')

    def clear(self):
        raise ModelException('cannot reset read-only model')
