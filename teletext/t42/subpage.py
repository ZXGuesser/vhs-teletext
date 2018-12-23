import numpy

from descriptors import *
from elements import *
from packet import *
from printer import PrinterHTML

from teletext.misc.all import All

class Subpage(object):
    control = ControlBits()

    def __init__(self, fill=0x20, links=[None for n in range(6)]):
        self.displayable = numpy.full((40, 25), fill, dtype=numpy.uint8)
        self.control = 0
        self.__links = [link if link else PageLink() for link in links]
        self.packet26 = numpy.full((40, 16), fill, dtype=numpy.uint8)
        self.packet27 = numpy.full((40, 4), fill, dtype=numpy.uint8)
        self.packet28 = numpy.full((40, 5), fill, dtype=numpy.uint8)

    @property
    def links(self):
        return self.__links

    @staticmethod
    def from_packets(packet_iter):
        s = Subpage()

        for p in packet_iter:
            if type(p) == HeaderPacket:
                s._original_subpage = p.header.subpage
                s._original_page = p.header.page
                s._original_magazine = p.mrag.magazine
                s._original_displayable = p.displayable
            elif type(p) == FastextPacket:
                if p.dc == 0:
                    for i in range(6):
                        s.links[i] = p.links[i]
                # TODO: DC 1-3
            elif type(p) == DisplayPacket:
                s.displayable[:,p.mrag.row-1] = p.displayable
            elif type(p) == EnhancementPacket:
                if p.mrag.row == 26:
                    s.packet26[:,p.dc] = p.data
                elif p.mrag.row == 27:
                    s.packet27[:,p.dc-4] = p.data
                elif p.mrag.row == 28:
                    s.packet28[:,p.dc] = p.data

        return s

    def to_packets(self, magazineno, pageno, subpageno, header_displayable=numpy.full((32,), 0x20, dtype=numpy.uint8)):
        yield HeaderPacket(Mrag(magazineno, 0), PageHeader(pageno, subpageno, self.control), header_displayable)
        for i in range(0, 25):
            if (self.displayable[:,i] != 0x20).any():
                yield DisplayPacket(Mrag(magazineno, i+1), self.displayable[:,i])
        for i in range(0, 16):
            if (self.packet26[:,i] != 0x20).any():
                yield EnhancementPacket(Mrag(magazineno, 26), self.packet26[:,i])
        for i in range(0, 5):
            if (self.packet28[:,i] != 0x20).any():
                yield EnhancementPacket(Mrag(magazineno, 28), self.packet28[:,i])
        yield FastextPacket(Mrag(magazineno, 27), self.links)

    def to_html(self, magazineno, pageno, subpageno, header_displayable=numpy.full((32,), 0x20, dtype=numpy.uint8), pages_set=All):
        body = []

        p = PrinterHTML(header_displayable)
        p.anchor = '#%04X' % subpageno
        body.append('   <span class="pgnum">P%d%02x</span> ' % (magazineno, pageno) + str(p))

        for i in range(0,25):
            if i == 0 or numpy.all(self.displayable[:,i-1] != 0x0d):
                p = PrinterHTML(self.displayable[:,i], pages_set=pages_set)
                if i == 23:
                    p.fastext = True
                    p.links = ['%d%02X' % (l.magazine, l.page) for l in self.links]
                body.append(str(p))

        head = '<div class="subpage" id="%04X">' % subpageno

        return head + "".join(body) + '</div>'

