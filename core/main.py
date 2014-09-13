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

import os
import traceback
import threading
import xbmc
import xbmcgui
import utils
import settings
from utils import escape_param, log, notify
from itertools import repeat
from watchdog.events import FileSystemEventHandler
from emitters import MultiEmitterObserver


class XBMCIF(threading.Thread):
    """Wrapper around the builtins to make sure no two commands a executed at
    the same time (xbmc will cancel previous if not finished)
    """

    def __init__(self):
        threading.Thread.__init__(self)
        self._stop_event = threading.Event()
        self._cmd_queue = utils.OrderedSetQueue()

    def stop(self):
        self._stop_event.set()
        self._cmd_queue.put(None)  # unblock get in run

    def queue_scan(self, library, path=None):
        if path:
            cmd = "UpdateLibrary(%s,%s)" % (library, escape_param(path))
        else:
            cmd = "UpdateLibrary(%s)" % library
        self._cmd_queue.put(cmd)

    def queue_clean(self, library):
        self._cmd_queue.put("CleanLibrary(%s)" % library)

    def run(self):
        player = xbmc.Player()
        while True:
            cmd = self._cmd_queue.get()
            if self._stop_event.is_set():
                return
            while player.isPlaying() and not self._stop_event.is_set():
                xbmc.sleep(1000)
            if self._stop_event.is_set():
                return

            # TODO: duplicate commands can be cleared from the queue here
            log("[xbmcif] executing builtin: '%s'" % cmd)
            xbmc.executebuiltin(cmd)

            # wait for scan to start. we need a timeout or else we a screwed
            # if we missed it.
            # TODO: replace this crap with Monitor callbacks in Helix
            log("[xbmcif] waiting for scan/clean start..")
            timeout = 3000
            while not xbmc.getCondVisibility('Library.IsScanning') \
                    and not self._stop_event.is_set():
                xbmc.sleep(100)
                timeout -= 100
                if timeout <= 0:
                    log("[xbmcif] wait for scan/clean timed out.")
                    break
            log("[xbmcif] scan/clean started.")
            log("[xbmcif] waiting for scan/clean end..")

            # wait for scan to end
            while xbmc.getCondVisibility('Library.IsScanning') \
                    and not self._stop_event.is_set():
                xbmc.sleep(100)
            log("[xbmcif] scan/clean ended.")


class EventHandler(FileSystemEventHandler):
    """
    Handles raw incoming events for single root path and library,
    and queues scan/clean commands to the xbmcif singleton.
    """

    def __init__(self, library, path, xbmcif):
        FileSystemEventHandler.__init__(self)
        self.library = library
        self.path = path
        self.xbmcif = xbmcif
        self.supported_media = '|' + xbmc.getSupportedMedia(library) + '|'

    def on_created(self, event):
        if not self._can_skip(event, event.src_path):
            # TODO: remove this hack when fixed in xbmc
            if settings.FORCE_GLOBAL_SCAN and self.library == 'video':
                self.xbmcif.queue_scan(self.library)
            else:
                self.xbmcif.queue_scan(self.library, self.path)

    def on_deleted(self, event):
        if settings.CLEAN and not self._can_skip(event, event.src_path):
            self.xbmcif.queue_clean(self.library)

    def on_moved(self, event):
        self.on_deleted(event)
        if not self._can_skip(event, event.dest_path):
            # TODO: remove this hack when fixed in xbmc
            if settings.FORCE_GLOBAL_SCAN and self.library == 'video':
                self.xbmcif.queue_scan(self.library)
            else:
                self.xbmcif.queue_scan(self.library, self.path)

    def on_any_event(self, event):
        log("<%s> <%s>" % (event.event_type, event.src_path))

    @staticmethod
    def _is_hidden(path):
        dirs = path.split(os.sep)
        for d in dirs:
            if d.startswith('.') or d.startswith('_UNPACK'):
                return True
        return False

    def _can_skip(self, event, path):
        if not path:
            return False
        relpath = path[len(self.path):] if path.startswith(self.path) else path
        if self._is_hidden(relpath):
            log("skipping <%s> <%s>" % (event.event_type, path))
            return True
        if not event.is_directory:
            _, ext = os.path.splitext(path)
            ext = ext.lower()
            if self.supported_media.find('|%s|' % ext) == -1:
                log("skipping <%s> <%s>" % (event.event_type, path))
                return True
        return False


def main():
    progress = xbmcgui.DialogProgressBG()
    progress.create("Watchdog starting. Please wait...")

    if settings.STARTUP_DELAY > 0:
        log("waiting for user delay of %d seconds" % settings.STARTUP_DELAY)
        msg = "Delaying startup by %d seconds."
        progress.update(0, message=msg % settings.STARTUP_DELAY)
        xbmc.sleep(settings.STARTUP_DELAY * 1000)
        if xbmc.abortRequested:
            return

    sources = []
    video_sources = settings.VIDEO_SOURCES
    sources.extend(zip(repeat('video'), video_sources))
    log("video sources %s" % video_sources)

    music_sources = settings.MUSIC_SOURCES
    sources.extend(zip(repeat('music'), music_sources))
    log("music sources %s" % music_sources)

    if not sources:
        notify("Nothing to watch", "No media source found")

    xbmcif = XBMCIF()
    observer = MultiEmitterObserver()
    observer.start()  # start so emitters are started on schedule

    for i, (libtype, path) in enumerate(sources):
        progress.update((i+1)/len(sources)*100, message="Setting up %s" % path)
        try:
            fs_path, emitter_cls = utils.select_emitter(path)
        except IOError:
            log("not watching <%s>. does not exist" % path)
            notify("Could not find path", path)
            continue
        eh = EventHandler(libtype, path, xbmcif)
        try:
            observer.schedule(eh, path=fs_path, emitter_cls=emitter_cls)
            log("watching <%s> using %s" % (path, emitter_cls))
        except Exception:
            traceback.print_exc()
            log("failed to watch <%s>" % path)
            notify("Failed to watch %s" % path, "See log for details")

    xbmcif.start()
    progress.close()
    log("initialization done")

    while not xbmc.abortRequested:
        xbmc.sleep(100)

    log("stopping..")
    observer.stop()
    xbmcif.stop()
    observer.join()
    xbmcif.join()

if __name__ == "__main__":
    main()
