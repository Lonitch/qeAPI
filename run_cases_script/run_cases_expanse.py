"""
This script prepare files for submitting QE calculation jobs to XSEDE expanse
platform, where python3 and QuantumEspresso are compiled. 

!!!Please change the tring "top" if the platform environment you have access to is slightly different.

Currently, this script prepares job files for 

	scf/nscf/relax/bands/dos/pdos/charge density calcs.

Created by Sizhe Liu @University of Illinois at Urbana-Champaign
"""

import os, stat, re
import glob,random


inbit = ''
qe = [
'mpirun --map-by core --mca btl_openib_if_include "mlx5_2:1" --mca btl openib,self,vader pw.x -npool {} -input ',
'mpirun -np $SLURM_NTASKS dos.x -input ', 
'mpirun  -np $SLURM_NTASKS projwfc.x -input ', 
'mpirun -np $SLURM_NTASKS pp.x -input ',
'mpirun -np $SLURM_NTASKS bands.x -input ']

# output and pseudo dir 
outdir = '/expanse/lustre/scratch/sliu135/temp_project'
pseudodir = '/expanse/home/sliu135/inputdir/pseudo/SSSP_efficiency_pseudos/'

# top for running jobs on expanse

top = """#!/bin/bash
#SBATCH --job-name="qe-mpi"
#SBATCH -o qe.%j.out
#SBATCH -e qe.%j.err
### Change partition if needed
#SBATCH --partition=shared
### Change the following to your allocation ID
#SBATCH -A phy210009p
#SBATCH --nodes=1
#SBATCH --ntasks-per-node={}
#SBATCH --mem-per-cpu=1800M
#SBATCH --export=ALL
#SBATCH -t {}:{}:00

module purge
module load slurm
module load cpu
module load gcc/9.2.0
module load openmpi
module load quantum-espresso/6.7.0-openblas

### Run QE
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

print('tell me number of ntasks(<128 with shared partition) on cpu node')
nodeinfo = input('Type it here:')
print('tell me number of pools for your jobs')
poolinfo = input('Type it here:')
if nodeinfo=='':
        ntask=120
        plnum=8
else:
        ntask = int(nodeinfo)
        plnum = int(poolinfo)

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


top = top.format(ntask,hr,mn,svpath)

WINDOWS_LINE_ENDING = b'\r\n'
UNIX_LINE_ENDING = b'\n'

for file in glob.glob(iptformat):

	with open(file, 'r') as f:
		temp = f.readlines()
	# filedata.replace(WINDOWS_LINE_ENDING, UNIX_LINE_ENDING)
	f.close()
	for i in range(len(temp)):
		if 'outdir' in temp[i]:
			tag = temp[i].split('/')[-1]
			tag = re.sub('[^0-9a-zA-Z]','',tag)
			temp[i]= 'outdir="{}/{}",\n'.format(outdir,tag)
		elif 'pseudo_dir' in temp[i]:
			temp[i]='pseudo_dir="{}",\n'.format(pseudodir)
	# Write the file out again
	with open(file, 'w') as f:
		f.write(''.join(temp))
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
					qemachine=qe[0].format(plnum)
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
					qemachine=qe[0].format(plnum)
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
						qemachine=qe[0].format(plnum)
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
					qemachine=qe[0].format(plnum)
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
