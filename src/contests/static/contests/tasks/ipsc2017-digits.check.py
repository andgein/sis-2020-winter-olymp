#!/usr/bin/env python3

import sys

def wrong(msg):
    print(msg)
    sys.exit(1)

with open(sys.argv[1], 'rb') as f: our_in = f.read().split()
with open(sys.argv[2], 'rb') as f: their_out = f.read().split()

our_in = [int(r) for r in our_in]

try:
    their_out = [int(r) for r in their_out]
except Exception:
    wrong('Wrong answer: Output file should only contain integers')

their_pos = 0

def readnext():
    global their_pos
    if their_pos >= len(their_out): wrong('Wrong answer')
    r = their_out[their_pos]
    their_pos += 1
    return r

assert our_in[0]+1 == len(our_in)
our_in = our_in[1:]

def neopakuje(cis):
    s = str(cis)
    return len(s) == len(set(s))

for testcase in our_in:
    if neopakuje(testcase):
        if readnext() != 1: wrong('Wrong answer')
        if readnext() != testcase: wrong('Wrong answer')
    else:
        if readnext() != 2: wrong('Wrong answer')
        a = readnext()
        b = readnext()
        if not (neopakuje(a) and neopakuje(b) and a > 0 and b > 0 and a+b == testcase):
            wrong('Wrong answer')

print('OK')
