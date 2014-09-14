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


def _join_paths(base_path, paths):
    return [os.path.join(base_path, p) for p in paths if not hidden(p)]


def _walk(path):
    dirs, files = xbmcvfs.listdir(path)
    dirs = _join_paths(path, dirs)
    files = _join_paths(path, files)
    yield dirs, files
    for d in dirs:
        for dirs, files in _walk(d):
            yield dirs, files


def _get_mtime(path):
    return xbmcvfs.Stat(path).st_mtime()


class VFSPoller(PollerBase):
    polling_interval = settings.POLLING_INTERVAL
    make_snapshot = partial(FileSnapshot, walker=_walk)


class VFSPollerNonRecursive(PollerBase):
    polling_interval = settings.POLLING_INTERVAL
    make_snapshot = partial(MtimeSnapshot, get_mtime=_get_mtime)

