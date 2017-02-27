# -*- coding: utf-8 -*-
#
# This file is part of Linux Show Player
#
# Copyright 2016-2017 Thomas Achtner <info@offtools.de>
#
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

# TODO: purge empty paths

from weakref import WeakSet


class MessageDispatcher:
    """
    class to filter and dispatch incoming messages from Midi, Osc and Keyboard

    nested dict holds message id and value masks as keys and store values or objects in a WeakSet,
    which can be used to execute commands or callbacks.

    incoming messages are described by two parts the a static part, the message id
    and a value mask, representing the arguments of the incoming message.
    if a incoming message fits description (message id and the value mask), the stored callback
    will be executed.

    osc: [message id: '/path/to/hell ii'] [value mask: (1,1)]
    midi: [message id: 'note_on'] [value mask: (0,0,64)]

    messages should be stored in settings as list of: message_id, *value_mask

    entries of a value masks can be masked with None. This means, that this values of the incoming message,
    will be ignored to identify the message or in other words, any value of the specific argument is possible.
    masked values are also forwarded as possible arguments to the callbacks.

    the messages and the value masks are stored in a tree like order:
    the most upper level of the dict contain the messages strings.
    for Midi: 'note_on', 'control_change', etc
    for OSC: '/path/to/something, ii'
    for Keyboard: 'Space'

    in the level under the messages the value masks are stored. To test the incoming message a tree search
    is executed:

    incoming message: 'note_on' (0,2,5)

    'note_on' - 0 - 1 - 1       ->  CMD: GO
        |           |   2       ->  CMD: PAUSE
        |           |
        |           2 - NONE    ->  CMD: GO_NUM(int)
        |
        |
    'Space'   ------------------->  CMD: GO

    for the incoming message the result of the tree search will be GO_NUM(5), start Cue 5
    """

    __value_type = WeakSet

    def __init__(self):
        self.__keys__ = {}

    @property
    def dict(self):
        """
        nested dictionary
        :rtype: dict
        """
        return self.__keys__

    @staticmethod
    def __set_mask(d, cmd, m):
        # actions with no arguments
        if len(m) > 1:
            for k, v in d.items():
                if not isinstance(v, dict):
                    # already found cmd, not going deeper
                    return False
            if not m[0] in d:
                d[m[0]] = {}
            else:
                if not isinstance(d[m[0]], dict):
                    d[m[0]] = {}
            return MessageDispatcher.__set_mask(d[m[0]], cmd, m[1:])
        elif len(m) == 1:
            if m[0] in d:
                if isinstance(d[m[0]], dict):
                    # already stores on a depper level
                    return False
                if isinstance(d[m[0]], MessageDispatcher.__value_type):
                    d[m[0]].add(cmd)
                    return True
            d[m[0]] = MessageDispatcher.__value_type({cmd})
            return True
        else:
            return False

    def add(self, message_id, cmd, mask=()):
        """

        :param message_id:
        :type message_id:
        :param cmd:
        :type cmd:
        :param mask:
        :type mask:
        :return:
        :rtype: bool
        """
        if message_id not in self.__keys__:
            self.__keys__[message_id] = {}
        if not mask:
            self.__keys__[message_id] = cmd
            return True
        else:
            return MessageDispatcher.__set_mask(self.__keys__[message_id], cmd, mask)

    @staticmethod
    def __item(d, m):
        if not d or not m:
            return
        mask = []
        for i in range(len(m)):
            if m[i] in d or None in d:
                mask.append(m[i] if m[i] in d else None)
                d = d.get(m[i] if m[i] in d else None, None)
                if not isinstance(d, dict):
                    return d, tuple(mask)
            else:
                return None, None
        else:
            return None, None

    def item(self, message_id, mask=()):
        """
        returns first occurrence of (value, mask) under the given mask,
        if value is stored under a shorter mask as the given one,
        this value and its mask is returned
        :param message_id:
        :type message_id:
        :param mask:
        :type mask:
        :return: value, tuple(mask)
        :rtype: value, tuple
        """
        if message_id in self.__keys__:
            if not mask:
                if not isinstance(self.__keys__.get(message_id, None), dict):
                    return self.__keys__.get(message_id, None), mask
                else:
                    return None, mask
            else:
                return MessageDispatcher.__item(self.__keys__[message_id], mask)
        else:
            return None, mask

    @staticmethod
    def __size(d, m):
        if not d or not m:
            return
        for i in range(len(m)):
            if m[i] in d:
                d = d.get(m[i], None)
                if not isinstance(d, dict):
                    return len(d)
            else:
                return 0
        else:
            return len(d)

    def size(self, message_id, mask=()):
        """
        return number of items stored under given mask
        :param message_id:
        :type message_id:
        :param mask: value mask as tuple of integers or None
        :type mask: tuple
        :return: number of items
        :rtype: int
        """
        if message_id in self.__keys__:
            if not mask:
                v = self.__keys__.get(message_id)
                if isinstance(v, dict):
                    return len(v)
                else:
                    return 1
            else:
                return MessageDispatcher.__size(self.__keys__[message_id], mask)
        return 0

    def __remove_mask(d, m):
        if isinstance(d, dict):
            if len(m) > 1:
                if m[0] in d:
                    return MessageDispatcher.__remove_mask(d.get(m[0]), m[1:])
            else:
                if len(m) and m[0] in d:
                    return d.pop(m[0])
                else:
                    return None

    def remove(self, message_id, mask=None):
        """
        dump remove method, doesn't check
        :param message_id: message_id e.g. 'note_on', 'Space' '/lisp/lisp/go, ii'
        :type message_id: str
        :param mask: value mask as tuple of integers or None
        :type mask: tuple
        :return: removed part of the MessageDispatcher (a value or dict)
        :rtype: stored value or dict
        """
        if message_id in self.__keys__:
            if not mask:
                return self.__keys__.pop(message_id)
            else:
                return MessageDispatcher.__remove_mask(self.__keys__[message_id], mask)

    def clear(self):
        self.__keys__.clear()

    @staticmethod
    def filter(mask, *args):
        args = list(args)
        for i in range(len(mask)):
            if mask[i] is not None:
                args.pop(0)
        return args


