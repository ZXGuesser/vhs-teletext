# * Copyright 2016 Alistair Buxton <a.j.buxton@gmail.com>
# *
# * License: This program is free software; you can redistribute it and/or
# * modify it under the terms of the GNU General Public License as published
# * by the Free Software Foundation; either version 3 of the License, or (at
# * your option) any later version. This program is distributed in the hope
# * that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# * warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# * GNU General Public License for more details.

import sys
import argparse
import importlib
import itertools
from multiprocessing.pool import Pool

import numpy
from scipy.stats.mstats import mode
from tqdm import tqdm

from .map import RawLineReader
from .line import Line

from teletext.misc.all import All
from teletext.t42.packet import Packet


extra_roll = 0

def doit(*args, **kwargs):
    l = Line(*args, **kwargs)
    if l.is_teletext:
        l.roll(extra_roll)
        l.bits()
        l.mrag()
        l.bytes()
    return l


def split_seq(iterable, size):
    it = iter(iterable)
    item = list(itertools.islice(it, size))
    while item:
        yield item
        item = list(itertools.islice(it, size))


def deconvolve():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('inputfile', type=str, help='Read VBI samples from this file.')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-a', '--ansi',
                       help='Output lines in ANSI format suitable for console display. Default if STDOUT is a tty.',
                       action='store_true')
    group.add_argument('-t', '--t42',
                       help='Output lines in T42 format for further processing. Default if STDOUT is not a tty.',
                       action='store_true')

    parser.add_argument('-r', '--rows', type=int, metavar='R', nargs='+',
                        help='Only attempt to deconvolve.py lines from these rows.', default=All)
    parser.add_argument('-m', '--mags', type=int, metavar='M', nargs='+',
                        help='Only attempt to deconvolve.py lines from these magazines.', default=All)
    parser.add_argument('-n', '--numbered',
                        help='When output is ansi, number the lines according to position in input file.',
                        action='store_true')
    parser.add_argument('-c', '--config', help='Configuration. Default bt8x8_pal.', default='bt8x8_pal')
    parser.add_argument('-e', '--extra-roll', metavar='SAMPLES', type=int, help='Extra roll.', default=4)
    parser.add_argument('-H', '--headers', help='Synonym for --ansi --numbered --rows 0.', action='store_true')
    parser.add_argument('-S', '--squash', metavar='N', type=int, help='Merge N consecutive rows to reduce output.',
                        default=1)
    parser.add_argument('-C', '--force-cpu', help='Disable CUDA even if it is available.', action='store_true')
    parser.add_argument('-T', '--threads', type=int, help='Number of CPU worker threads. Default 1.', default=1)

    parser.add_argument('--start', type=int, metavar='N', help='Start after the Nth line of the input file.', default=0)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--stop', type=int, metavar='N', help='Stop before the Nth line of the input file.', default=-1)
    group.add_argument('--count', type=int, metavar='N', help='Stop after processing N lines from the input file.',
                       default=-1)

    cliargs = parser.parse_args()

    if not cliargs.t42 and not cliargs.ansi:
        if sys.stdout.isatty():
            cliargs.ansi = True
        else:
            cliargs.t42 = True

    if cliargs.stop == -1 and cliargs.count > -1:
        cliargs.stop = cliargs.start + cliargs.count

    if cliargs.headers:
        cliargs.ansi = True
        cliargs.t42 = False
        cliargs.numbered = True
        cliargs.rows = {0}

    try:
        config = importlib.import_module('config_' + cliargs.config)
    except ImportError:
        sys.stderr.write('No configuration file for ' + cliargs.config + '.\n')

    Line.set_config(config)

    if cliargs.force_cpu:
        Line.disable_cuda()

    global extra_roll
    extra_roll = cliargs.extra_roll

    if cliargs.threads > 0:
        p = Pool(cliargs.threads)
        map_func = lambda f, it: p.imap(f, it, chunksize=1000)
    else:
        map_func = map

    with RawLineReader(cliargs.inputfile, config.line_length, start=cliargs.start, stop=cliargs.stop) as rl:
        with tqdm(rl, unit=' Lines') as rlw:

            it = (l for l in map_func(doit, rlw) if l.is_teletext and l.magazine in cliargs.mags and l.row in cliargs.rows)

            if cliargs.squash > 1:
                for l_list in split_seq(it, cliargs.squash):
                    a = numpy.array([l.bytes_array for l in l_list])
                    best, counts = mode(a)
                    best = best[0].astype(numpy.uint8)
                    if cliargs.t42:
                        best.tofile(sys.stdout)
                    elif cliargs.ansi:
                        if cliargs.numbered:
                            rlw.write(('%8d ' % l_list[0].offset), end='')
                        rlw.write(Packet.from_bytes(best).to_ansi())

            else:
                for l in it:
                    if cliargs.t42:
                        l.bytes_array.tofile(sys.stdout)
                    elif cliargs.ansi:
                        if cliargs.numbered:
                            rlw.write(('%8d ' % l.offset), end='')
                        rlw.write(Packet.from_bytes(l.bytes_array).to_ansi())