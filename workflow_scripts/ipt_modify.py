"""
This script replaces bad settings in QE input files with new ones. Please use this script
after you run the opt_check.py, which generates a list of output files,"modify.txt",
that have "not converged" issue at the end. This script will read the file names from
"modify.txt" and replace substring in the input files based on user-defined tuples.

Each tuple has a format of `old substring,new substring`. If the `old substring` appears
multiple times in input files, you can specify name of the setting that uses 
`old substring` by defining a tuple as `setting name, old substring, new substring`.

To use this script, simply copy it to the folder where you save both input and 
output files and run "python3 ipt_modify.py"

Created/maintained by Sizhe Liu @ 4/30/2021
"""

import os
from collections import defaultdict

pwd = os.getcwd()
good = False
for file in os.listdir(pwd):
        if file.endswith('modify.txt'):
                good = True

if not good:
    print('No modify.txt was found here!')
else:
    with open(os.path.join(pwd,'modify.txt')) as f:
            content = f.read().split('\n')
    f.close()
    usrdict = defaultdict(list)
    while True:
        print('Tell me a tuple of name,value, separated using ",".'+
        ' Type Enter if you dont have any.')
        usrtuple = input('Type it here:')
        templst = usrtuple.split(',')

        if len(templst)==3:
            k,oldv,v = templst
        elif len(templst)==2:
            k,v = templst
        else:
            break

        boolst = ['True','true','TRUE','False','false','FALSE']
        if any([_a in v for _a in boolst]):
            if 'T' in v or 't' in v:
                v = '.TRUE.'
            else:
                v = '.FLASE.'
        if len(templst)==3:
            usrdict[k] = (oldv,v)
        else:
            usrdict[k]=v
        
    for line in content:
            if line is not '':
                with open(os.path.join(pwd,line)) as ipt:
                    inputcontent = ipt.readlines()
                ipt.close()
                newipt = []
                for entry in inputcontent:
                    flg = False
                    for _a in usrdict.keys():
                        if _a in entry:
                            flg = True
                            if isinstance(usrdict[_a],str):
                                newipt.append(entry.replace(_a,usrdict[_a]))
                            else:
                                newipt.append(entry.replace(usrdict[_a][0],
                                usrdict[_a][1]))
                    if not flg:
                        newipt.append(entry)
                with open(os.path.join(pwd,line),'w') as newf:
                    newf.write(''.join(newipt))
                newf.close()