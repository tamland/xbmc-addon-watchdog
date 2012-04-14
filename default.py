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
import simplejson
import xbmc
import xbmcaddon
import debugging
from time import sleep
from threading import Thread
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


ADDON    = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
CLEAN    = ADDON.getSetting("clean") in ["true", "True", "1"]
DELAY    = 1


class Worker(Thread):
  def __init__(self):
    Thread.__init__(self)
    self.scan = False
    self.clean = False
  
  def run(self):
    sleep(DELAY)
    while True:
      if self.clean:
        self.clean = False
        xbmc.log("%s cleaning library" % (ADDON_ID), xbmc.LOGDEBUG)
        xbmc.executebuiltin("CleanLibrary(video)")
        sleep(1) #give xbmc time to render
        while xbmc.getCondVisibility('Window.IsActive(10101)'):
          sleep(1)
      
      if self.scan:
        xbmc.log("%s scanning library" % (ADDON_ID), xbmc.LOGDEBUG)
        self.scan = False
        xbmc.executebuiltin("UpdateLibrary(video)")
        sleep(1)
        while xbmc.getCondVisibility('Library.IsScanning'):
          sleep(1)
      
      #done if no new requests since scan/clean was set to false
      if not(self.scan) and not(self.clean):
        return


class EventHandler(FileSystemEventHandler):
  def __init__(self):
    FileSystemEventHandler.__init__(self)
    self.worker = Worker()
  
  def _scan(self):
    self._on_worker('scan')
  
  def _clean(self):
    if CLEAN: self._on_worker('clean')
  
  def _on_worker(self, attr):
    if self.worker.isAlive():
      setattr(self.worker, attr, True)
    else:
      self.worker = Worker()
      setattr(self.worker, attr, True)
      self.worker.start()
  
  def on_created(self, event):
    self._scan()
  
  def on_deleted(self, event):
    self._clean()
  
  def on_moved(self, event):
    self._clean()
    self._scan()
  
  def on_any_event(self, event):
    xbmc.log("%s <%s> <%s>" % (ADDON_ID, str(event.event_type), str(event.src_path)), xbmc.LOGDEBUG)


def get_media_sources():
  query = '{"jsonrpc": "2.0", "method": "Files.GetSources", "params": {"media": "video"}, "id": 1}'
  result = xbmc.executeJSONRPC(query)
  json = simplejson.loads(result)
  if json.has_key('result'):
    if json['result'].has_key('sources'):
      return [ e['file'] for e in json['result']['sources'] ]
  return []


if __name__ == "__main__":
  event_handler = EventHandler()
  observer = Observer()
  
  xbmc.log("%s: using <%s>" % (ADDON_ID, debugging.get_observer_name()), xbmc.LOGDEBUG)
  
  dirs = get_media_sources()
  for item in dirs:
    if os.path.exists(item):
      xbmc.log("%s: watching <%s>" % (ADDON_ID, item), xbmc.LOGDEBUG)
      observer.schedule(event_handler, path=item, recursive=True)
    else:
      xbmc.log("%s: not watching <%s>" % (ADDON_ID, item), xbmc.LOGDEBUG)
  
  observer.start()
  while (not xbmc.abortRequested):
    sleep(1)
  observer.stop()
  observer.join()

