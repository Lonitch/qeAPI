"""
This script replaces bad settings in QE input files with new ones. Please use this script
after you run the opt_check.py, which generates a list of output files,"modify.txt",
that have "not converged" issue at the end. This script will read the file names from
"modify.txt" or "restart.txt" and replace substring in the input files based on 
user-defined tuples.

Note that if your first input is neither 'r' nor 'm', the code will rewrite 'restart.txt'
with the file names that have your input as part of them. And the code replaces substrings
in the files listed in the new 'restart.txt'.

Each tuple has a format of `old substring,new substring`. If the `old substring` appears
multiple times in input files, you can specify name of the setting that uses 
`old substring` by defining a tuple as `setting name, old substring, new substring`.

To use this script, simply copy it to the folder where you save both input and 
output files and run "python3 ipt_modify.py"

Created/maintained by Sizhe Liu @ UIUC
"""

import os, glob
from collections import defaultdict

print('Tell me which file to look into: "m" for modify.txt and "r" for restart.txt')
look = input('Type it here:')
if look =='m':
    look = 'modify.txt'
elif look =='r':
    look = 'restart.txt'
else:
    print('You just gave me a different input, I will rewrite restart.txt '+
    'with the file names that have your input string in them.')
    files = glob.glob('*'+look+'*.in')
    with open(os.path.join(os.getcwd(),'restart.txt'),'w') as f:
        f.write('\n'.join(files))
    f.close()
    look = 'restart.txt'

pwd = os.getcwd()
good = False
for file in os.listdir(pwd):
        if file.endswith(look):
                good = True

if not good:
    print('No {} was found here!'.format(look))
else:
    with open(os.path.join(pwd,look)) as f:
            content = f.read().split('\n')
    f.close()
    usrdict = defaultdict(list)
    while True:
        print('Tell me a tuple of (setting name),old value,new value, separated using ",".'+
        ' Type Enter if you don\'t have any.')
        usrtuple = input('Type it here:')
        templst = usrtuple.split(',')

        if len(templst)==3:
            k,oldv,v = templst
        elif len(templst)==2:
            k,v = templst
        else:
            break

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