"""
This script checks the coexisitance of x.in and x.out files with 'x' being a specific case name.
"""

import glob

ans = input('Keyword in the names of input/output files:')
iptfiles = glob.glob('*'+ans+'*.in')
optfiles = glob.glob('*'+ans+'*.out')

iptcases = []
optcases = []
for i in iptfiles:
    iptcases.append(i[:-3])
for i in optfiles:
    optcases.append(i[:-4])

iToF = [] # x.in exists but x.out does not
iFoT = [] # x.out exists but x.in does not
iToT = [] # both x.in and x.out exist
for i in iptcases:
    if i not in optcases:
        iToF.append(i)
    else:
        iToT.append(i)
for i in optcases:
    if i not in iptcases:
        iFoT.append(i)
    elif i not in iToT:
        iToT.append(i)

res = open('coexist.txt','w')
res.write('!!!x.out exists but x.in does not!!!\n')
for c in iFoT:
    res.write(c+'\n')
res.write('!!!x.in exists but x.out does not!!!\n')
for c in iToF:
    res.write(c+'\n')
res.write('!!!both x.in and x.out exist!!!\n')
for c in iToT:
    res.write(c+'\n')
res.close()