import os, sys, time, math
import xbmc, xbmcaddon
from pyinotify import *
from threading import Thread
from autoexecHandler import AutoexecHandler

ADDON_ID      = "script.autoupdater"
FILENAME_THIS = "default.py"

SETTINGS      = xbmcaddon.Addon(id=ADDON_ID)
DELAY         = math.fabs(int(SETTINGS.getSetting("delay"))) #delay before executing the update function
CLEAN         = SETTINGS.getSetting("clean")
AUTOEXEC      = SETTINGS.getSetting("autoexec")

PATHS = []
for i in range(0, 4):
	p = SETTINGS.getSetting("path" + str(i))
	if not("" == p.strip()):
		PATHS.append(xbmc.translatePath(p))

SETTINGS = None

MASK = EventsCodes.IN_CREATE | EventsCodes.IN_DELETE | EventsCodes.IN_MOVED_TO | EventsCodes.IN_MOVED_FROM |EventsCodes.IN_MOVE_SELF

	
class Worker(Thread):
	def __init__(self):
		Thread.__init__(self)
		self.q1 = []
		self.q2 = []
		
	def queue1(self, f, b):
		self.q1.append((f,b))
		
	def queue2(self, f, b):
		self.q2.append((f,b))
		
	def run(self):
		time.sleep(DELAY)
		
		while (len(self.q1) > 0) or (len(self.q2) > 0):
			if len(self.q1) > 0:
				while len(self.q1) > 0:
					(f, b) = self.q1.pop()
				f()
				time.sleep(0.2) #Without this getCondVisibility(window) wont work. It returns false until gui is actually rendered
				while b():
					time.sleep(1)

			if len(self.q2) > 0:
				while len(self.q2) > 0:
					(f, b) = self.q2.pop()
				f()
				time.sleep(0.2)
				while b():
					time.sleep(1)

class Xbmc:
	def __init__(self):
		self.worker = Worker()
		self.worker.start()
		
	def __scanf(self):
		xbmc.executebuiltin("UpdateLibrary(video)")
	
	def __cleanf(self):
		xbmc.executebuiltin("CleanLibrary(video)")
	
	def __isScanningf(self):
		return xbmc.getCondVisibility('Library.IsScanning')
	
	def __isCleaningf(self):
		return xbmc.getCondVisibility('Window.IsActive(10101)')
	
	def scan(self):
		if(self.worker.isAlive()):
			self.worker.queue1( self.__scanf, self.__isScanningf )
		else:
			self.worker = Worker()
			self.worker.queue1( self.__scanf, self.__isScanningf )
			self.worker.start()
			
	def clean(self):
		if CLEAN:
			if(self.worker.isAlive()):
				self.worker.queue2( self.__cleanf, self.__isCleaningf )
			else:
				self.worker = Worker()
				self.worker.queue2( self.__cleanf, self.__isCleaningf )
				self.worker.start()

class ProcHandler(ProcessEvent):
	def __init__(self, wm, xbmch):
		self.wm = wm
		self.xbmch = xbmch
		
	def process_IN_CREATE(self, event):
		log(event)
		path = event.path + "/" + event.name
		if os.path.isdir(path) and len(os.listdir(path)) == 0:
			return
		self.xbmch.scan()

	def process_IN_DELETE(self, event):
		log(event)
		self.xbmch.clean()

	def process_IN_MOVE_SELF(self, event):
		log(event)
		if event.path.endswith("invalided-path"): #moved outside
			self.wm.rm_watch(event.wd, rec=True)
			
	def process_IN_IGNORED(self, event):
		log(event)

	def process_IN_MOVED_FROM(self, event):
		log(event)
		self.xbmch.clean()
		
	def process_IN_MOVED_TO(self, event):
		log(event)
		path = event.path + "/" + event.name
		if os.path.isdir(path) and len(os.listdir(path)) == 0:
			return 
		self.xbmch.scan()
		
def log(event):
	v = (event.event_name, event.is_dir, event.mask, event.name, event.path)
	print ADDON_ID + ": event_name: %s\t   is_dir: %s\t   mask: %s\t   name: %s\t   path: %s" % v

def main():
	aeh = AutoexecHandler()
	if AUTOEXEC:
		aeh.add(ADDON_ID, FILENAME_THIS)
	else:
		aeh.remove(ADDON_ID, FILENAME_THIS)
	aeh = None
	
	if len(PATHS) == 0: #nothing to watch
		return
	
	xbmch = Xbmc()
	wm = WatchManager()
	phandler = ProcHandler(wm, xbmch)
	notifier = ThreadedNotifier(wm, phandler)
	notifier.start()
	
	for p in PATHS:
		wm.add_watch(p, MASK, rec=True, auto_add=True)
	
	#keep self alive or else python will hang when exiting xbmc
	while True:
		time.sleep(1)
		
if ( __name__ == "__main__" ):
	main()
