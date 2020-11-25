import os, sys, stat
import glob
import time
import fileinput

inbit = ''
qe = ['mpirun  ./pw.x -npool 8 -in','mpirun ./dos.x -in', 'mpirun ./projwfc.x -in', 
'mpirun ./pp.x -in']
top = """#!/bin/bash
#
#!/bin/bash
#PBS -l nodes=2:ppn=12
#PBS -l walltime=01:00:00
#PBS -N rlx
#PBS -j oe
#PBS -q eng-research

module load python/3
module load intel/18.0
cd /home/sliu135/inputdir/

# tell me what you are doing
set -x

# make a private copy of the potentials in the RAM disk
# aprun -n8 -N1 cp -a /home/$USER/pseudo /dev/shm/pseudo

"""

depname = 'serialjob'
svpath = os.getcwd()
os.chdir(svpath)
jobs = open(os.path.join(svpath, depname), 'w')
p = 0
filelst = [[], [], [], [],[]]
for file in glob.glob('*.in'):

	with open(file, 'r') as f:
		filedata = f.read()

	# Replace some strings in your input files that you don't like(optional)
	filedata = filedata.replace('"/u/sciteam/liu19/pseudo"', '"/home/sliu135/pseudo"')
	filedata = filedata.replace('ibrav = 0','ibrav = 14')
	filedata = filedata.replace('"/u/sciteam/liu19/scratch"', '"/home/sliu135/scratch/{}"'.format(file[:-3]))

	# Write the file out again
	with open(file, 'w') as f:
		f.write(filedata)

	tempstr = file[:-3]+'.pbs'
	if 'pdos' in tempstr:
		qemachine=qe[2]
		filelst[3].append(tempstr)
	elif 'dos' in tempstr:
		qemachine=qe[1]
		filelst[2].append(tempstr)
	elif 'nscf' in tempstr:
		qemachine=qe[0]
		filelst[1].append(tempstr)
	elif 'pp' in tempstr:
		qemachine=qe[3]
		filelst[4].append(tempstr)
	else:
		qemachine=qe[0]
		filelst[0].append(tempstr)
	content = top + '\n'
	content = content + '{} {} > {}.out \n'.format(qemachine, file, file[:-3])
	pbs = open(os.path.join(svpath,tempstr), 'w')
	pbs.write(content)
	pbs.close()

lb=0
lb2 =1
## The jobs with pw.x is always run first, followed by jobs with dos.x, projwfc.x, and pp.x
for i in range(len(filelst)):
	for j in range(len(filelst[i])):
		if lb==0:
			jobs.write('JOB_{}=`qsub {}`\n'.format(lb2, filelst[i][j]))
			lb2+=1
		elif lb!=0:
			jobs.write('JOB_{}=`qsub -W depend=afterany:$JOB_{} {}`\n'.format(lb2,lb,filelst[i][j]))
			lb2+=1
	lb=lb2-1
				
jobs.close()
os.chmod(depname, stat.S_IRWXU)
