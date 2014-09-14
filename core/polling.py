# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Thomas Amland
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import xbmc
from functools import partial
from watchdog.observers.api import EventEmitter, BaseObserver
from watchdog.events import DirDeletedEvent, DirCreatedEvent
from utils import log
import settings


def _paused():
    return xbmc.Player().isPlaying() and settings.PAUSE_ON_PLAYBACK


def hidden(path):
    return path.startswith('.') or path.startswith('_UNPACK')


class MtimeSnapshot(object):
    def __init__(self, root, get_mtime):
        self._root = root
        self._mtime = get_mtime(root)

    def diff(self, other):
        modified = [self._root] if self._mtime != other._mtime else []
        return [], [], modified


class FileSnapshot(object):
    def __init__(self, root, walker):
        self._files = set()
        for dirs, files in walker(root):
            self._files.update(files)

    def diff(self, other):
        created = other._files - self._files
        deleted = self._files - other._files
        return created, deleted, []


class PollerBase(EventEmitter):
    make_snapshot = None
    interval = -1

    def __init__(self, event_queue, watch, timeout=1):
        EventEmitter.__init__(self, event_queue, watch, timeout)
        self._snapshot = None

    def queue_events(self, timeout):
        if self._snapshot is None:
            self._snapshot = self.make_snapshot(self.watch.path)
        if self.stopped_event.wait(timeout):
            return
        if not _paused():
            new_snapshot = self.make_snapshot(self.watch.path)
            created, deleted, modified = self._snapshot.diff(new_snapshot)
            self._snapshot = new_snapshot

            if deleted:
                log("poller: delete event appeared in %s" % deleted)
            if created:
                log("poller: create event appeared in %s" % created)
            if modified and not(deleted or created):
                log("poller: modify event appeared in %s" % modified)

            if modified or deleted:
                self.queue_event(DirDeletedEvent(self.watch.path + '*'))
            if modified or created:
                self.queue_event(DirCreatedEvent(self.watch.path + '*'))
