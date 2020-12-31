import os, sys, stat
import glob,random


inbit = ''
qe = ['mpirun  ./pw.x -npool 8 -in','./dos.x -in', './projwfc.x -in', 
'mpirun ./pp.x -in','./bands.x -in']
top = """#!/bin/bash
#SBATCH --nodes={}
#SBATCH --ntasks-per-node={}
#SBATCH --time={}:{}:00
#SBATCH --job-name="rlx"
#SBATCH --partition={}


module load python/3
module load intel/18.0
cd {}

# make a private copy of the potentials in the RAM disk
# aprun -n8 -N1 cp -a /home/$USER/pseudo /dev/shm/pseudo

"""

depname = 'serialjob'
svpath = os.getcwd()
os.chdir(svpath)
jobs = open(os.path.join(svpath, depname), 'w')
p = 0
filelst = [[], [], [], [], [], [], [], []]
print('Tell me what\'s in the names of input files,the code will search files with "*string*.in"')
iptformat=input('Type it here:')
if iptformat=='':
    iptformat='*.in'
else:
    iptformat='*'+iptformat+'*.in'

print('tell me number of nodes(<=8) and number of cores per node(<=20), separated by comma(default is 4,12)')
nodeinfo = input('Type it here:')
if nodeinfo=='':
    ndnum,crnum=4,12
else:
    ndnum,crnum = nodeinfo.split(',')
print('tell me the walltime you want to request,and separate hr and min using comma(<=4hrs, default is 3hr)')

waltinfo = input('Type it here(e.g. 3,20):')
if waltinfo=='':
    hr,mn = '3','00'
else:
	hr,mn = waltinfo.split(',')
	if int(hr)<10:
		hr='0'+hr
	if int(mn)<10:
		mn = '0'+mn

quename = input('Tell me the queue name(default is beckman):')
if quename=='':
    quename = 'beckman'

top = top.format(ndnum,crnum,hr,mn,quename,os.getcwd())

WINDOWS_LINE_ENDING = b'\r\n'
UNIX_LINE_ENDING = b'\n'

for file in glob.glob(iptformat):

	with open(file, 'rb') as f:
		filedata = f.read()
	filedata.replace(WINDOWS_LINE_ENDING, UNIX_LINE_ENDING)
	# Write the file out again
	with open(file, 'wb') as f:
		f.write(filedata)
	# we run jobs in a sequence of '(vc-)rlx->restart->bands->band->nscf->dos->pdos->pp_rho'
	tempstr = file[:-3]+'.sbatch'
	if 'pdos' in tempstr:
		qemachine=qe[2]
		filelst[6].append(tempstr)
	elif 'dos' in tempstr:
		qemachine=qe[1]
		filelst[5].append(tempstr)
	elif 'nscf' in tempstr:
		qemachine=qe[0]
		filelst[4].append(tempstr)
	elif 'pp' in tempstr:
		qemachine=qe[3]
		filelst[7].append(tempstr)
	elif 'restart' in tempstr:
		qemachine=qe[0]
		filelst[1].append(tempstr)
	elif 'band' in tempstr and 'bands' not in tempstr:
		qemachine=qe[-1]
		filelst[3].append(tempstr)
	elif 'bands' in tempstr:
		qemachine=qe[0]
		filelst[2].append(tempstr)
	else:
		qemachine=qe[0]
		filelst[0].append(tempstr)
	
	content = top + ' ' + file +'\n\n'
	content = content + '{} {} > {}.out \n'.format(qemachine, file, file[:-3])
	pbs = open(os.path.join(svpath,tempstr), 'w')
	pbs.write(content)
	pbs.close()

lb2 = int(100+random.random()*1000)
initflg = list(map(bool, filelst)).index(True)
for i in range(len(filelst)):
	for j in range(len(filelst[i])):
		if initflg==i:
			if 'restart' in filelst[i][j]:
				repnum = input('how many times do you wanna restart it?(default is 1):')
				if repnum=='' or repnum=='1':
					jobs.write('JOB_{}=`sbatch {} |cut -f 4 -d " "`\n'.format(lb2, filelst[i][j]))
					lb2+=1
				elif int(repnum)>1:
					print('"restart job" is sent into a job array, might cause running error!')
					jobs.write('JOB_{}=`sbatch --array 1-{} --dependency=afterany:$JOB_{} {} |cut -f 4 -d " "`\n'.format(lb2,int(repnum),lb2-1,filelst[i][j]))
					lb2+=1
			else:
				jobs.write('JOB_{}=`sbatch {} |cut -f 4 -d " "`\n'.format(lb2, filelst[i][j]))
				lb2+=1
		else:
			jobs.write('JOB_{}=`sbatch --dependency=afterany:$JOB_{} {} |cut -f 4 -d " "`\n'.format(lb2,lb2-1,filelst[i][j]))
			lb2+=1
			if 'restart' in filelst[i][j]:
				repnum = input('how many times do you wanna restart it?(default is 1):')
				if repnum=='' or repnum=='1':
					continue
				else:
					print('"restart job" is sent into a job array, might cause running error!')
					jobs.write('JOB_{}=`sbatch --array 1-{} --dependency=afterany:$JOB_{} {} |cut -f 4 -d " "`\n'.format(lb2,int(repnum),lb2-1,filelst[i][j]))
					lb2+=1

jobs.close()
os.chmod(depname, stat.S_IRWXU)
