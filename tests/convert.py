#!/usr/bin/env python

import glob
import subprocess
import sys

for filename in glob.glob(sys.argv[1] + '/*.c'):
    print filename
    res = subprocess.call(['gcc', '-O0', '-c', '-o', filename + '.o', filename])
    if res:
        break
    res = subprocess.call(' '.join(['objdump', '-Mintel', '-d', filename + '.o']) + ' > ' + filename + '.deasm', shell=True)
    if res:
        break
    res = subprocess.call(['../edeco.py', '-m', 'x86_64', '--cmap', filename + '.deasm', filename + '.deasm', filename + '.deco'])
    if res:
        break
