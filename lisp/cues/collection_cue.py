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
from lisp.application import Application

from lisp.core.has_properties import Property
from lisp.cues.cue import Cue


class CollectionCue(Cue):
    children = Property(default=[])

    def __iter__(self):
        for child in self.children:
            child = Application().cue_model.get(child)
            if child is not None:
                yield child

    def __start__(self):
        for child_cue in self:
            child_cue.start()

    def __stop__(self):
        for child_cue in self:
            child_cue.stop()

    def __pause__(self):
        for child_cue in self:
            child_cue.pause()
