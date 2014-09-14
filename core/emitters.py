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

from watchdog.observers.api import BaseObserver
from watchdog.observers.api import ObservedWatch
from polling_local import LocalPoller
from polling_xbmc import XBMCVFSPoller, XBMCVFSPollerNonRecursive

__all__ = ['LocalPoller', 'XBMCVFSPoller', 'XBMCVFSPollerNonRecursive',
           'NativeEmitter', 'MultiEmitterObserver']

try:
    from watchdog.observers.inotify import InotifyEmitter as NativeEmitter
except:
    try:
        from watchdog.observers.kqueue import KqueueEmitter as NativeEmitter
    except:
        try:
            from watchdog.observers.read_directory_changes import WindowsApiEmitter as NativeEmitter
        except:
            NativeEmitter = LocalPoller


class MultiEmitterObserver(BaseObserver):
    def __init__(self):
        BaseObserver.__init__(self, None)

    def schedule(self, event_handler, path, emitter_cls=None):
        with self._lock:
            watch = ObservedWatch(path, True)
            emitter = emitter_cls(self.event_queue, watch, self.timeout)
            if self.is_alive():
                emitter.start()
            self._add_handler_for_watch(event_handler, watch)
            self._add_emitter(emitter)
            self._watches.add(watch)
            return watch