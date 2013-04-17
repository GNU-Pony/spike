#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
spike – a package manager running on top of git

Copyright © 2013  Mattias Andrée (maandree@member.fsf.org)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import sys
import os


class SHA3:
    '''
    SHA-3/Keccak[] hash algorithm implementation
    
    @author  Mattias Andrée  (maandree@member.fsf.org)
    '''
    
    
    RC=[0x0000000000000001, 0x0000000000008082, 0x800000000000808A, 0x8000000080008000,
        0x000000000000808B, 0x0000000080000001, 0x8000000080008081, 0x8000000000008009,
        0x000000000000008A, 0x0000000000000088, 0x0000000080008009, 0x000000008000000A,
        0x000000008000808B, 0x800000000000008B, 0x8000000000008089, 0x8000000000008003,
        0x8000000000008002, 0x8000000000000080, 0x000000000000800A, 0x800000008000000A,
        0x8000000080008081, 0x8000000000008080, 0x0000000080000001, 0x8000000080008008]
    '''
    :list<int>  Round contants
    '''
    
    B = [0] * 25
    '''
    :list<int>  Keccak-f round temporary
    '''
    
    C = [0] * 5
    '''
    :list<int>  Keccak-f round temporary
    '''
    

    (r, c, n) = (0, 0, 0)
    '''
       r:int  The bitrate
       c:int  The capacity
       n:int  The output size
    '''
    
    S = None
    '''
    :list<int>  The current state
    '''
    
    M = None
    '''
    :bytes  Left over water to fill the sponge with at next update
    '''
    
    
    
    @staticmethod
    def rotate64(x, n):
        '''
        Rotate a 64-bit word
        
        @param   x:int  The value to rotate
        @param   n:int  Rotation steps
        @return   :int  The value rotated
        '''
        return ((x >> (64 - n)) + (x << n)) & 0xFFFFFFFFFFFFFFFF
    
    
    @staticmethod
    def lb(x):
        '''
        Binary logarithm
        
        @param   x:int  The value of which to calculate the binary logarithm
        @return   :int  The binary logarithm
        '''
        rc = 0
        if (x & 0xFF00) != 0:  rc +=  8 ;  x >>=  8
        if (x & 0x00F0) != 0:  rc +=  4 ;  x >>=  4
        if (x & 0x000C) != 0:  rc +=  2 ;  x >>=  2
        if (x & 0x0002) != 0:  rc +=  1
        return rc
    
    
    @staticmethod
    def keccakFRound(A, rc):
        '''
        Perform one round of computation
        
        @param   A:list<int>  The current state
        @param  rc:int        Round constant
        '''
        # θ step (step 1 and 2 of 3)
        SHA3.C[0] = (A[0]  ^ A[1])  ^ (A[2]  ^ A[3])  ^ A[4]
        SHA3.C[2] = (A[10] ^ A[11]) ^ (A[12] ^ A[13]) ^ A[14]
        db = SHA3.C[0] ^ SHA3.rotate64(SHA3.C[2], 1)
        SHA3.C[4] = (A[20] ^ A[21]) ^ (A[22] ^ A[23]) ^ A[24]
        dd = SHA3.C[2] ^ SHA3.rotate64(SHA3.C[4], 1)
        SHA3.C[1] = (A[5]  ^ A[6])  ^ (A[7]  ^ A[8])  ^ A[9]
        da = SHA3.C[4] ^ SHA3.rotate64(SHA3.C[1], 1)
        SHA3.C[3] = (A[15] ^ A[16]) ^ (A[17] ^ A[18]) ^ A[19]
        dc = SHA3.C[1] ^ SHA3.rotate64(SHA3.C[3], 1)
        de = SHA3.C[3] ^ SHA3.rotate64(SHA3.C[0], 1)
        
        # ρ and π steps, with last part of θ
        SHA3.B[0] = SHA3.rotate64(A[0] ^ da, 0)
        SHA3.B[1] = SHA3.rotate64(A[15] ^ dd, 28)
        SHA3.B[2] = SHA3.rotate64(A[5] ^ db, 1)
        SHA3.B[3] = SHA3.rotate64(A[20] ^ de, 27)
        SHA3.B[4] = SHA3.rotate64(A[10] ^ dc, 62)
        
        SHA3.B[5] = SHA3.rotate64(A[6] ^ db, 44)
        SHA3.B[6] = SHA3.rotate64(A[21] ^ de, 20)
        SHA3.B[7] = SHA3.rotate64(A[11] ^ dc, 6)
        SHA3.B[8] = SHA3.rotate64(A[1] ^ da, 36)
        SHA3.B[9] = SHA3.rotate64(A[16] ^ dd, 55)
        
        SHA3.B[10] = SHA3.rotate64(A[12] ^ dc, 43)
        SHA3.B[11] = SHA3.rotate64(A[2] ^ da, 3)
        SHA3.B[12] = SHA3.rotate64(A[17] ^ dd, 25)
        SHA3.B[13] = SHA3.rotate64(A[7] ^ db, 10)
        SHA3.B[14] = SHA3.rotate64(A[22] ^ de, 39)
        
        SHA3.B[15] = SHA3.rotate64(A[18] ^ dd, 21)
        SHA3.B[16] = SHA3.rotate64(A[8] ^ db, 45)
        SHA3.B[17] = SHA3.rotate64(A[23] ^ de, 8)
        SHA3.B[18] = SHA3.rotate64(A[13] ^ dc, 15)
        SHA3.B[19] = SHA3.rotate64(A[3] ^ da, 41)
        
        SHA3.B[20] = SHA3.rotate64(A[24] ^ de, 14)
        SHA3.B[21] = SHA3.rotate64(A[14] ^ dc, 61)
        SHA3.B[22] = SHA3.rotate64(A[4] ^ da, 18)
        SHA3.B[23] = SHA3.rotate64(A[19] ^ dd, 56)
        SHA3.B[24] = SHA3.rotate64(A[9] ^ db, 2)
        
        # ξ step
        A[0] = SHA3.B[0] ^ ((~(SHA3.B[5])) & SHA3.B[10])
        A[1] = SHA3.B[1] ^ ((~(SHA3.B[6])) & SHA3.B[11])
        A[2] = SHA3.B[2] ^ ((~(SHA3.B[7])) & SHA3.B[12])
        A[3] = SHA3.B[3] ^ ((~(SHA3.B[8])) & SHA3.B[13])
        A[4] = SHA3.B[4] ^ ((~(SHA3.B[9])) & SHA3.B[14])
        
        A[5] = SHA3.B[5] ^ ((~(SHA3.B[10])) & SHA3.B[15])
        A[6] = SHA3.B[6] ^ ((~(SHA3.B[11])) & SHA3.B[16])
        A[7] = SHA3.B[7] ^ ((~(SHA3.B[12])) & SHA3.B[17])
        A[8] = SHA3.B[8] ^ ((~(SHA3.B[13])) & SHA3.B[18])
        A[9] = SHA3.B[9] ^ ((~(SHA3.B[14])) & SHA3.B[19])
        
        A[10] = SHA3.B[10] ^ ((~(SHA3.B[15])) & SHA3.B[20])
        A[11] = SHA3.B[11] ^ ((~(SHA3.B[16])) & SHA3.B[21])
        A[12] = SHA3.B[12] ^ ((~(SHA3.B[17])) & SHA3.B[22])
        A[13] = SHA3.B[13] ^ ((~(SHA3.B[18])) & SHA3.B[23])
        A[14] = SHA3.B[14] ^ ((~(SHA3.B[19])) & SHA3.B[24])
        
        A[15] = SHA3.B[15] ^ ((~(SHA3.B[20])) & SHA3.B[0])
        A[16] = SHA3.B[16] ^ ((~(SHA3.B[21])) & SHA3.B[1])
        A[17] = SHA3.B[17] ^ ((~(SHA3.B[22])) & SHA3.B[2])
        A[18] = SHA3.B[18] ^ ((~(SHA3.B[23])) & SHA3.B[3])
        A[19] = SHA3.B[19] ^ ((~(SHA3.B[24])) & SHA3.B[4])
        
        A[20] = SHA3.B[20] ^ ((~(SHA3.B[0])) & SHA3.B[5])
        A[21] = SHA3.B[21] ^ ((~(SHA3.B[1])) & SHA3.B[6])
        A[22] = SHA3.B[22] ^ ((~(SHA3.B[2])) & SHA3.B[7])
        A[23] = SHA3.B[23] ^ ((~(SHA3.B[3])) & SHA3.B[8])
        A[24] = SHA3.B[24] ^ ((~(SHA3.B[4])) & SHA3.B[9])
        
        # ι step
        A[0] ^= rc
    
    
    @staticmethod
    def keccakF(A):
        '''
        Perform Keccak-f function
        
        @param  A:list<int>  The current state
        '''
        SHA3.keccakFRound(A, 0x0000000000000001)
        SHA3.keccakFRound(A, 0x0000000000008082)
        SHA3.keccakFRound(A, 0x800000000000808A)
        SHA3.keccakFRound(A, 0x8000000080008000)
        SHA3.keccakFRound(A, 0x000000000000808B)
        SHA3.keccakFRound(A, 0x0000000080000001)
        SHA3.keccakFRound(A, 0x8000000080008081)
        SHA3.keccakFRound(A, 0x8000000000008009)
        SHA3.keccakFRound(A, 0x000000000000008A)
        SHA3.keccakFRound(A, 0x0000000000000088)
        SHA3.keccakFRound(A, 0x0000000080008009)
        SHA3.keccakFRound(A, 0x000000008000000A)
        SHA3.keccakFRound(A, 0x000000008000808B)
        SHA3.keccakFRound(A, 0x800000000000008B)
        SHA3.keccakFRound(A, 0x8000000000008089)
        SHA3.keccakFRound(A, 0x8000000000008003)
        SHA3.keccakFRound(A, 0x8000000000008002)
        SHA3.keccakFRound(A, 0x8000000000000080)
        SHA3.keccakFRound(A, 0x000000000000800A)
        SHA3.keccakFRound(A, 0x800000008000000A)
        SHA3.keccakFRound(A, 0x8000000080008081)
        SHA3.keccakFRound(A, 0x8000000000008080)
        SHA3.keccakFRound(A, 0x0000000080000001)
        SHA3.keccakFRound(A, 0x8000000080008008)
    
    
    @staticmethod
    def toLane64(message, rr, off):
        '''
        Convert a chunk of char:s to a 64-bit word
        
        @param   message:bytes  The message
        @param        rr:int    Bitrate in bytes
        @param       off:int    The offset in the message
        @return         :int    Lane
        '''
        rc = 0
        n = min(len(message), rr)
        
        return ((message[off + 7] << 56) if (off + 7 < n) else 0) | ((message[off + 6] << 48) if (off + 6 < n) else 0) | ((message[off + 5] << 40) if (off + 5 < n) else 0) | ((message[off + 4] << 32) if (off + 4 < n) else 0) | ((message[off + 3] << 24) if (off + 3 < n) else 0) | ((message[off + 2] << 16) if (off + 2 < n) else 0) | ((message[off + 1] <<  8) if (off + 1 < n) else 0) | ((message[off]) if (off < n) else 0)
    
    
    @staticmethod
    def pad10star1(msg, r):
        '''
        pad 10*1
        
        @param   msg:bytes  The message to pad
        @param     r:int    The bitrate
        @return     :str    The message padded
        '''
        nnn = len(msg) << 3
        
        nrf = nnn >> 3
        nbrf = nnn & 7
        ll = nnn % r
        
        bbbb = 1 if nbrf == 0 else ((msg[nrf] >> (8 - nbrf)) | (1 << nbrf))
        
        message = None
        if ((r - 8 <= ll) and (ll <= r - 2)):
            message = [bbbb ^ 128]
        else:
            nnn = (nrf + 1) << 3
            nnn = ((nnn - (nnn % r) + (r - 8)) >> 3) + 1
            message = [0] * (nnn - nrf)
            message[0] = bbbb
            nnn -= nrf
            message[nnn - 1] = 0x80
        
        return msg[:nrf] + bytes(message)
    
    
    @staticmethod
    def initialise(r, c, n):
        '''
        Initialise Keccak sponge
        
        @param  r:int  The bitrate
        @param  c:int  The capacity
        @param  n:int  The output size
        '''
        SHA3.r = r
        SHA3.c = c
        SHA3.n = n
        SHA3.S = [0] * 25
        SHA3.M = bytes([])
    
    
    @staticmethod
    def update(msg):
        '''
        Absorb the more of the message message to the Keccak sponge
        
        @param  msg:bytes  The partial message
        '''
        rr = SHA3.r >> 3
        
        SHA3.M += msg
        nnn = len(SHA3.M)
        nnn -= nnn % (SHA3.r * 200)
        message = SHA3.M[:nnn]
        SHA3.M = SHA3.M[nnn:]
        
        # Absorbing phase
        for i in range(0, nnn, rr):
            SHA3.S[ 0] ^= SHA3.toLane64(message, rr, 0)
            SHA3.S[ 5] ^= SHA3.toLane64(message, rr, 8)
            SHA3.S[10] ^= SHA3.toLane64(message, rr, 16)
            SHA3.S[15] ^= SHA3.toLane64(message, rr, 24)
            SHA3.S[20] ^= SHA3.toLane64(message, rr, 32)
            SHA3.S[ 1] ^= SHA3.toLane64(message, rr, 40)
            SHA3.S[ 6] ^= SHA3.toLane64(message, rr, 48)
            SHA3.S[11] ^= SHA3.toLane64(message, rr, 56)
            SHA3.S[16] ^= SHA3.toLane64(message, rr, 64)
            SHA3.S[21] ^= SHA3.toLane64(message, rr, 72)
            SHA3.S[ 2] ^= SHA3.toLane64(message, rr, 80)
            SHA3.S[ 7] ^= SHA3.toLane64(message, rr, 88)
            SHA3.S[12] ^= SHA3.toLane64(message, rr, 96)
            SHA3.S[17] ^= SHA3.toLane64(message, rr, 104)
            SHA3.S[22] ^= SHA3.toLane64(message, rr, 112)
            SHA3.S[ 3] ^= SHA3.toLane64(message, rr, 120)
            SHA3.S[ 8] ^= SHA3.toLane64(message, rr, 128)
            SHA3.S[13] ^= SHA3.toLane64(message, rr, 136)
            SHA3.S[18] ^= SHA3.toLane64(message, rr, 144)
            SHA3.S[23] ^= SHA3.toLane64(message, rr, 152)
            SHA3.S[ 4] ^= SHA3.toLane64(message, rr, 160)
            SHA3.S[ 9] ^= SHA3.toLane64(message, rr, 168)
            SHA3.S[14] ^= SHA3.toLane64(message, rr, 176)
            SHA3.S[19] ^= SHA3.toLane64(message, rr, 184)
            SHA3.S[24] ^= SHA3.toLane64(message, rr, 192)
            SHA3.keccakF(SHA3.S)
            message = message[rr:]
    
    
    @staticmethod
    def digest(msg = None):
        '''
        Absorb the last part of the message and squeeze the Keccak sponge
        
        @param  msg:bytes  The rest of the message
        '''
        if msg is None:
            msg = bytes([])
        message = SHA3.pad10star1(SHA3.M + msg, SHA3.r)
        SHA3.M = None
        nnn = len(message)
        rc = [0] * ((SHA3.n + 7) >> 3)
        ptr = 0
        
        rr = SHA3.r >> 3
        nn = SHA3.n >> 3
        
        # Absorbing phase
        for i in range(0, nnn, rr):
            SHA3.S[ 0] ^= SHA3.toLane64(message, rr, 0)
            SHA3.S[ 5] ^= SHA3.toLane64(message, rr, 8)
            SHA3.S[10] ^= SHA3.toLane64(message, rr, 16)
            SHA3.S[15] ^= SHA3.toLane64(message, rr, 24)
            SHA3.S[20] ^= SHA3.toLane64(message, rr, 32)
            SHA3.S[ 1] ^= SHA3.toLane64(message, rr, 40)
            SHA3.S[ 6] ^= SHA3.toLane64(message, rr, 48)
            SHA3.S[11] ^= SHA3.toLane64(message, rr, 56)
            SHA3.S[16] ^= SHA3.toLane64(message, rr, 64)
            SHA3.S[21] ^= SHA3.toLane64(message, rr, 72)
            SHA3.S[ 2] ^= SHA3.toLane64(message, rr, 80)
            SHA3.S[ 7] ^= SHA3.toLane64(message, rr, 88)
            SHA3.S[12] ^= SHA3.toLane64(message, rr, 96)
            SHA3.S[17] ^= SHA3.toLane64(message, rr, 104)
            SHA3.S[22] ^= SHA3.toLane64(message, rr, 112)
            SHA3.S[ 3] ^= SHA3.toLane64(message, rr, 120)
            SHA3.S[ 8] ^= SHA3.toLane64(message, rr, 128)
            SHA3.S[13] ^= SHA3.toLane64(message, rr, 136)
            SHA3.S[18] ^= SHA3.toLane64(message, rr, 144)
            SHA3.S[23] ^= SHA3.toLane64(message, rr, 152)
            SHA3.S[ 4] ^= SHA3.toLane64(message, rr, 160)
            SHA3.S[ 9] ^= SHA3.toLane64(message, rr, 168)
            SHA3.S[14] ^= SHA3.toLane64(message, rr, 176)
            SHA3.S[19] ^= SHA3.toLane64(message, rr, 184)
            SHA3.S[24] ^= SHA3.toLane64(message, rr, 192)
            SHA3.keccakF(SHA3.S)
            message = message[rr:]
        
        # Squeezing phase
        olen = SHA3.n
        j = 0
        ni = min(25, rr)
        while (olen > 0):
            i = 0
            while (i < ni) and (j < nn):
                v = SHA3.S[(i % 5) * 5 + i // 5]
                for _ in range(64):
                    if (j < nn):
                        rc[ptr] = v & 255
                        ptr += 1
                    v >>= 8
                    j += 1
                i += 1
            olen -= SHA3.r
            if olen > 0:
                SHA3.keccakF(S)
        
        return bytes(rc)



if __name__ == '__main__':
    files = []
    if len(files) == 0:
        files.append(None)
    stdin = None
    for filename in files:
        if (filename is None) and (stdin is not None):
            print(stdin)
            continue
        rc = ''
        fn = '/dev/stdin' if filename is None else filename
        with open(fn, 'rb') as file:
            SHA3.initialise(1024, 576, 576)
            blksize = 8192
            try:
                blksize = os.stat(os.path.realpath(fn)).st_blksize
            except:
                pass
            while True:
                chunk = file.read(blksize)
                if len(chunk) == 0:
                    break
                SHA3.update(chunk)
            bs = SHA3.digest(file.read())
            for b in bs:
                rc += "0123456789ABCDEF"[b >> 4]
                rc += "0123456789ABCDEF"[b & 15]
            rc += ' ' + ('-' if filename is None else filename) + '\n'
            if filename is None:
                stdin = rc
            sys.stdout.buffer.write(rc.encode('UTF-8'))
            sys.stdout.buffer.flush()


