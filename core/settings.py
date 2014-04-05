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
import xbmcaddon

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
CLEAN = ADDON.getSetting('clean') == 'true'
POLLING = int(ADDON.getSetting('method'))
POLLING_METHOD = int(ADDON.getSetting('pollingmethod'))
POLLING_INTERVAL = int("0"+ADDON.getSetting('pollinginterval')) or 4
RECURSIVE = not (ADDON.getSetting('nonrecursive') == 'true') or not POLLING
WATCH_VIDEO = ADDON.getSetting('watchvideo') == 'true'
WATCH_MUSIC = ADDON.getSetting('watchmusic') == 'true'
SCAN_DELAY = int("0"+ADDON.getSetting('delay')) or 1
PAUSE_ON_PLAYBACK = ADDON.getSetting('pauseonplayback') == 'true'
FORCE_GLOBAL_SCAN = ADDON.getSetting('forceglobalscan') == 'true'
SHOW_NOTIFICATIONS = ADDON.getSetting('notifications') == 'true'
