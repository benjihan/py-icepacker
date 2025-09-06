#! /usr/bin/env python3
#
# @file   tests/test_icepack.py
# @author  Ben "G" Han
# @brief   icepack python module test script.

import unittest, random
from icepack import Icepack, IcepackError

class TestIcepack(unittest.TestCase):
    def test_pack_depack(self):
        icepack = Icepack()

        data_set = [ ]
        data_set.append(random.randbytes(1))
        data_set.append(random.randbytes(16))
        data_set.append(random.randbytes(1024))
        data_set.append(random.randbytes(random.randint(2048,65536)))
        with open(__file__,'rb') as inp:
            data_set.append( inp.read() )
        for data in data_set:
            compressed = icepack.pack(data)
            dsize, csize = icepack.depacked_size(compressed)
            self.assertEqual(csize, len(compressed))
            self.assertEqual(dsize, len(data))
            print('inp: %d, out: %d, ratio: %.1f%%' % (dsize, csize, csize * 100 / dsize))
            decompressed = icepack.depack(compressed)
            self.assertEqual(data, decompressed)

if __name__ == "__main__":
    unittest.main()
