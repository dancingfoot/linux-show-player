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

import time
from threading import Event

from lisp.core.signal import Signal


class RWait:
    """Provide a reasumable-wait mechanism."""

    def __init__(self, timeout):
        self._timeout = timeout
        self._elapsed = 0
        self._start_time = 0
        self._is_waiting = Event()
        self._wait = Event()

        self.start = Signal()
        self.ended = Signal()
        self.paused = Signal()

    def wait(self):
        # Clear the events
        self._wait.clear()
        self._is_waiting.clear()
        # Set the start-time
        self._start_time = time.time() - self._elapsed

        # Emit a signal and wait
        self.start.emit()
        ended = not self._wait.wait(self._timeout - self._elapsed)

        # Notify that we are not waiting anymore
        self._is_waiting.set()
        if ended:
            self._elapsed = 0
            self.ended.emit()

        return ended

    def interrupt(self):
        self._elapsed = 0
        self._wait.set()
        self._is_waiting.wait()
        self.ended.emit()

    def pause(self):
        if not self._wait.is_set():
            self._elapsed = time.time() - self._start_time
            self._wait.set()
            self._is_waiting.wait()
            self.paused.emit()

    def current_time(self):
        if self._is_waiting.is_set():
            return self._elapsed

        return time.time() - self._start_time
