#!/usr/bin/env python3
"""Rule 1 independent oracle. Inputs: retired scalar access observations only."""
from collections import OrderedDict
MASK=(1<<64)-1
class Classifier:
    def __init__(self, capacity=16):
        self.capacity=capacity; self.history=OrderedDict(); self.evictions=0
    def observe(self, rid, pc, address, store=0, size=3):
        if not 1 <= rid < 64 or not 0 <= size <= 3:
            return 'dropped'
        key=(rid,pc,store,size)
        if key not in self.history:
            if len(self.history)==self.capacity:
                self.history.popitem(last=False); self.evictions+=1
            self.history[key]=(address,None)
            return 'warmup'
        last,old=self.history[key]
        delta=(address-last)&MASK
        signed=delta if delta < 1<<63 else delta-(1<<64)
        self.history[key]=(address,delta)
        if old is None: return 'warmup'
        if delta==old==0: return 'scalar'
        if delta==old and 0 < abs(signed) <=4096 and signed%(1<<size)==0:
            return 'stream'
        return 'irregular'
