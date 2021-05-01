"""
This script checks the integrity of QE output files. Any output file ends with 
the strings in "check" list are considered as incomplete, and files do not end with 
strings in "check2" list are also considered as incomplete. The code will then delete 
the input files for completed jobs and leave the input files of incomplete jobs intact.

To use this script, simply copy it to the folder where you save both input and output files

Created/maintained by Sizhe Liu
"""

import glob,os,time

keyword = input('Tell me a keyword in output file names:')
files = glob.glob('*{}*.out'.format(keyword))
ans = input('Remove slurm-related output files?(Y/N):')
print('Tell me the shortest time interval between now and '+ 
'the latest modification time of the jobs for restart (default is 1hrs).')
latest = input('Type it here: ')
if latest == '':
    latest = 1
else:
    latest = int(latest)
# Things you don't want to see at the end of output files
check = ['convergence NOT achieved','%%%%%']
# Thins you want to see them all at the end of complete output files
check2 = ['JOB DONE.']
# A list of files that are ready to restart
rslst = []
# A list of input files that need to be modified
mdlst = []
# A list of files that are complete
cplst = []
for i,f in enumerate(files):
    kpflg = False
    with open(f,'r') as cc:
        content = cc.readlines()
        cc.close()
    if len(content)<200:
        kpflg=True # flag for keeping input files
    
    else:
        temp = content[-200:]
        for i, c in enumerate(check):
            if any([c in t for t in temp]):
                tempname = '.'.join(f.split('.')[:-1]+['in'])
                if tempname not in mdlst:
                    mdlst.append(tempname)
                kpflg = True

        checklst = [False for i in range(len(check2))]
        for i, c2 in enumerate(check2):
            if any([c2 in t for t in temp]):
                checklst[i] = True
            else:
                checklst[i] = False
        if not all(checklst):
            kpflg = True
# incomplete output files that are last modified x hrs ago are ready to be restarted
    if kpflg and (time.time()-os.stat(f).st_mtime)/3600>latest:
        rslst.append('.'.join(f.split('.')[:-1]+['in']))

    if not kpflg:
        temp = f.split('.')[:-1]+['in']
        try:
            os.remove('.'.join(temp))
        except:
            pass
        cplst.append(f)

# Create a text file that record all the cases that need restart
rsfile = open('restart.txt','w')
for r in rslst:
    rsfile.write(r+'\n')
rsfile.close()

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