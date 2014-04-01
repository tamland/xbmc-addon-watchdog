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
import re
import os
import xbmc
import xbmcaddon
import xbmcvfs
import simplejson as json
from urllib import unquote
import settings


def log(msg):
    xbmc.log("%s: %s" % (settings.ADDON_ID, msg), xbmc.LOGDEBUG)


def escape_param(s):
    escaped = s.replace('\\', '\\\\').replace('"', '\\"')
    return '"' + escaped + '"'


def notify(msg1, msg2):
    if settings.SHOW_NOTIFICATIONS:
        xbmc.executebuiltin("XBMC.Notification(Watchdog: %s,%s)" % (msg1, escape_param(msg2)))


def rpc(method, **params):
    params = json.dumps(params)
    query = '{"jsonrpc": "2.0", "method": "%s", "params": %s, "id": 1}' % (method, params)
    return json.loads(xbmc.executeJSONRPC(query))


def select_observer(path):
    import observers
    if os.path.exists(path): #path from xbmc appears to always be utf-8 so if it contains non-ascii and os is not utf-8, this will fail
        if settings.POLLING:
            return observers.local_full()
        return observers.auto()
    elif re.match("^[A-Za-z]+://", path):
        if xbmcvfs.exists(path):
            observer_cls = [observers.xbmc_depth_1, observers.xbmc_depth_2,
                            observers.xbmc_full][settings.POLLING_METHOD]
            return observer_cls(settings.POLLING_INTERVAL)
    return None


def get_media_sources(media_type):
    response = rpc("Files.GetSources", media=media_type)
    ret = []
    if response.has_key('result'):
        if response['result'].has_key('sources'):
            paths = [e['file'] for e in response['result']['sources']]
            for path in paths:
                #split and decode multipaths
                if path.startswith("multipath://"):
                    for e in path.split("multipath://")[1].split('/'):
                        if e != "":
                            ret.append(unquote(e).encode('utf-8'))
                else:
                    ret.append(path.encode('utf-8'))
    return ret
