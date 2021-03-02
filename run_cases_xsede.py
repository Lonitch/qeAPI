"""
This script prepare files for submitting QE calculation jobs to XSEDE platform running on "slurm" system, 
and having python3 and QuantumEspresso installed. 

!!!Please change the tring "top" if the platform environment you have access to is slightly different.

Currently, this script prepares job files for scf/nscf/relax/bands/dos/pdos/charge density/gw calcs.

Created by Sizhe Liu @University of Illinois at Urbana-Champaign
"""

import os, stat
import glob,random


inbit = ''
qe = ['mpirun  -np $SLURM_NTASKS $QuantumEspresso/bin/pw.x < ','$QuantumEspresso/dos.x < ', 
'$QuantumEspresso/bin/projwfc.x < ', 
'mpirun -np $SLURM_NTASKS $QuantumEspresso/bin/pp.x < ',
'$QuantumEspresso/bin/bands.x < ']
top = """#!/bin/bash
#SBATCH -J high-fidelity         # Job name
#SBATCH -o hf.%j.out   # define stdout filename; %j expands to jobid
#SBATCH -e hf.%j.err   # define stderr filename; skip to combine stdout and stderr

#SBATCH --mail-user=sliu135@illinois.edu
#SBATCH --mail-type=END
#SBATCH -A phy210009p     # see the charge ID after "projects" command

#SBATCH -p {}         # specify queue
#SBATCH -N {}          # Number of nodes, not cores (16 cores/node)
#SBATCH -n {}             # Total number of MPI tasks (if omitted, n=N)
#SBATCH -t {}:{}:00       # set maximum run time of 30 minutes

module load QuantumEspresso
export PSEUDO_DIR=/jet/home/sliu135/inputdir/pseudo
export I_MPI_JOB_RESPECT_PROCESS_PLACEMENT=0
export QuantumEspresso=/opt/packages/QuantumEspresso/qe-6.7/INTEL

cd {}

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

print('tell me the name of your partition (default is RM)')
partition = input('Type is here:')
if partition == '':
    partition = 'RM'

print('tell me number of nodes')
nodeinfo = input('Type it here:')
if nodeinfo=='':
    ndnum=8
else:
    ndnum = int(nodeinfo)

print('tell me the walltime you want to request,and separate hr and min using comma(<=48hrs, default is 3hr)')
waltinfo = input('Type it here(e.g. 3,20):')
if waltinfo=='':
    hr,mn = '3','00'
else:
	hr,mn = waltinfo.split(',')
	if int(hr)<10:
		hr='0'+hr
	if int(mn)<10:
		mn = '0'+mn


top = top.format(partition,ndnum,ndnum,hr,mn,svpath)

WINDOWS_LINE_ENDING = b'\r\n'
UNIX_LINE_ENDING = b'\n'

for file in glob.glob(iptformat):

	with open(file, 'rb') as f:
		filedata = f.read()
	filedata.replace(WINDOWS_LINE_ENDING, UNIX_LINE_ENDING)
	f.close()
	# Write the file out again
	with open(file, 'wb') as f:
		f.write(filedata)
	f.close()
	# we run jobs in a sequence of '(vc-)rlx->restart->bands/gw->band->nscf->dos->pdos->pp_rho'
	tempstr = file[:-3]+'.sbatch'
	# tell me which files are found and will be generated!
	print("{}:{}".format(file,tempstr))
	if 'pdos' in tempstr:
		qemachine=qe[2]
		filelst[6].append(tempstr)
	elif 'dos' in tempstr:
		qemachine=qe[1]
		filelst[5].append(tempstr)
	elif 'nscf' in tempstr:
		with open(file, 'r') as f:
			filedata = f.readlines()
		f.close()
		p = 0
		while p< len(filedata):
			if 'K_POINTS' in filedata[p]:
				t1,t2 = filedata[p].split()
				if t2 in ['gamma','Gamma','GAMMA']:
					qemachine=qe[0].format(1)
				else:
					# k1,k2,k3,k4,k5,k6 = filedata[p+1].split()
					# np = int(k1)*int(k2)*int(k3)
					# while crnum*ndnum%np!=0:
					# 	np = np//2
					# qemachine=qe[0].format(np)
					qemachine=qe[0].format(ndnum)
				p+=len(filedata)
			p+=1
		filelst[4].append(tempstr)
	elif 'pp' in tempstr:
		qemachine=qe[3]
		filelst[7].append(tempstr)
	elif 'restart' in tempstr:
		with open(file, 'r') as f:
			filedata = f.readlines()
		f.close()
		p = 0
		while p < len(filedata):
			if 'K_POINTS' in filedata[p]:
				t1,t2 = filedata[p].split()
				if t2 in ['gamma','Gamma','GAMMA']:
					qemachine=qe[0].format(1)
				else:
					# k1,k2,k3,k4,k5,k6 = filedata[p+1].split()
					# np = int(k1)*int(k2)*int(k3)
					# while crnum*ndnum%np!=0:
					# 	np = np//2
					# qemachine=qe[0].format(np)
					qemachine=qe[0].format(ndnum)
				p+=len(filedata)
			p+=1
		filelst[1].append(tempstr)
	elif 'band' in tempstr and 'bands' not in tempstr:
		qemachine=qe[4]
		filelst[3].append(tempstr)
	elif 'bands' in tempstr or 'gw' in tempstr:
		if 'gw' in tempstr:
			pass
		else:
			with open(file, 'r') as f:
				filedata = f.readlines()
			f.close()
			p = 0
			while p < len(filedata):
				if 'K_POINTS' in filedata[p]:
					t1,t2 = filedata[p].split()
					if t2 in ['gamma','Gamma','GAMMA']:
						qemachine=qe[0].format(1)
					else:
						# k1,k2,k3,k4,k5,k6 = filedata[p+1].split()
						# np = int(k1)*int(k2)*int(k3)
						# while crnum*ndnum%np!=0:
						# 	np = np//2
						# qemachine=qe[0].format(np)
						qemachine=qe[0].format(ndnum)
					p+=len(filedata)
				p+=1
		filelst[2].append(tempstr)
	else:
		with open(file, 'r') as f:
			filedata = f.readlines()
		f.close()
		p = 0
		while p < len(filedata):
			if 'K_POINTS' in filedata[p]:
				t1,t2 = filedata[p].split()
				if t2 in ['gamma','Gamma','GAMMA']:
					qemachine=qe[0].format(1)
				else:
					# k1,k2,k3,k4,k5,k6 = filedata[p+1].split()
					# np = int(k1)*int(k2)*int(k3)
					# while crnum*ndnum%np!=0:
					# 	np = np//2
					# qemachine=qe[0].format(np)
					qemachine=qe[0].format(ndnum)
				p+=len(filedata)
			p+=1
		filelst[0].append(tempstr)
	
	content = top + ' ' +'\n\n'
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
					jobs.write('JOB_{}=`sbatch {}`\n'.format(lb2, filelst[i][j]))
					lb2+=1
				elif int(repnum)>1:
					print('"restart job" is sent into a job array, might cause running error!')
					jobs.write('JOB_{}=`sbatch --array 1-{} --dependency=afterany:$JOB_{} {}`\n'.format(lb2,int(repnum),lb2-1,filelst[i][j]))
					lb2+=1
			else:
				jobs.write('JOB_{}=`sbatch {}`\n'.format(lb2, filelst[i][j]))
				lb2+=1
		else:
			jobs.write('JOB_{}=`sbatch --dependency=afterany:$JOB_{} {}`\n'.format(lb2,lb2-1,filelst[i][j]))
			lb2+=1
			if 'restart' in filelst[i][j]:
				repnum = input('how many times do you wanna restart it?(default is 1):')
				if repnum=='' or repnum=='1':
					continue
				else:
					print('"restart job" is sent into a job array, might cause running error!')
					jobs.write('JOB_{}=`sbatch --array 1-{} --dependency=afterany:$JOB_{} {}`\n'.format(lb2,int(repnum),lb2-1,filelst[i][j]))
					lb2+=1

jobs.close()
os.chmod(depname, stat.S_IRWXU)
