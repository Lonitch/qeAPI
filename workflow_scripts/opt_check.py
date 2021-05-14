"""
This script checks the integrity of QE output files. Any output file ends with 
the strings in "check" list are considered as incomplete, and files do not contain all
the strings in "check2" list are also incomplete. The cases that have thier outputs 
contain any of the strings in "check1" are ready to be restarted. The code will then 
delete the input files for completed jobs and leave the input files of incomplete jobs intact.

The input file names that correspond complete, erroneous, and ready-to-restart cases are
written in the files, "complete.txt","modify.txt", and "restart.txt", respectively.

To use this script, simply copy it to the folder where you save both input and output files

Created/maintained by Sizhe Liu
"""

import glob,os,time
from collections import defaultdict

keyword = input('Tell me a keyword in output file names:')
files = glob.glob('*{}*.out'.format(keyword))
ans = input('Remove slurm-related output files?(Y/N):')
ans2 = input('Remove input files of complete jobs?(Y/N):')
# SCF iteration marker
marker = 'avg # of iterations'
# Things you don't want to see at the end of output files
# The second string in the list below is usually followed by error messages.
check = ['convergence NOT achieved','%%%%%%']
# When the following things shown at end of the outputs, we restart the cases.
# To see "Maximum CPU time exceeded" in the outputs, 
# please set 'max_seconds' in your input files to be less than the max walltime.
check1 = ['Maximum CPU time exceeded']
# Things you want to see them all at the end of complete output files
# For lattice relaxation, we can use 'End final coordinates'(very strict one)
# For SCF calculation, it could be 'JOB DONE' or 'Total force'
check2 = ['JOB DONE']
# A list of files that are ready to restart
rslst = []
# A list of input files that need to be modified
mdlst = []
# A list of files that are complete
cplst = []
for i,f in enumerate(files):
    with open(f,'r') as cc:
        content = cc.readlines()
        cc.close()
    if len(content)<200 and (time.time()-os.stat(f).st_mtime)/3600>0.5:
        tempname = '.'.join(f.split('.')[:-1]+['in'])
        if tempname not in mdlst:
            mdlst.append(tempname)
    
    else:
        temp = content
        checkdict = defaultdict(list)
        totcheck = check+check1+check2+[marker]
        for i,t in enumerate(temp):
            for c in totcheck:
                if c in t:
                    checkdict[c].append(i)
        # We check various messages during the last SCF iteraction
        maxmarker = max(checkdict[marker])
        for c in check+check1+check2:
            checkdict[c][:]=[_x for _x in checkdict[c] if _x>maxmarker]

        checklst = []
        for i,c in enumerate(check):
            if checkdict[c]:
                checklst.append(True)
            else:
                checklst.append(False)
        if any(checklst):
            tempname = '.'.join(f.split('.')[:-1]+['in'])
            if tempname not in mdlst:
                mdlst.append(tempname)

        checklst = []
        for i,c in enumerate(check1):
            if checkdict[c]:
                checklst.append(True)
            else:
                checklst.append(False)
        if any(checklst):
            tempname = '.'.join(f.split('.')[:-1]+['in'])
            if tempname not in rslst and tempname not in mdlst:
                rslst.append(tempname)

        checklst = []
        for i,c in enumerate(check2):
            if checkdict[c]:
                checklst.append(True)
            else:
                checklst.append(False)
        if all(checklst):
            tempname = '.'.join(f.split('.')[:-1]+['in'])
            if tempname not in cplst and tempname not in rslst and tempname not in mdlst:
                cplst.append(tempname)

        # deal with unfinished ends
        if len(content)-maxmarker<10 and (time.time()-os.stat(f).st_mtime)/3600>0.5:
            tempname = '.'.join(f.split('.')[:-1]+['in'])
            if tempname not in rslst and tempname not in mdlst:
                rslst.append(tempname)

# Remove input files corresponding to complete cases. 
if ans2=='Y' or ans2=='y':
    for c in cplst:
        try:
            os.remove(c)
            print('remove {} !!!'.format(c))
        except:
            print('{} is already removed!!!'.format(c))

# Create a text file that record all the cases that need restart
rsfile = open('restart.txt','w')
for r in rslst:
    rsfile.write(r+'\n')
# for m in mdlst:
#     if m not in rslst:
#         rsfile.write(m+'\n')
# rsfile.close()

# Create a text file that keeps names of input files that need their parameters modified
# in order to make calculation converge
mdfile = open('modify.txt','w')
for m in mdlst:
    mdfile.write(m+'\n')
mdfile.close()

# Create a txt file that keeps names of complete output files in "complete.txt" file
cpfile = open('complete.txt','w')
for c in cplst:
    cpfile.write(c+'\n')
cpfile.close()

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