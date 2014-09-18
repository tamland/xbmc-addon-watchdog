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

from __future__ import unicode_literals

import sys
import xbmc
import xbmcgui
import simplejson as json
from urllib import unquote
from Queue import Queue


def log(msg):
    import settings
    xbmc.log((settings.ADDON_ID + ": " + msg).encode('utf-8', 'replace'), xbmc.LOGDEBUG)


def encode_path(path):
    """os.path does not handle unicode properly, i.e. when locale is C, file
    system encoding is assumed to be ascii. """
    if sys.platform.startswith('win'):
        return path
    return path.encode('utf-8')


def decode_path(path):
    if sys.platform.startswith('win'):
        return path
    return path.decode('utf-8')


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
    params = json.dumps(params, encoding='utf-8')
    query = b'{"jsonrpc": "2.0", "method": "%s", "params": %s, "id": 1}' % (method, params)
    return json.loads(xbmc.executeJSONRPC(query), encoding='utf-8')


def get_media_sources(media_type):
    response = rpc('Files.GetSources', media=media_type)
    paths = [s['file'] for s in response.get('result', {}).get('sources', [])]

    ret = []
    for path in paths:
        #split and decode multipaths
        if path.startswith("multipath://"):
            for e in path.split("multipath://")[1].split('/'):
                if e != "":
                    ret.append(unquote(e))
        elif not path.startswith("upnp://"):
            ret.append(path)
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
