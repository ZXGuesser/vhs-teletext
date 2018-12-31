# * Copyright 2016 Alistair Buxton <a.j.buxton@gmail.com>
# *
# * License: This program is free software; you can redistribute it and/or
# * modify it under the terms of the GNU General Public License as published
# * by the Free Software Foundation; either version 3 of the License, or (at
# * your option) any later version. This program is distributed in the hope
# * that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# * warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# * GNU General Public License for more details.

import numpy

hammtab = [
    0x0101, 0x100f, 0x0001, 0x0101, 0x100f, 0x0100, 0x0101, 0x100f,
    0x100f, 0x0102, 0x0101, 0x100f, 0x010a, 0x100f, 0x100f, 0x0107,
    0x100f, 0x0100, 0x0101, 0x100f, 0x0100, 0x0000, 0x100f, 0x0100,
    0x0106, 0x100f, 0x100f, 0x010b, 0x100f, 0x0100, 0x0103, 0x100f,
    0x100f, 0x010c, 0x0101, 0x100f, 0x0104, 0x100f, 0x100f, 0x0107,
    0x0106, 0x100f, 0x100f, 0x0107, 0x100f, 0x0107, 0x0107, 0x0007,
    0x0106, 0x100f, 0x100f, 0x0105, 0x100f, 0x0100, 0x010d, 0x100f,
    0x0006, 0x0106, 0x0106, 0x100f, 0x0106, 0x100f, 0x100f, 0x0107,
    0x100f, 0x0102, 0x0101, 0x100f, 0x0104, 0x100f, 0x100f, 0x0109,
    0x0102, 0x0002, 0x100f, 0x0102, 0x100f, 0x0102, 0x0103, 0x100f,
    0x0108, 0x100f, 0x100f, 0x0105, 0x100f, 0x0100, 0x0103, 0x100f,
    0x100f, 0x0102, 0x0103, 0x100f, 0x0103, 0x100f, 0x0003, 0x0103,
    0x0104, 0x100f, 0x100f, 0x0105, 0x0004, 0x0104, 0x0104, 0x100f,
    0x100f, 0x0102, 0x010f, 0x100f, 0x0104, 0x100f, 0x100f, 0x0107,
    0x100f, 0x0105, 0x0105, 0x0005, 0x0104, 0x100f, 0x100f, 0x0105,
    0x0106, 0x100f, 0x100f, 0x0105, 0x100f, 0x010e, 0x0103, 0x100f,
    0x100f, 0x010c, 0x0101, 0x100f, 0x010a, 0x100f, 0x100f, 0x0109,
    0x010a, 0x100f, 0x100f, 0x010b, 0x000a, 0x010a, 0x010a, 0x100f,
    0x0108, 0x100f, 0x100f, 0x010b, 0x100f, 0x0100, 0x010d, 0x100f,
    0x100f, 0x010b, 0x010b, 0x000b, 0x010a, 0x100f, 0x100f, 0x010b,
    0x010c, 0x000c, 0x100f, 0x010c, 0x100f, 0x010c, 0x010d, 0x100f,
    0x100f, 0x010c, 0x010f, 0x100f, 0x010a, 0x100f, 0x100f, 0x0107,
    0x100f, 0x010c, 0x010d, 0x100f, 0x010d, 0x100f, 0x000d, 0x010d,
    0x0106, 0x100f, 0x100f, 0x010b, 0x100f, 0x010e, 0x010d, 0x100f,
    0x0108, 0x100f, 0x100f, 0x0109, 0x100f, 0x0109, 0x0109, 0x0009,
    0x100f, 0x0102, 0x010f, 0x100f, 0x010a, 0x100f, 0x100f, 0x0109,
    0x0008, 0x0108, 0x0108, 0x100f, 0x0108, 0x100f, 0x100f, 0x0109,
    0x0108, 0x100f, 0x100f, 0x010b, 0x100f, 0x010e, 0x0103, 0x100f,
    0x100f, 0x010c, 0x010f, 0x100f, 0x0104, 0x100f, 0x100f, 0x0109,
    0x010f, 0x100f, 0x000f, 0x010f, 0x100f, 0x010e, 0x010f, 0x100f,
    0x0108, 0x100f, 0x100f, 0x0105, 0x100f, 0x010e, 0x010d, 0x100f,
    0x100f, 0x010e, 0x010f, 0x100f, 0x010e, 0x000e, 0x100f, 0x010e,
]



