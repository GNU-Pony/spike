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
    SHA-3/Keccak[r=1024, c=576, n=576] hash algorithm implementation
    
    @author  Mattias Andrée  (maandree@member.fsf.org)
    '''
    
    def __init__(self):
        '''
        Constructor
        '''
        self.S = None
        # :list<int>  The current state
        self.M = None
        # :bytes  Left over water to fill the sponge with at next update
        self.B = [0] * 25
        # :list<int>  Keccak-f round temporary
        self.C = [0] * 5
        # :list<int>  Keccak-f round temporary
        self.reinitialise()
    
    
    
    @staticmethod
    def rotate(x, n):
        '''
        Rotate a 64-bit word
        
        @param   x:int  The value to rotate
        @param   n:int  Rotation steps
        @return   :int  The value rotated
        '''
        return ((x >> (64 - n)) + (x << n)) & 0xFFFFFFFFFFFFFFFF
    
    
    def keccakFRound(self, rc):
        '''
        Perform one round of computation
        
        @param  rc:int  Round constant
        '''
        # θ step (step 1 and 2 of 3)
        self.C[0] = (self.S[0]  ^ self.S[1])  ^ (self.S[2]  ^ self.S[3])  ^ self.S[4]
        self.C[2] = (self.S[10] ^ self.S[11]) ^ (self.S[12] ^ self.S[13]) ^ self.S[14]
        db = self.C[0] ^ SHA3.rotate(self.C[2], 1)
        self.C[4] = (self.S[20] ^ self.S[21]) ^ (self.S[22] ^ self.S[23]) ^ self.S[24]
        dd = self.C[2] ^ SHA3.rotate(self.C[4], 1)
        self.C[1] = (self.S[5]  ^ self.S[6])  ^ (self.S[7]  ^ self.S[8])  ^ self.S[9]
        da = self.C[4] ^ SHA3.rotate(self.C[1], 1)
        self.C[3] = (self.S[15] ^ self.S[16]) ^ (self.S[17] ^ self.S[18]) ^ self.S[19]
        dc = self.C[1] ^ SHA3.rotate(self.C[3], 1)
        de = self.C[3] ^ SHA3.rotate(self.C[0], 1)
        
        # ρ and π steps, with last part of θ
        self.B[0] = SHA3.rotate(self.S[0] ^ da, 0)
        self.B[1] = SHA3.rotate(self.S[15] ^ dd, 28)
        self.B[2] = SHA3.rotate(self.S[5] ^ db, 1)
        self.B[3] = SHA3.rotate(self.S[20] ^ de, 27)
        self.B[4] = SHA3.rotate(self.S[10] ^ dc, 62)
        
        self.B[5] = SHA3.rotate(self.S[6] ^ db, 44)
        self.B[6] = SHA3.rotate(self.S[21] ^ de, 20)
        self.B[7] = SHA3.rotate(self.S[11] ^ dc, 6)
        self.B[8] = SHA3.rotate(self.S[1] ^ da, 36)
        self.B[9] = SHA3.rotate(self.S[16] ^ dd, 55)
        
        self.B[10] = SHA3.rotate(self.S[12] ^ dc, 43)
        self.B[11] = SHA3.rotate(self.S[2] ^ da, 3)
        self.B[12] = SHA3.rotate(self.S[17] ^ dd, 25)
        self.B[13] = SHA3.rotate(self.S[7] ^ db, 10)
        self.B[14] = SHA3.rotate(self.S[22] ^ de, 39)
        
        self.B[15] = SHA3.rotate(self.S[18] ^ dd, 21)
        self.B[16] = SHA3.rotate(self.S[8] ^ db, 45)
        self.B[17] = SHA3.rotate(self.S[23] ^ de, 8)
        self.B[18] = SHA3.rotate(self.S[13] ^ dc, 15)
        self.B[19] = SHA3.rotate(self.S[3] ^ da, 41)
        
        self.B[20] = SHA3.rotate(self.S[24] ^ de, 14)
        self.B[21] = SHA3.rotate(self.S[14] ^ dc, 61)
        self.B[22] = SHA3.rotate(self.S[4] ^ da, 18)
        self.B[23] = SHA3.rotate(self.S[19] ^ dd, 56)
        self.B[24] = SHA3.rotate(self.S[9] ^ db, 2)
        
        # ξ step
        self.S[0] = self.B[0] ^ ((~(self.B[5])) & self.B[10])
        self.S[1] = self.B[1] ^ ((~(self.B[6])) & self.B[11])
        self.S[2] = self.B[2] ^ ((~(self.B[7])) & self.B[12])
        self.S[3] = self.B[3] ^ ((~(self.B[8])) & self.B[13])
        self.S[4] = self.B[4] ^ ((~(self.B[9])) & self.B[14])
        
        self.S[5] = self.B[5] ^ ((~(self.B[10])) & self.B[15])
        self.S[6] = self.B[6] ^ ((~(self.B[11])) & self.B[16])
        self.S[7] = self.B[7] ^ ((~(self.B[12])) & self.B[17])
        self.S[8] = self.B[8] ^ ((~(self.B[13])) & self.B[18])
        self.S[9] = self.B[9] ^ ((~(self.B[14])) & self.B[19])
        
        self.S[10] = self.B[10] ^ ((~(self.B[15])) & self.B[20])
        self.S[11] = self.B[11] ^ ((~(self.B[16])) & self.B[21])
        self.S[12] = self.B[12] ^ ((~(self.B[17])) & self.B[22])
        self.S[13] = self.B[13] ^ ((~(self.B[18])) & self.B[23])
        self.S[14] = self.B[14] ^ ((~(self.B[19])) & self.B[24])
        
        self.S[15] = self.B[15] ^ ((~(self.B[20])) & self.B[0])
        self.S[16] = self.B[16] ^ ((~(self.B[21])) & self.B[1])
        self.S[17] = self.B[17] ^ ((~(self.B[22])) & self.B[2])
        self.S[18] = self.B[18] ^ ((~(self.B[23])) & self.B[3])
        self.S[19] = self.B[19] ^ ((~(self.B[24])) & self.B[4])
        
        self.S[20] = self.B[20] ^ ((~(self.B[0])) & self.B[5])
        self.S[21] = self.B[21] ^ ((~(self.B[1])) & self.B[6])
        self.S[22] = self.B[22] ^ ((~(self.B[2])) & self.B[7])
        self.S[23] = self.B[23] ^ ((~(self.B[3])) & self.B[8])
        self.S[24] = self.B[24] ^ ((~(self.B[4])) & self.B[9])
        
        # ι step
        self.S[0] ^= rc
    
    
    def keccakF(self):
        '''
        Perform Keccak-f function
        '''
        self.keccakFRound(0x0000000000000001)
        self.keccakFRound(0x0000000000008082)
        self.keccakFRound(0x800000000000808A)
        self.keccakFRound(0x8000000080008000)
        self.keccakFRound(0x000000000000808B)
        self.keccakFRound(0x0000000080000001)
        self.keccakFRound(0x8000000080008081)
        self.keccakFRound(0x8000000000008009)
        self.keccakFRound(0x000000000000008A)
        self.keccakFRound(0x0000000000000088)
        self.keccakFRound(0x0000000080008009)
        self.keccakFRound(0x000000008000000A)
        self.keccakFRound(0x000000008000808B)
        self.keccakFRound(0x800000000000008B)
        self.keccakFRound(0x8000000000008089)
        self.keccakFRound(0x8000000000008003)
        self.keccakFRound(0x8000000000008002)
        self.keccakFRound(0x8000000000000080)
        self.keccakFRound(0x000000000000800A)
        self.keccakFRound(0x800000008000000A)
        self.keccakFRound(0x8000000080008081)
        self.keccakFRound(0x8000000000008080)
        self.keccakFRound(0x0000000080000001)
        self.keccakFRound(0x8000000080008008)
    
    
    @staticmethod
    def toLane(message, off):
        '''
        Convert a chunk of char:s to a 64-bit word
        
        @param   message:bytes  The message
        @param       off:int    The offset in the message
        @return         :int    Lane
        '''
        n = min(len(message), 128)
        
        return ((message[off + 7] << 56) if (off + 7 < n) else 0) | ((message[off + 6] << 48) if (off + 6 < n) else 0) | ((message[off + 5] << 40) if (off + 5 < n) else 0) | ((message[off + 4] << 32) if (off + 4 < n) else 0) | ((message[off + 3] << 24) if (off + 3 < n) else 0) | ((message[off + 2] << 16) if (off + 2 < n) else 0) | ((message[off + 1] <<  8) if (off + 1 < n) else 0) | ((message[off]) if (off < n) else 0)
    
    
    @staticmethod
    def pad10star1(msg):
        '''
        pad 10*1
        
        @param   msg:bytes  The message to pad
        @return     :str    The message padded
        '''
        nnn = len(msg) << 3
        
        nrf = nnn >> 3
        nbrf = nnn & 7
        ll = nnn & 1023
        
        bbbb = 1 if nbrf == 0 else ((msg[nrf] >> (8 - nbrf)) | (1 << nbrf))
        
        message = None
        if ((1016 <= ll) and (ll <= 1022)):
            message = [bbbb ^ 128]
        else:
            nnn = (nrf + 1) << 3
            nnn = ((nnn - (nnn & 1023) + 1016) >> 3) + 1
            message = [0] * (nnn - nrf)
            message[0] = bbbb
            nnn -= nrf
            message[nnn - 1] = 0x80
        
        return msg[:nrf] + bytes(message)
    
    
    def reinitialise(self):
        '''
        Initialise Keccak sponge
        '''
        self.S = [0] * 25
        self.M = bytes([])
    
    
    def update(self, msg):
        '''
        Absorb the more of the message message to the Keccak sponge
        
        @param  msg:bytes  The partial message
        '''
        self.M += msg
        nnn = len(self.M)
        nnn -= nnn % 204800
        message = self.M[:nnn]
        self.M = self.M[nnn:]
        
        # Absorbing phase
        for i in range(0, nnn, 128):
            self.S[ 0] ^= SHA3.toLane(message, 0)
            self.S[ 5] ^= SHA3.toLane(message, 8)
            self.S[10] ^= SHA3.toLane(message, 16)
            self.S[15] ^= SHA3.toLane(message, 24)
            self.S[20] ^= SHA3.toLane(message, 32)
            self.S[ 1] ^= SHA3.toLane(message, 40)
            self.S[ 6] ^= SHA3.toLane(message, 48)
            self.S[11] ^= SHA3.toLane(message, 56)
            self.S[16] ^= SHA3.toLane(message, 64)
            self.S[21] ^= SHA3.toLane(message, 72)
            self.S[ 2] ^= SHA3.toLane(message, 80)
            self.S[ 7] ^= SHA3.toLane(message, 88)
            self.S[12] ^= SHA3.toLane(message, 96)
            self.S[17] ^= SHA3.toLane(message, 104)
            self.S[22] ^= SHA3.toLane(message, 112)
            self.S[ 3] ^= SHA3.toLane(message, 120)
            self.S[ 8] ^= SHA3.toLane(message, 128)
            self.S[13] ^= SHA3.toLane(message, 136)
            self.S[18] ^= SHA3.toLane(message, 144)
            self.S[23] ^= SHA3.toLane(message, 152)
            self.S[ 4] ^= SHA3.toLane(message, 160)
            self.S[ 9] ^= SHA3.toLane(message, 168)
            self.S[14] ^= SHA3.toLane(message, 176)
            self.S[19] ^= SHA3.toLane(message, 184)
            self.S[24] ^= SHA3.toLane(message, 192)
            self.keccakF()
            message = message[128:]
    
    
    def digest(self, msg = None):
        '''
        Absorb the last part of the message and squeeze the Keccak sponge
        
        @param  msg:bytes  The rest of the message
        '''
        if msg is None:
            msg = bytes([])
        message = SHA3.pad10star1(self.M + msg)
        self.M = None
        nnn = len(message)
        rc = [0] * 72
        
        # Absorbing phase
        for i in range(0, nnn, 128):
            self.S[ 0] ^= SHA3.toLane(message, 0)
            self.S[ 5] ^= SHA3.toLane(message, 8)
            self.S[10] ^= SHA3.toLane(message, 16)
            self.S[15] ^= SHA3.toLane(message, 24)
            self.S[20] ^= SHA3.toLane(message, 32)
            self.S[ 1] ^= SHA3.toLane(message, 40)
            self.S[ 6] ^= SHA3.toLane(message, 48)
            self.S[11] ^= SHA3.toLane(message, 56)
            self.S[16] ^= SHA3.toLane(message, 64)
            self.S[21] ^= SHA3.toLane(message, 72)
            self.S[ 2] ^= SHA3.toLane(message, 80)
            self.S[ 7] ^= SHA3.toLane(message, 88)
            self.S[12] ^= SHA3.toLane(message, 96)
            self.S[17] ^= SHA3.toLane(message, 104)
            self.S[22] ^= SHA3.toLane(message, 112)
            self.S[ 3] ^= SHA3.toLane(message, 120)
            self.S[ 8] ^= SHA3.toLane(message, 128)
            self.S[13] ^= SHA3.toLane(message, 136)
            self.S[18] ^= SHA3.toLane(message, 144)
            self.S[23] ^= SHA3.toLane(message, 152)
            self.S[ 4] ^= SHA3.toLane(message, 160)
            self.S[ 9] ^= SHA3.toLane(message, 168)
            self.S[14] ^= SHA3.toLane(message, 176)
            self.S[19] ^= SHA3.toLane(message, 184)
            self.S[24] ^= SHA3.toLane(message, 192)
            self.keccakF()
            message = message[128:]
        
        # Squeezing phase
        ptr = 0
        i = 0
        while i < 9:
            v = self.S[(i % 5) * 5 + i // 5]
            for _ in range(8):
                rc[ptr] = v & 255
                ptr += 1
                v >>= 8
            i += 1
        
        return bytes(rc)
    
    
    def digestFile(self, filename):
        '''
        Calculate the hash sum of an entire file
        
        @param   filename:str  The filename of which to calculate the hash
        @return  :str          The hash sum in uppercase hexadecimal
        '''
        blksize = 8192
        try:
            blksize = os.stat(os.path.realpath(filename)).st_blksize
        except:
            pass
        rc = ''
        with open(filename, 'rb') as file:
            while True:
                chunk = file.read(blksize)
                if len(chunk) == 0:
                    break
                self.update(chunk)
            bs = self.digest()
            for b in bs:
                rc += "0123456789ABCDEF"[b >> 4]
                rc += "0123456789ABCDEF"[b & 15]
        return rc

