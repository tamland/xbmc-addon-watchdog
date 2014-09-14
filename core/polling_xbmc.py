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
import xbmcvfs
import settings
from functools import partial
from polling import PollerBase, FileSnapshot, MtimeSnapshot, hidden


def _join_path(base, lst):
    return [ os.path.join(base, _) for _ in lst if not hidden(_) ]


def _walker_recursive(top):
    dirs, files = xbmcvfs.listdir(top) #returns utf-8 encoded str
    dirs = _join_path(top, dirs)
    files = _join_path(top, files)
    yield dirs, files
    for d in dirs:
        for dirs, files in _walker_recursive(d):
            yield dirs, files


def _get_mtime(path):
    return xbmcvfs.Stat(path).st_mtime()


class VFSPoller(PollerBase):
    interval = settings.POLLING_INTERVAL
    make_snapshot = partial(FileSnapshot, walker=_walker_recursive)


class VFSPollerNonRecursive(PollerBase):
    interval = settings.POLLING_INTERVAL
    make_snapshot = partial(MtimeSnapshot, get_mtime=_get_mtime)

