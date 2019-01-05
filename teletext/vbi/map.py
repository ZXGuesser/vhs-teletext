# * Copyright 2016 Alistair Buxton <a.j.buxton@gmail.com>
# *
# * License: This program is free software; you can redistribute it and/or
# * modify it under the terms of the GNU General Public License as published
# * by the Free Software Foundation; either version 3 of the License, or (at
# * your option) any later version. This program is distributed in the hope
# * that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# * warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# * GNU General Public License for more details.

from functools import partial
import multiprocessing
from multiprocessing.pool import IMapIterator, Pool
import itertools
import time
import sys
import os

# raw file handler

def wrapper(func):
  def wrap(self, timeout=None):
    # Note: the timeout of 1 googol seconds introduces a rather subtle
    # bug for Python scripts intended to run many times the age of the universe.
    return func(self, timeout=timeout if timeout is not None else 1e100)
  return wrap
IMapIterator.next = wrapper(IMapIterator.next)


class SpeedMonitor(object):
    def __init__(self, lines):
        self.start_time = time.time()
        self.update_time = self.start_time
        self.teletext = 0
        self.rejects = 0
        self.total = 0
        self.lines = lines


    def tally(self, is_teletext):
        if is_teletext:
            self.teletext += 1
        else:
            self.rejects += 1
        self.total += 1
        if time.time() - self.update_time > 2.0:
            elapsed = time.time() - self.start_time
            m,s = divmod(elapsed, 60)
            h,m = divmod(m, 60)
            completed = float(self.total) / self.lines
            total_lines_sec = self.total / elapsed
            teletext_lines_sec = self.teletext / elapsed
            rejected = float(self.rejects) / self.total
            sys.stderr.write('{:02d}:{:02d}:{:02d} : {:d}/{:d} lines ({:.2%}), {:.0f}/s total, {:.0f}/s teletext, {:.2%} rejected.   \r'.format(int(h), int(m), int(s), self.total, self.lines, completed, total_lines_sec, teletext_lines_sec, rejected))
            self.update_time = time.time()


def raw_line_reader(filename, line_length, start=0, stop=-1):
    with open(filename, 'rb') as infile:
        if start > 0:
            infile.seek(start * line_length)
        rawlines = iter(partial(infile.read, line_length), b'')
        for n,rl in enumerate(rawlines):
            offset = n + start
            if len(rl) < line_length:
                return
            elif offset == stop:
                return
            else:
                yield (offset,rl)



def raw_line_map(filename, line_length, func, start=0, stop=-1, threads=1, pass_teletext=True, pass_rejects=False, show_speed=True):
    if stop < 0:
        statinfo = os.stat(filename)
        lines = statinfo.st_size / 2048
    else:
        lines = stop
    
    if show_speed:
        s = SpeedMonitor(lines)

    if threads > 0:
        p = Pool(threads)
        map_func = lambda x, y: p.imap(x, y, chunksize=100)
    else:
        map_func = itertools.imap

    for l in map_func(func, raw_line_reader(filename, line_length, start, stop)):
        if show_speed:
            s.tally(l.is_teletext)
        if l.is_teletext:
            if pass_teletext:
                yield l
        else:
            if pass_rejects:
                yield l
