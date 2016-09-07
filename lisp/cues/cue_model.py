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

from lisp.core.model import Model
from lisp.cues.cue import Cue


class CueModel(Model):
    """Model to store cue(s) by cue_id.

    Internally use a python dictionary, so get/set/del methods are O(1).
    """

    def __init__(self):
        super().__init__()
        self.__cues = {}

    def add(self, cue):
        if cue.id in self.__cues:
            raise ValueError('the cue is already in the layout')

        self.__cues[cue.id] = cue
        self.item_added.emit(cue)

    def remove(self, cue):
        self.pop(cue.id)

    def pop(self, cue_id):
        cue = self.__cues.pop(cue_id)
        self.item_removed.emit(cue)

        return cue

    def get(self, cue_id, default=None):
        return self.__cues.get(cue_id, default)

    def items(self):
        """Return a view on model items (cue_id, cue)."""
        return self.__cues.items()

    def keys(self):
        """Return a view on of model keys (cue_id)."""
        return self.__cues.keys()

    def clear(self):
        self.__cues.clear()
        self.cleared.emit()

    def filter(self, cue_class=Cue):
        """Filter cue by class (subclasses are included)."""
        for cue in self.__cues.values():
            if isinstance(cue, cue_class):
                yield cue

    def __iter__(self):
        return self.__cues.values().__iter__()

    def __len__(self):
        return len(self.__cues)

    def __contains__(self, cue):
        return cue.id in self.__cues
