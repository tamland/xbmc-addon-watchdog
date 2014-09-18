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

import xbmcvfs
import settings
from polling import PollerBase, FileSnapshot, MtimeSnapshot, hidden


def _walk(path):
    dirs, files = xbmcvfs.listdir(path)
    dirs = [path + '/' + _.decode('utf-8') for _ in dirs if not hidden(_)]
    files = [path + '/' + _.decode('utf-8') for _ in files if not hidden(_)]
    yield dirs, files
    for d in dirs:
        for dirs, files in _walk(d):
            yield dirs, files


def _get_mtime(path):
    return xbmcvfs.Stat(path).st_mtime()


class VFSPoller(PollerBase):
    polling_interval = settings.POLLING_INTERVAL
    recursive = settings.RECURSIVE

    def _take_snapshot(self):
        if self.recursive:
            return FileSnapshot(self.watch.path, _walk)
        return MtimeSnapshot(self.watch.path, _get_mtime)

    def is_offline(self):
        # Since path is always a media source, it's unlikely the user would
        # delete it. Assume it's offline if it doesn't exist.
        return not xbmcvfs.exists(self.watch.path)
