# -*- coding: utf-8 -*-
#
# This file is part of Linux Show Player
#
# Copyright 2012-2016 Francesco Ceruti <ceppofrancy@gmail.com>
# Copyright 2016 Thomas Achtner <info@offtools.de>
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


import collections
from weakref import WeakSet, finalize

from lisp.ui import elogging


class Handler:

    def execute(self, *args):
        """base class for objects added to DispatchDict"""

    @property
    def debug(self):
        """"""
        return ''


class DispatchDict(collections.UserDict):
    def __init__(self, value=None, parent=None):
        super().__init__()

        if not (parent is None or isinstance(parent, DispatchDict)):
            raise TypeError("parent needs to be of type DispatchDict")

        self.__parent = parent
        self.__type = WeakSet
        self.__handler = self.__type()
        if value:
            if not isinstance(value, Handler):
                raise TypeError("values not a instance of class Handler")
            self.__handler.add(value)

    def __setitem__(self, key, value):
        if key in self:
            self[key].__value = self.__type()
            self[key].add(value)
        else:
            self.data[key] = DispatchDict(value=value, parent=self)

    @property
    def parent(self):
        return self.__parent

    def child(self, index, value=None):
        """
        sets child value by given index, if index does not exists, it will be created
        returns child by given index
        :param index: index key
        :type index: int
        :param value: value
        :type value: object
        :param parent: parent
        :type parent: MaskDict, None
        :return: child
        :rtype: DispatchDict
        """
        if index not in self:
            self.data[index] = DispatchDict(value=value, parent=self)
        return self[index]

    def __finalize(self, message_id, mask):
        print("finalizer: ", self.__cleanup_mask(message_id, mask))

    def add(self, msg_id, handler, mask=()):
        """
        adds a weakref of the value object (or handler) under the given mask
        the object  needs to be hold elsewhere (weakref)
        if the original object is deleted, it will be removed from the from the dict
        and the dict does a garbage collect of empty mask paths
        :param msg_id: message id
        :type msg_id: str
        :param handler: an object or handler
        :type handler: object
        :param mask: mask, tuple of message arguments (None means any)
        :type mask: tuple
        """
        if not isinstance(handler, Handler):
            raise TypeError("values not a instance of class Handler")

        m_dict = self
        for idx in (msg_id, *mask):
            m_dict = m_dict.child(idx)
        if handler not in m_dict.__handler:
            finalize(handler, self.__finalize, msg_id, mask)
        m_dict.__handler.add(handler)

    def get_handler(self, msg_id, *args):
        """
        returns a generator with containing tuples of (values, mask) found with the given arguments
        :param msg_id: message id (e.g.: 'note_on', '/osc/path, i', 'Space' ...)
        :type msg_id: str
        :param args: arguments
        :type args: tuple
        :return: generator ( (handler, (mask)), ...)
        :rtype: generator
        """
        m_dict = self
        path = []
        for idx in (msg_id, *args):
            if idx in m_dict:
                m_dict = m_dict[idx]
                path.append(idx)
                if len(m_dict.__handler):
                    yield m_dict.__handler, tuple(path[1:])
            elif None in m_dict:
                m_dict = m_dict[None]
                path.append(None)
                if len(m_dict.__handler):
                    yield m_dict.__handler, tuple(path[1:])
            else:
                break

    def size(self, msg_id, mask=()):
        """
        searches for mask and returns size of their values
        :param msg_id: message id
        :type msg_id: str
        :param mask: returns size of stored values or -1 if mask or msg_id isn't valid
        :type mask: tuple
        :rtype: int
        """
        m_dict = self
        for idx in (msg_id, *mask):
            if idx in m_dict:
                m_dict = m_dict[idx]
            else:
                return -1
        return len(m_dict.__handler)

    def __cleanup_mask(self, msg_id, mask=()):
        """
        garbage collect empty mask path, after an object is deleted
        """
        m_dict = self
        path = [msg_id, *mask]

        print("__cleanup_mask: ", msg_id, mask)

        # get mask entry
        for idx in path:
            if idx in m_dict:
                m_dict = m_dict[idx]
            else:
                # mask not found
                return False

        while m_dict.parent:
            m_dict = m_dict.parent
            idx = path.pop()
            if not len(m_dict[idx].__handler) and not len(m_dict[idx]):
                m_dict.pop(idx)
                return True
            else:
                return True

    @staticmethod
    def filter(mask, *args):
        """
        helper method, filters arguments list against a mask
        all arguments not None are removed
        :param mask: mask
        :type mask: tuple
        :param args: *args
        :type args: *object
        :return: filtered args
        :rtype: tuple
        """

        flt = list(args)
        for i in range(len(mask)):
            if mask[i] is not None:
                flt.pop(0)
        return flt

    def debug(self):
        def rec(m_dict, path=[]):
            for idx in m_dict.keys():
                child = [*path, idx]
                if len(m_dict[idx].__handler):
                    elogging.debug("Handler: {0} {1} {2}".format(child, '\t\t', *[v.debug for v in m_dict[idx].__handler]))
                rec(m_dict[idx], child)

        rec(self)