def hamming16_decode(d):
    a = hammtab[d[0]]
    b = hammtab[d[1]]
    err = (a>>8)+(b>>8)
    return (a&0xf|((b&0xf)<<4),err)



def hamming8_decode(d):
    a = hammtab[d]
    return (a&0xf,a>>4)

def hamming8_encode(d):
    d1 = d&1
    d2 = (d>>1)&1
    d3 = (d>>2)&1
    d4 = (d>>3)&1

    p1 = (1 + d1 + d3 + d4) & 1
    p2 = (1 + d1 + d2 + d4) & 1
    p3 = (1 + d1 + d2 + d3) & 1
    p4 = (1 + p1 + d1 + p2 + d2 + p3 + d3 + d4) & 1

    return (p1 | (d1<<1) | (p2<<2) | (d2<<3) 
     | (p3<<4) | (d3<<5) | (p4<<6) | (d4<<7))


def hamming24_encode(d):
    d1 = d&1
    d2 = (d>>1)&1
    d3 = (d>>2)&1
    d4 = (d>>3)&1
    d5 = (d>>4)&1
    d6 = (d>>5)&1
    d7 = (d>>6)&1
    d8 = (d>>7)&1
    d9 = (d>>8)&1
    d10 = (d>>9)&1
    d11 = (d>>10)&1
    d12 = (d>>11)&1
    d13 = (d>>12)&1
    d14 = (d>>13)&1
    d15 = (d>>14)&1
    d16 = (d>>15)&1
    d17 = (d>>16)&1
    d18 = (d>>17)&1
    
    p1 = (1 + d1 + d2 + d4 + d5 + d7 + d9 + d11 + d12 + d14 + d16 + d18) & 1
    p2 = (1 + d1 + d3 + d4 + d6 + d7 + d10 + d11 + d13 + d14 + d17 + d18) & 1
    p3 = (1 + d2 + d3 + d4 + d8 + d9 + d10 + d11 + d15 + d16 + d17 + d18) & 1
    p4 = (1 + d5 + d6 + d7 + d8 + d9 + d10 + d11) & 1
    p5 = (1 + d12 + d13 + d14 + d15 + d16 + d17 + d18) & 1
    p6 = (1 + p1 + p2 + d1 + p3 + d2 + d3 + d4 + p4 + d5 + d6 + d7 + d8 + d9 + d10 + d11 + p5 + d12 + d13 + d14 + d15 + d16 + d17 + d18) & 1
    
    return (p1 | (p2<<1) | (d1<<2) | (p3<<3) | (d2<<4) | (d3<<5) | (d4<<6) | (p4<<7) | (d5<<8) | (d6<<9) | (d7<<10) | (d8<<11) | (d9<<12) | (d10<<13) | (d11<<14) | (p5<<15) | (d12<<16) | (d13<<17) | (d14<<18) | (d15<<19) | (d16<<20) | (d17<<21) | (d18<<22) | (p6<<23))

