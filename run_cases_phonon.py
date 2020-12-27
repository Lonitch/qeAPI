import os, sys, stat
import glob
import time,random
import fileinput

from numpy.core.fromnumeric import partition

inbit = ''
qe = ['mpirun  ./pw.x -npool 8 -in','mpirun  ./ph.x -npool 8 -in',
'mpirun  ./q2r.x -npool 8 -in','mpirun  ./matdyn.x -npool 8 -in']
top = """#!/bin/bash
#
#!/bin/bash
#PBS -l nodes={}:ppn={}
#PBS -l walltime=0{}:{}:00
#PBS -N rlx
#PBS -j oe
#PBS -q {}
#PBS -p {}

module load python/3
module load intel/18.0
cd {}

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
filelst = [[], [], [], [], [], []]
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
    hr,mn = '3','00'
else:
    hr,mn = waltinfo.split(',')
    if int(hr)>4:
        hr,mn = '04','00'
        print('hr exceeds 4, run with 4hrs instead')
    elif int(mn)<10:
        mn = '0'+mn

quename = input('Tell me the queue name(default is beckman):')
if quename=='':
    quename = 'beckman'

partition = input('Tell me the partition id(1-primary/2-secondary, default is 2):')
if partition=='1':
    partition = 'primary'
else:
    partition = 'secondary'

retag = input('Do you want to add restart file?(y/n):')
if retag=='y' or retag=='Y':
    scffiles = glob.glob('*ph.in')
    for scf in scffiles:
        fn = open(scf, "r")
        lines = fn.readlines()
        lines.insert(3,'recover=.true.,\n')
        fn.close()
        f = open(os.path.split(scf)[-1][:-3]+'_restart.in','w')
        content="".join(lines)
        f.write(content)
        f.close()

top = top.format(ndnum,crnum,hr,mn,quename,partition,os.getcwd())

for file in glob.glob(iptformat):

	with open(file, 'r',encoding='utf8',errors='ignore') as f:
		filedata = f.read()

	# Write the file out again
	with open(file, 'w') as f:
		f.write(filedata)
	# we run jobs in a sequence of 'scf->ph->q2r->matdyn'
	tempstr = file[:-3]+'.pbs'
	if 'scf' in tempstr:
		qemachine=qe[0]
		filelst[0].append(tempstr)
	elif 'ph' in tempstr and 'dos' not in tempstr:
		qemachine=qe[1]
		filelst[1].append(tempstr)
	elif 'q2r' in tempstr:
		qemachine=qe[2]
		filelst[3].append(tempstr)
	elif 'phdos' in tempstr:
		qemachine=qe[3]
		filelst[4].append(tempstr)
	elif 'disp' in tempstr:
		qemachine=qe[3]
		filelst[5].append(tempstr)
	content = top + ' ' + file +'\n\n'
	content = content + '{} {} > {}.out \n'.format(qemachine, file, file[:-3])
	pbs = open(os.path.join(svpath,tempstr), 'w')
	pbs.write(content)
	pbs.close()


lb2 = int(100+random.random()*1000)
for i in range(len(filelst)):
	for j in range(len(filelst[i])):
		if i==0:
			jobs.write('JOB_{}=`qsub {}`\n'.format(lb2, filelst[i][j]))
			lb2+=1
		else:
			jobs.write('JOB_{}=`qsub -W depend=afterany:$JOB_{} {}`\n'.format(lb2,lb2-1,filelst[i][j]))
			lb2+=1
				
jobs.close()
os.chmod(depname, stat.S_IRWXU)
