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
from polling import PollerBase, FileSnapshot, SnapshotRootOnly, SnapshotWithStat, hidden


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


def _walker_depth_1(top):
    dirs, files = xbmcvfs.listdir(top) #returns utf-8 encoded str
    yield _join_path(top, dirs), _join_path(top, files)


def _get_mtime(path):
    return xbmcvfs.Stat(path).st_mtime()


class XBMCVFSPoller(PollerBase):
    interval = settings.POLLING_INTERVAL
    make_snapshot = partial(FileSnapshot, walker=_walker_recursive)


class XBMCVFSPollerDepth1(XBMCVFSPoller):
    make_snapshot = partial(SnapshotRootOnly, get_mtime=_get_mtime)


class XBMCVFSPollerDepth2(XBMCVFSPoller):
    make_snapshot = partial(SnapshotWithStat, walker=_walker_depth_1, get_mtime=_get_mtime)