def hamming24_decode(d):
    # TODO: this would be better implemented in lookup tables
    errors = 0
    errorbit = 0
    p = 1 ^ parity_check(d&0xff) ^ parity_check((d>>8)&0xff) ^ parity_check((d>>16)&0xff)
    c0 = (d&1) ^ ((d>>2)&1) ^ ((d>>4)&1) ^ ((d>>6)&1) ^ ((d>>8)&1) ^ ((d>>10)&1) ^ ((d>>12)&1) ^ ((d>>14)&1) ^ ((d>>16)&1) ^ ((d>>18)&1) ^ ((d>>20)&1) ^ ((d>>22)&1)
    c1 =  ((d>>1)&1) ^ ((d>>2)&1) ^ ((d>>5)&1) ^ ((d>>6)&1) ^ ((d>>9)&1) ^ ((d>>10)&1) ^ ((d>>13)&1) ^ ((d>>14)&1) ^ ((d>>17)&1) ^ ((d>>18)&1) ^ ((d>>21)&1) ^ ((d>>22)&1)
    c2 = ((d>>3)&1) ^ ((d>>4)&1) ^ ((d>>5)&1) ^ ((d>>6)&1) ^ ((d>>11)&1) ^ ((d>>12)&1) ^ ((d>>13)&1) ^ ((d>>14)&1) ^ ((d>>19)&1) ^ ((d>>20)&1) ^ ((d>>21)&1) ^ ((d>>22)&1)
    c3 = ((d>>7)&1) ^ ((d>>8)&1) ^ ((d>>9)&1) ^ ((d>>10)&1) ^ ((d>>11)&1) ^ ((d>>12)&1) ^ ((d>>13)&1) ^ ((d>>14)&1)
    c4 = ((d>>15)&1) ^ ((d>>16)&1) ^ ((d>>17)&1) ^ ((d>>18)&1) ^ ((d>>19)&1) ^ ((d>>20)&1) ^ ((d>>21)&1) ^ ((d>>22)&1)
    
    if p == 1:
        if c0 & c1 & c2 & c3 & c4:
            errors = 0
        else:
            errors = 2
    else:
        errors = 1
        if c0 == 0:
            errorbit |= 1
        if c1 == 0:
            errorbit |= 2
        if c2 == 0:
            errorbit |= 4
        if c3 == 0:
            errorbit |= 8
        if c4 == 0:
            errorbit |= 16
        
        if errorbit:
            d ^= (1 << (errorbit - 1))
    
    decoded = ((d>>22)&1)<<17 | ((d>>21)&1)<<16 | ((d>>20)&1)<<15 | ((d>>19)&1)<<14 | ((d>>18)&1)<<13 | ((d>>17)&1)<<12 | ((d>>16)&1)<<11 | ((d>>14)&1)<<10| ((d>>13)&1)<<9 | ((d>>12)&1)<<8 | ((d>>11)&1)<<7 | ((d>>10)&1)<<6 | ((d>>9)&1)<<5 | ((d>>8)&1)<<4 | ((d>>6)&1)<<3 | ((d>>5)&1)<<2 | ((d>>4)&1)<<1 | ((d>>2)&1)
    
    return decoded, errors

parity_tab = numpy.array([
    1,0,0,1,0,1,1,0,0,1,1,0,1,0,0,1,0,1,1,0,1,0,0,1,1,0,0,1,0,1,1,0,
    0,1,1,0,1,0,0,1,1,0,0,1,0,1,1,0,1,0,0,1,0,1,1,0,0,1,1,0,1,0,0,1,
    0,1,1,0,1,0,0,1,1,0,0,1,0,1,1,0,1,0,0,1,0,1,1,0,0,1,1,0,1,0,0,1,
    1,0,0,1,0,1,1,0,0,1,1,0,1,0,0,1,0,1,1,0,1,0,0,1,1,0,0,1,0,1,1,0,
    0,1,1,0,1,0,0,1,1,0,0,1,0,1,1,0,1,0,0,1,0,1,1,0,0,1,1,0,1,0,0,1,
    1,0,0,1,0,1,1,0,0,1,1,0,1,0,0,1,0,1,1,0,1,0,0,1,1,0,0,1,0,1,1,0,
    1,0,0,1,0,1,1,0,0,1,1,0,1,0,0,1,0,1,1,0,1,0,0,1,1,0,0,1,0,1,1,0,
    0,1,1,0,1,0,0,1,1,0,0,1,0,1,1,0,1,0,0,1,0,1,1,0,0,1,1,0,1,0,0,1
], dtype=numpy.uint8)

def parity_encode(d):
    return d | (parity_tab[d] << 7)

def parity_decode(d):
    return d & 0x7f

def parity_check(d):
    return parity_tab[d]

parity_set = set([parity_encode(n) for n in range(0x80)])
hamming_set = set([hamming8_encode(n) for n in range(0x10)])
hamming24_set = set([hamming24_encode(n) for n in range(0x40000)])