"""
This script prepare files for submitting QE calculation jobs to a high-performance computational
platform running on "slurm" system, and having python3 and intel LAPACK installed. 

!!!Please change the tring "top" if the platform environment you have access to is slightly different.

Currently, this script prepares job files for scf/nscf/relax/bands/dos/pdos/charge density/gw calcs.

Created by Sizhe Liu @University of Illinois at Urbana-Champaign
"""

import os, sys, stat
import glob,random


inbit = ''
qe = ['mpirun  ./pw.x -npool {} -in','mpirun ./dos.x -in', 'mpirun ./projwfc.x -in', 
'mpirun ./pp.x -in','./bands.x -in','mpirun -np {} ./gw.x -npool {} -nimage {} -in']
top = """#!/bin/bash
#SBATCH -n {}
#SBATCH --time={}:{}:00
#SBATCH --job-name="bands"
#SBATCH --partition={}

module load openmpi/4.0.5-gcc-7.2.0
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

print('tell me total number of processors and number of k-point pools, separate them using comma,(e.g., 8,2)')
nodeinfo = input('Type it here:')
if nodeinfo=='':
    ndnum,crnum=12,4
else:
    crnum,ndnum = nodeinfo.split(',')
    ndnum = int(ndnum)
    crnum = int(crnum)

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

top = top.format(crnum,hr,mn,quename,os.getcwd())

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
					qemachine=qe[0].format(ndnum)
				p+=len(filedata)
			p+=1
		filelst[1].append(tempstr)
	elif 'band' in tempstr and 'bands' not in tempstr:
		qemachine=qe[4]
		filelst[3].append(tempstr)
	elif 'bands' in tempstr or 'gw' in tempstr:
		if 'gw' in tempstr:
			if ndnum*crnum%8!=0:
				print('!!!number of processors should be multiple of 8!!!')
				continue
			qemachine = qe[5].format(ndnum*crnum,8,ndnum*crnum//8)
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
