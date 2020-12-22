import os, sys, stat
import glob
import time
import fileinput

inbit = ''
qe = ['mpirun  ./pw.x -npool 8 -in','./dos.x', './projwfc.x', 
'mpirun ./pp.x -in']
top = """#!/bin/bash
#
#!/bin/bash
#PBS -l nodes={}:ppn={}
#PBS -l walltime=0{}:{}:00
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
filelst = [[], [], [], [], [],[]]
print('Tell me what\'s in the names of input files,the code will search files with "*string*.in"')
iptformat=input('Type it here:')
if iptformat=='':
	iptformat='*.in'
else:
	iptformat='*'+iptformat+'*.in'
print('tell me number of nodes and number of cores per node(<=20), separated by comma(default is 4,12)')
nodeinfo = input('Type it here:')
if nodeinfo=='':
	ndnum,crnum=4,12
else:
	ndnum,crnum = nodeinfo.split(',')
print('tell me the walltime you want to request,and separate hr and min using comma(<=4hrs, default is 3hr)')
waltinfo = input('Type it here(e.g. 3,20):')
if waltinfo=='':
	hr,min = '3','00'
else:
	hr,min = waltinfo.split(',')
	if int(hr)>4:
		hr,min = '04','00'
		print('hr exceeds 4, run with 4hrs instead')
	elif int(min)<10:
		min = '0'+min
top = top.format(ndnum,crnum,hr,min)

for file in glob.glob(iptformat):

	with open(file, 'r') as f:
		filedata = f.read()

	# Replace the target string
	filedata = filedata.replace('"/u/sciteam/liu19/pseudo"', '"/home/sliu135/pseudo"')
	filedata = filedata.replace('"/u/sciteam/liu19/scratch"', '"/home/sliu135/scratch/{}"'.format(file[:-3]))

	# Write the file out again
	with open(file, 'w') as f:
		f.write(filedata)

	tempstr = file[:-3]+'.pbs'
	if 'pdos' in tempstr:
		qemachine=qe[2]
		filelst[4].append(tempstr)
	elif 'dos' in tempstr:
		qemachine=qe[1]
		filelst[3].append(tempstr)
	elif 'nscf' in tempstr:
		qemachine=qe[0]
		filelst[2].append(tempstr)
	elif 'pp' in tempstr:
		qemachine=qe[3]
		filelst[5].append(tempstr)
	elif 'restart' in tempstr:
		qemachine=qe[0]
		filelst[1].append(tempstr)
	else:
		qemachine=qe[0]
		filelst[0].append(tempstr)
	content = top + ' ' + file +'\n\n'
	content = content + '{} {} > {}.out \n'.format(qemachine, file, file[:-3])
	pbs = open(os.path.join(svpath,tempstr), 'w')
	pbs.write(content)
	pbs.close()

lb=0
lb2 =1
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
