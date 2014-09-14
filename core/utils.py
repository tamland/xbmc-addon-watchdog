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
import xbmcgui
import simplejson as json
from urllib import unquote
from Queue import Queue


def log(msg):
    import settings
    xbmc.log("%s: %s" % (settings.ADDON_ID, msg), xbmc.LOGDEBUG)


def escape_param(s):
    escaped = s.replace('\\', '\\\\').replace('"', '\\"')
    return '"' + escaped + '"'


def notify(msg1, msg2):
    import settings
    if settings.SHOW_NOTIFICATIONS:
        dialog = xbmcgui.Dialog()
        dialog.notification("Watchdog: %s" % msg1, msg2,
                            xbmcgui.NOTIFICATION_WARNING, 2000)


def rpc(method, **params):
    params = json.dumps(params)
    query = '{"jsonrpc": "2.0", "method": "%s", "params": %s, "id": 1}' % (method, params)
    return json.loads(xbmc.executeJSONRPC(query))


def get_media_sources(media_type):
    response = rpc('Files.GetSources', media=media_type)
    paths = [s['file'] for s in response.get('result', {}).get('sources', [])]

    ret = []
    for path in paths:
        #split and decode multipaths
        if path.startswith("multipath://"):
            for e in path.split("multipath://")[1].split('/'):
                if e != "":
                    ret.append(unquote(e).encode('utf-8'))
        elif not path.startswith("upnp://"):
            ret.append(path.encode('utf-8'))
    return ret


class OrderedSetQueue(Queue):
    """Queue with no repetition."""

    def _init(self, maxsize):
        self.queue = []

    def _qsize(self, len=len):
        return len(self.queue)

    def _put(self, item):
        if item not in self.queue:
            self.queue.append(item)

    def _get(self):
        return self.queue.pop()