if __name__ == "__main__":
    class Types:
        def __init__(self, cmd):
            self.cmd = cmd

    d = {
        'GO': Types('GO'),
        'PAUSE': Types('PAUSE'),
        'STOP': Types('STOP'),
        'INTERRUPT': Types('INTERRUPT'),
        'NEXT': Types('NEXT'),
        'PREV': Types('PREV')
    }


    keys = MessageDispatcher()

    keys.add('note_on', d['GO'],        (0, 1, None))
    keys.add('note_on', d['PAUSE'],     (0, 1, 2))
    keys.add('note_on', d['STOP'],   (0, 1, 3))
    keys.add('note_on', d['INTERRUPT'], (1, 3, 1))
    keys.add('note_on', d['NEXT'], (1, 3, 2))
    keys.add('note_on', d['STOP'],      (1, 3, 1))
    keys.add('note_on', d['GO'],      (1, 3, 1))
    # keys.add('/lisp/list/go i', 'GO', (1,))
    # keys.add('/lisp/list/stop i', 'STOP', (1,))
    # keys.add("'/lisp/list/pause' 'i'", 'PAUSE', (None,))
    # keys.add('Space', 'GO')
    print("Stored Messages: ", keys.dict)

    print("Value OSC PAUSE      ", *keys.item("'/lisp/list/pause' 'i'", (1,)))

    print("Value (0,1,8)      ", *keys.item('note_on', (0, 1, 8)))
    print("Value (0,1,None,1) ", *keys.item('note_on', (0, 1, None, 1)))
    print("Value (0,1,1)      ", *keys.item('note_on', (0, 1, 1)))
    print("Value (1,3,1)      ", *keys.item('note_on', (1,3,1)))
    print("Value Space Go     ", *keys.item('Space'))
    print("Value empty        ", *keys.item('note_on', (0,5,1)))
    print("size note_on       ", keys.size('note_on'))
    print("size GO (0,1,None) ", keys.size('note_on', (0, 1, 2)))
    print("size (0,1)         ", keys.size('note_on', (0, 1)))
    print("size (0)           ", keys.size('note_on', (0,)))
    print("size ()            ", keys.size('note_on', ()))
    # as size is using get_item - size of parent is returned ???
    print("size (0,1,None,1)  ", keys.size('note_on', (0, 1, None, 1)))
    print("size (1,3,1)       ", keys.size('note_on', (1,3,1)))
    print("dict: ", keys.dict)

    print("size ", keys.size('note_on', (1,)))

    print(keys.remove('note_on', (0,2,1)))
    print("end remove: ", keys.dict)

    print("filter: ", keys.filter((0,3,None), 0, 3, 4, 5))

    print("items: ", [i.cmd for i in keys.item('note_on', (1, 3, 1))[0]], keys.size('note_on', (1,3,1)))
    d.pop('STOP')
    print("items: ", [i.cmd for i in keys.item('note_on', (1, 3, 1))[0]], keys.size('note_on', (1,3,1)))
