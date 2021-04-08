"""
This script checks the integrity of QE output files. Any output file ends with 
the strings in "check" list are considered as incomplete, and files do not end with 
strings in "check2" list are also considered as incomplete. The code will then delete 
the input files for completed jobs and leave the input files of incomplete jobs intact.
"""

import glob,os,sys

keyword = input('Tell me a keyword in output file names:')
files = glob.glob('*{}*.out'.format(keyword))
ans = input('Remove slurm-related output files?(Y/N):')

# Things you don't want to see in complete output files
check = ['convergence NOT achieved','%%%%%%%%%%%%%%%%']
# Thins you want to see in complete output files
check2 = ['JOB DONE.']
for i,f in enumerate(files):
    rmflg = False
    with open(f,'r') as cc:
        content = cc.readlines()
        cc.close()
    if len(content)<200:
        rmflg=True
    else:
        for q in range(1,200):
            if any([_a in content[-q] for _a in check]):
                rmflg=True
            if not any([_a in content[-q] for _a in check2]):
                rmflg=True

    if not rmflg:
        temp = f.split('.')[:-1]+['in']
        os.remove('.'.join(temp))

if ans=='Y' or ans=='y':
    files = glob.glob('slurm*'.format(keyword))
    for f in files:
        os.remove(f)
    files = glob.glob('core*'.format(keyword))
    for f in files:
        os.remove(f)
    files = glob.glob('*.sbatch'.format(keyword))
    for f in files:
        os.remove(f)