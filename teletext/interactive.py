import curses
import os
import time
import locale

from .file import FileChunker
from .packet import Packet
from .printer import PrinterANSI


def setstyle(self, fg=None, bg=None):
    return '\033[' + chr(fg or self.fg) + chr(bg or self.bg) + chr(1 if self.flash else 0 + 2 if self.conceal else 0)


PrinterANSI.setstyle = setstyle


class TerminalTooSmall(Exception):
    pass


class Interactive(object):
    colours = {0: curses.COLOR_BLACK, 1: curses.COLOR_RED, 2: curses.COLOR_GREEN, 3: curses.COLOR_YELLOW,
               4: curses.COLOR_BLUE, 5: curses.COLOR_MAGENTA, 6: curses.COLOR_CYAN, 7: curses.COLOR_WHITE}

    def __init__(self, packet_iter, scr):
        self.scr = scr

        self.packet_iter = packet_iter

        self.magazine = 1
        self.page = 0
        self.last_subpage = None
        self.last_header = None
        self.inputtmp = [None, None, None]
        self.inputstate = 0
        self.hold = False
        self.reveal = False

        y, x = self.scr.getmaxyx()
        if x < 41 or y < 25:
            raise TerminalTooSmall(x, y)

        for n in range(64):
            curses.init_pair(n + 1, Interactive.colours[n & 0x7], Interactive.colours[n >> 3])
        self.set_concealed_pairs()

        self.scr.nodelay(1)
        curses.curs_set(0)

        self.set_input_field('P100')

    def set_concealed_pairs(self, show=False):
        for n in range(64):
            curses.init_pair(n + 1 + 64, Interactive.colours[n & 0x7] if show else Interactive.colours[n >> 3],
                             Interactive.colours[n >> 3])

    def set_input_field(self, str, clr=0):
        self.scr.addstr(0, 3, str, curses.color_pair(clr))

    def addstr(self, row, st):
        s = iter(st.split('\033['))
        self.scr.addstr(row, 0, next(s))
        for fragment in s:
            fg = ord(fragment[0])
            bg = ord(fragment[1])
            flash = ord(fragment[2]) & 1
            conceal = ord(fragment[2]) & 2
            colour = (fg | (bg << 3)) + (1 if conceal else 1)
            self.scr.addstr(fragment[3:], curses.color_pair(colour) | (curses.A_BLINK if flash else 0))

    def do_alnum(self, i):
        if self.inputstate == 0:
            if i >= 1 and i <= 8:
                self.inputtmp[0] = i
                self.inputstate = 1
        else:
            self.inputtmp[self.inputstate] = i
            self.inputstate += 1

        if self.inputstate != 0:
            self.set_input_field(
                'P' + ''.join([('%1X' % self.inputtmp[x]) if self.inputtmp[x] is not None else '.' for x in range(3)]),
                3 if self.inputstate < 3 else 0)

        if self.inputstate == 3:
            self.inputstate = 0
            self.magazine = self.inputtmp[0]
            self.page = (self.inputtmp[1] << 4) | self.inputtmp[2]
            self.inputtmp = [None, None, None]

    def do_hold(self):
        self.hold = not self.hold
        if self.hold:
            self.set_input_field('HOLD', 2)
            self.inputstate = 0
            self.inputtmp[0] = None
            self.inputtmp[1] = None
            self.inputtmp[2] = None
        else:
            self.set_input_field('P%d%02x' % (self.magazine, self.page))

    def do_reveal(self):
        self.reveal = not self.reveal
        self.set_concealed_pairs(self.reveal)

    def do_input(self, c):
        if c >= ord('0') and c <= ord('9'):
            if self.hold:
                self.do_hold()
            self.do_alnum(c - ord('0'))
        elif c >= ord('a') and c <= ord('f'):
            if self.hold:
                self.do_hold()
            self.do_alnum(c + 10 - ord('a'))
        elif c == ord('.'):
            self.do_hold()
        elif c == ord('r'):
            self.do_reveal()
        elif c == ord('q'):
            self.running = False

    def handle_one_packet(self):

        packet = next(self.packet_iter)
        if self.inputstate == 0 and not self.hold:
            if packet.mrag.magazine == self.magazine % 8:
                if packet.mrag.row == 0:
                    self.last_header = packet.header.page
                    if self.last_header == self.page:
                        self.scr.clear()
                    self.addstr(packet.mrag.row, packet.to_ansi(colour=False))
                    self.set_input_field('P%d%02X' % (self.magazine, self.page))
                elif self.last_header == self.page and packet.mrag.row < 25:
                    self.addstr(packet.mrag.row, packet.to_ansi(colour=False))

    def main(self):
        self.running = True
        while self.running:
            for i in range(32):
                self.handle_one_packet()

            self.do_input(self.scr.getch())

            self.scr.refresh()
            time.sleep(0.02)


def main(input):
    locale.setlocale(locale.LC_ALL, '')

    input_dup = os.fdopen(os.dup(input.fileno()), 'rb')
    if os.name == 'nt':
        f = open("CON:", 'r')
    else:
        f = open("/dev/tty", 'r')
    os.dup2(f.fileno(), 0)

    chunks = FileChunker(input_dup, 42)
    packets = (Packet(data, number) for number, data in chunks)

    def main(scr):
        Interactive(packets, scr).main()

    try:
        curses.wrapper(main)
    except TerminalTooSmall as e:
        print(f'Your terminal is too small.\nPlease make it at least 41x25.\nCurrent size: {e.args[0]}x{e.args[1]}.')
        exit(-1)
