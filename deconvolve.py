#!/usr/bin/env python

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

import numpy

from teletext.vbi.map import raw_line_map
from teletext.vbi.pattern import Pattern
from teletext.vbi.line import Line
from teletext.misc.all import All

from teletext.t42.packet import Packet

from scipy.stats.mstats import mode

if sys.platform == "win32":
    import os, msvcrt
    msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('inputfile', type=str, help='Read VBI samples from this file.')
group = parser.add_mutually_exclusive_group()
group.add_argument('-a', '--ansi', help='Output lines in ANSI format suitable for console display. Default if STDOUT is a tty.', action='store_true')
group.add_argument('-t', '--t42', help='Output lines in T42 format for further processing. Default if STDOUT is not a tty.', action='store_true')

parser.add_argument('-r', '--rows', type=int, metavar='R', nargs='+', help='Only attempt to deconvolve lines from these rows.', default=All)
parser.add_argument('-m', '--mags', type=int, metavar='M', nargs='+', help='Only attempt to deconvolve lines from these magazines.', default=All)
parser.add_argument('-n', '--numbered', help='When output is ansi, number the lines according to position in input file.', action='store_true')
parser.add_argument('-c', '--config', help='Configuration. Default bt8x8_pal.', default='bt8x8_pal')
parser.add_argument('-e', '--extra-roll', metavar='SAMPLES', type=int, help='Extra roll.', default=4)
parser.add_argument('-H', '--headers', help='Synonym for --ansi --numbered --rows 0.', action='store_true')
parser.add_argument('-S', '--squash', metavar='N', type=int, help='Merge N consecutive rows to reduce output.', default=1)
parser.add_argument('-C', '--force-cpu', help='Disable CUDA even if it is available.', action='store_true')
parser.add_argument('-T', '--threads', type=int, help='Number of CPU worker threads. Default 1.', default=1)

parser.add_argument('--start', type=int, metavar='N', help='Start after the Nth line of the input file.', default=0)
group = parser.add_mutually_exclusive_group()
group.add_argument('--stop', type=int, metavar='N', help='Stop before the Nth line of the input file.', default=-1)
group.add_argument('--count', type=int, metavar='N', help='Stop after processing N lines from the input file.', default=-1)


args = parser.parse_args()

if not args.t42 and not args.ansi:
    if sys.stdout.isatty():
        args.ansi = True
    else:
        args.t42 = True

if args.stop == -1 and args.count > -1:
    args.stop = args.start + args.count

if args.headers:
    args.ansi = True
    args.t42 = False
    args.numbered = True
    args.rows = set([0])

try:
    config = importlib.import_module('config_'+args.config)
except ImportError:
    sys.stderr.write('No configuration file for '+args.config+'.\n')

Line.set_config(config)

if args.force_cpu:
    Line.disable_cuda()


def doit(rl):
    l = Line(rl)
    if l.is_teletext:
        l.roll(args.extra_roll)
        l.bits()
        l.mrag()
        if l.magazine in args.mags and l.row in args.rows:
            l.bytes()
        else:
            l.is_teletext = False
    return l


def split_seq(iterable, size):
    it = iter(iterable)
    item = list(itertools.islice(it, size))
    while item:
        yield item
        item = list(itertools.islice(it, size))

if __name__ == '__main__':
    it = raw_line_map(args.inputfile, config.line_length, doit, start=args.start, stop=args.stop, threads=args.threads, show_speed=True)

    if args.squash > 1:
        for l_list in split_seq(it, args.squash):
            a = numpy.array([l.bytes_array for l in l_list])
            best, counts = mode(a)
            best = best[0].astype(numpy.uint8)
            if args.t42:
                best.tofile(sys.stdout)
            elif args.ansi:
                if args.numbered:
                    sys.stdout.write(('%8d ' % l_list[0].offset))
                sys.stdout.write(Packet.from_bytes(best).to_ansi() + '\n')

    else:
        for l in it:
            if args.t42:
                l.bytes_array.tofile(sys.stdout)
            elif args.ansi:
                if args.numbered:
                    sys.stdout.write(('%8d ' % l.offset))
                sys.stdout.write(Packet.from_bytes(l.bytes_array).to_ansi() + '\n')

    sys.stderr.write('\n')
