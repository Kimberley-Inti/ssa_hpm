#!/usr/bin/env python3
import unittest
from reference import Classifier
class Rules(unittest.TestCase):
    def seq(self, addresses, want, **kw):
        c=Classifier(); self.assertEqual([c.observe(1,100,a,**kw) for a in addresses],want.split())
    def test_scalar(self): self.seq([0,0,0,0], 'warmup warmup scalar scalar')
    def test_stream(self): self.seq([0,8,16,24], 'warmup warmup stream stream')
    def test_negative(self): self.seq([32,24,16,8], 'warmup warmup stream stream')
    def test_irregular(self): self.seq([0,32,8,80,0], 'warmup warmup irregular irregular irregular')
    def test_switch(self): self.seq([0,0,0,8,16,24], 'warmup warmup scalar irregular stream stream')
    def test_large(self): self.seq([0,8192,16384], 'warmup warmup irregular')
    def test_alignment(self): self.seq([0,3,6], 'warmup warmup irregular')
    def test_interleave(self):
        c=Classifier()
        for i in range(4):
            for pc in (100,104): self.assertEqual(c.observe(1,pc,i*8), 'warmup' if i<2 else 'stream')
    def test_context_and_resume(self):
        c=Classifier(); c.observe(1,100,0); c.observe(2,100,999); c.observe(1,100,8)
        self.assertEqual(c.observe(1,100,16),'stream')
        self.assertEqual(c.observe(2,100,999),'warmup')
    def test_same_pc_mixed_streams(self):
        self.seq([0,4096,8,4104,16,4112], 'warmup warmup irregular irregular irregular irregular')
    def test_distinct_pc_scalar_and_stream(self):
        c=Classifier();actual=[]
        for i in range(4):
            actual += [c.observe(1,100,i*8),c.observe(1,104,4096)]
        self.assertEqual(actual,'warmup warmup warmup warmup stream scalar stream scalar'.split())
    def test_eviction(self):
        c=Classifier(2)
        for pc in (100,104,108): c.observe(1,pc,0)
        self.assertEqual(c.evictions,1);self.assertEqual(c.observe(1,100,0),'warmup')
    def test_boundaries(self):
        c=Classifier();self.assertEqual(c.observe(64,100,0),'dropped'); self.assertEqual(c.observe(0,100,0),'dropped')
    def test_wrap(self): self.seq([(1<<64)-16,(1<<64)-8,0,8], 'warmup warmup stream stream')
if __name__=='__main__': unittest.main()
