'''
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
import os
import traceback
import threading
import pykka
import xbmc
import xbmcgui
import utils
import settings
from utils import escape_param, log, notify
from functools import partial
from itertools import repeat
from watchdog.events import FileSystemEventHandler

SUPPORTED_MEDIA = '|' + xbmc.getSupportedMedia('video') + \
                  '|' + xbmc.getSupportedMedia('music') + '|'


class XBMCActor(pykka.ThreadingActor):
    """ Messaging interface to xbmc's executebuiltin calls """

    @staticmethod
    def _xbmc_is_busy():
        xbmc.sleep(100) # visibility cant be immediately trusted. Give xbmc time to render
        return ((xbmc.Player().isPlaying() and settings.PAUSE_ON_PLAYBACK)
            or xbmc.getCondVisibility('Library.IsScanning')
            or xbmc.getCondVisibility('Window.IsActive(10101)'))

    def scan(self, library, path):
        """ Tell xbmc to scan. Returns immediately when scanning has started. """
        while self._xbmc_is_busy():
            pass
        log("scanning %s (%s)" % (path, library))
        if library == 'video' and settings.FORCE_GLOBAL_SCAN:
            xbmc.executebuiltin("UpdateLibrary(video)")
        else:
            xbmc.executebuiltin("UpdateLibrary(%s,%s)" % (library, escape_param(path)))

    def clean(self, library, path=None):
        """ Tell xbmc to clean. Returns immediately when scanning has started. """
        while self._xbmc_is_busy():
            pass
        log("cleaning %s library" % library)
        xbmc.executebuiltin("CleanLibrary(%s)" % library)


class EventQueue(pykka.ThreadingActor):
    """ Handles all raw incomming events for single root path and library. """
    def __init__(self, library, path, xbmc_actor):
        super(EventQueue, self).__init__()
        def ask(msg):
            if msg == 'scan':
                return xbmc_actor.scan(library, path).get()
            elif msg == 'clean':
                return xbmc_actor.clean(library, path).get()
        self.new_worker = partial(EventQueue.Worker, ask)
        self.worker = None

    def _notify_worker(self, attr):
        if not(self.worker) or not(self.worker.is_alive()):
            self.worker = self.new_worker()
            getattr(self.worker, attr).set()
            self.worker.start()
        else:
            getattr(self.worker, attr).set()

    def scan(self):
        self._notify_worker('scan')

    def clean(self):
        self._notify_worker('clean')

    def on_stop(self):
        if self.worker is not None:
            self.worker.abort.set()
            self.worker.join()

    class Worker(threading.Thread):
        """ Sends messages to XBMCActor and waits for reply. """
        def __init__(self, ask):
            super(EventQueue.Worker, self).__init__()
            self.ask = ask
            self.scan = threading.Event()
            self.clean = threading.Event()
            self.abort = threading.Event()

        def run(self):
            if self.abort.wait(settings.SCAN_DELAY):
                return
            while True:
                if self.clean.is_set():
                    self.ask('clean')
                    self.clean.clear()
                if self.scan.is_set():
                    self.ask('scan')
                    self.scan.clear()
                if not self.scan.is_set() and not self.clean.is_set():
                    return


class EventHandler(FileSystemEventHandler):
    def __init__(self, event_queue):
        super(EventHandler, self).__init__()
        self.event_queue = event_queue

    def on_created(self, event):
        if not self._can_skip(event, event.src_path):
            self.event_queue.scan()

    def on_deleted(self, event):
        if settings.CLEAN and not self._can_skip(event, event.src_path):
            self.event_queue.clean()

    def on_moved(self, event):
        if settings.CLEAN and not self._can_skip(event, event.src_path):
            self.event_queue.clean()
        if not self._can_skip(event, event.dest_path):
            self.event_queue.scan()

    def on_any_event(self, event):
        log("<%s> <%s>" % (event.event_type, event.src_path))

    @staticmethod
    def _can_skip(event, path):
        if not event.is_directory and path:
            _, ext = os.path.splitext(path)
            ext = ext.lower()
            if SUPPORTED_MEDIA.find('|%s|' % ext) == -1:
                log("skipping <%s> <%s>" % (event.event_type, path))
                return True
        return False


def main():
    progress = xbmcgui.DialogProgressBG()
    progress.create("Watchdog starting. Please wait...")
    sources = []
    if settings.WATCH_VIDEO:
        video_sources = utils.get_media_sources('video')
        sources.extend(zip(repeat('video'), video_sources))
        log("video sources %s" % video_sources)
    if settings.WATCH_MUSIC:
        music_sources = utils.get_media_sources('music')
        sources.extend(zip(repeat('music'), music_sources))
        log("music sources %s" % music_sources)

    xbmc_actor = XBMCActor.start().proxy()
    threads = []
    for i, (libtype, path) in enumerate(sources):
        progress.update((i+1)/len(sources)*100, message="Setting up %s" % path)
        try:
            fs_path, observer = utils.select_observer(path)
            event_queue = EventQueue.start(libtype, path, xbmc_actor).proxy()
            event_handler = EventHandler(event_queue)
            observer.schedule(event_handler, path=fs_path, recursive=settings.RECURSIVE)
            if not observer.is_alive():
                observer.start()
                threads.append(observer)
            threads.append(event_queue)
            log("watching <%s> using %s" % (path, observer))
        except IOError:
            log("not watching <%s>. does not exist" % path)
            notify("Path does not exist", path)
        except Exception:
            traceback.print_exc()
            log("failed to watch <%s>" % path)
            notify("Failed to watch", path)
    progress.close()

    while not xbmc.abortRequested:
        xbmc.sleep(100)
    for th in threads:
        try:
            th.stop()
        except Exception:
            traceback.print_exc()
    xbmc_actor.stop()

if __name__ == "__main__":
    main()
