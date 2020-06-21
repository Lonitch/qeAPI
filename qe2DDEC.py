"""
This file contains the functions that can be used to produce standardized input files 
for DDEC6 analysis based on charge density distribtions from QE calcualtions.

Some functions for extacting useful data from DDEC analysis results are also listed here

Created by Sizhe @06/15/2020
"""

# !!! You need Python3.5+, scipy, and numpy to run current script !!!

import os, shutil, re
from ase.io import read
from collections import Counter, defaultdict
from scipy.spatial import distance
import numpy as np
import subprocess 

# DDECHEAD is a template for making input files for DDEC analysis
# !!! Please change "atomic densities directory complete path" in "DDECHEAD" to your DDEC installation!!!
DDECHEAD = """<net charge>
{}
</net charge>

<periodicity along A, B, and C vectors>
.true.
.true.
.true.
</periodicity along A, B, and C vectors>

<atomic densities directory complete path>
C:\\Users\\liu_s\\Downloads\\chargemol_09_26_2017\\chargemol_09_26_2017\\atomic_densities\\
</atomic densities directory complete path>

<input filename>
total_density.cube
</input filename>

<charge type>
DDEC6 
</charge type>

<compute BOs>
.true. 
</compute BOs>
"""

# The dictionary of core electron numbers for common atomic species
# !!! please check if the values below coincide with the parameters in your pseudopotential files.
# Specifically, coure number=atomic number-valence number. And valence number should be in every
# self-respecting pseudopotential file.
CORENUM = {'Li':0,'Na':2,'Cu':10,'Fe':10,'H':0,'K':10,'Mg':2,'N':2,
'Ni':10,'O':2,'Rb':28,'S':10,'Se':28,'Ag':28,'Br':28,'C':2,'Cl':10,'Cs':46}

def redistri_opt(optRoot,strlst):
    # we use this function to build separate folders for different pp.x calculation cases
    # so that the results of DDEC analysis for each pp.x case will be found in the same folder 
    # with charge density files. strlst is a list of name string here to specify similar substrings 
    # in file names. For example, the files 'aabb01.opt' and 'aabbf.in' share the same substring 
    # "aabb" from the start, and we can put them into a folder named as 'aabb' by using strlst=['aabb'].
    # On the other hand, 'faabb.in' is not put into 'aabb' folder as it starts with 'f'.
    # The parameter 'optRoot' is required to tell the function where all the pp.x calc results are stored.
    onlyfiles = [f for f in os.listdir(optRoot) if os.path.isfile(os.path.join(optRoot, f))]
    for f in onlyfiles:
        foldername=re.findall(r"(?=(" + '|'.join(strlst) + r"))", f)[0]
        if not os.path.isdir(os.path.join(optRoot,foldername)):
            os.mkdir(os.path.join(optRoot,foldername))
            shutil.move(os.path.join(optRoot, f), os.path.join(optRoot,foldername))
        else:
            shutil.move(os.path.join(optRoot, f), os.path.join(optRoot,foldername))

def prep_DDECipt(iptPath):
    # This function is used to prepare input files for DDEC6 analysis using CUBE files from pp.x calcualtions
    # 'iptPath' tells where the "CUBE" file is stored, and the input file must be named as 'job_control.txt'.
    # Notice that the cube file should also be renamed as 'total_density.cube' in the same folder.

    # change cube file's name into "total_density.cube", if theres is no such file.
    for f in os.listdir(iptPath):
        if f[-4:]=='cube' and 'total_density' not in f:
            # !!!change '//' into '\' when you use this script on Linux system!!!
            os.rename(os.path.join(iptPath,f),os.path.join(iptPath,"total_density.cube"))

    # calculate total number of core charges
    data = read(os.path.join(iptPath,"total_density.cube"), format='cube')
    chemical_symbols = Counter(data.get_chemical_symbols())
    coren = 0
    for n,v in chemical_symbols.items():
        coren += v*CORENUM[n]

    # create 'job_control.txt'
    fn = open(os.path.join(iptPath,'job_control.txt'), "w")
    fn.write(DDECHEAD.format(coren))
    fn.close()

def run_DDEC(iptPath,sourcePath):
    # 'iptPath' is where you store your 'job_control.txt' and 'total_density.cube'
    # 'sourcePath' is the absolute path to the binary file.
    # The iptPath must be a raw path string with single backslashes
    # An example of iptPath in Windows OS: r'C:\User\Documents\H2O' for windows OS
    # An example of iptPath in Linux OS: r'/user/input/H2O'
    # !!! Please do not forget the raw string prefix "r" when you prepare the iptPath strings!!!
    p = subprocess.Popen(sourcePath, universal_newlines=True, stdin=subprocess.PIPE)
    p.communicate(iptPath)
    print('complete!')

def checkme(iptPath):
    # This function should be run if your DDEC analysis was not conducted properly,i.e.no bond-order result is
    # obtained. If the pathes are set correctly when you run the analysis, the reason for incorrect outcome is 
    # mostly related to incorrect setting of 'net charge' in 'job_control.txt'.
    # The function find the number of residual electrons in 'total_cube_DDEC_analysis.output', and add that 
    # number to the "net charge" option of the "job_control.txt" in the same folder.
    # !!!Make sure "job_control.txt" and 'total_cube_DDEC_analysis.output' are in the same folder!!!
    # !!!This function only works when 'checkme' is an integer, i.e., you calculation of the number of core 
    # electrons is wrong
    f = open(os.path.join(iptPath,'total_cube_DDEC_analysis.output')).readlines()
    k = 1
    while k<len(f) and 'checkme' not in f[-k]:
        k+=1
    if k==len(f):
        print('check the format of job_control.txt in {}'.format(iptPath))
    if float(f[-k].split()[-1]).is_integer():
        residual = int(float(f[-k].split()[-1]))
    else:
        print('checkme is not integer')
        residual = float(f[-k].split()[-1])
        
    job = open(os.path.join(iptPath,'job_control.txt')).readlines()[1]
    core = float(job.split()[0])+residual
    new = open(os.path.join(iptPath,'job_control.txt')).readlines()
    new[1]=str(core)+'\n'
    new = ''.join(new)
    f = open(os.path.join(iptPath,'job_control.txt'),'w')
    f.write(new)
    f.close()

    return

def overlap_pop(iptPath, clusterDict):
    # One of the outputs from DDEC is the overlap population analysis, which gives the extent to which the atomic
    # charge distributions of two atoms overlap. The overlap population analysis has been used to evaluate the 
    # bonding modulus in bulk crystalline material. More details can be found here: 
    # http://www.tcm.phy.cam.ac.uk/~mds21/thesis/node23.html.
    # Therefore, the overlap population analysis also tells us how stable a cluster of atoms is. A atomic cluster 
    # with high overlap population tends to remain its shape at finite temperature.
    # Current function calculate the total number of electrons pairing between all possible 
    # atom pairs in atomic clusters defined in 'clusterDict'. 
    # An example of 'clusterDict' could be: 
    # {1:['Na','Ni'],2:[('O','Na'),('N','H')],3:[('O','Ni','O'),('Na','O','Na')]}
    # Note that 'clusterDict' has three entries: 1, 2, and 3. Each entry contains a list of n-body tuples that
    # you wanna study based on the overlap population. 
    # For the 1-body tuple list, this function gives the atomic bond order (BO) for each atom kind. 
    # For the 2-body tuple list, this function counts the total number of electrons bounded between each atom pair.
    # For the 3-body tuple list, this function calculates the number of bounded electrons among each atom triplets.
    # The outcome is 'popDict' which is a list dictionary with each index being n-body tuple.
    # A popDict should have the follwing format:
    # {
    #   'Na':[3,2.8],'Ni':[6], 
    #   ('O','Na'):[1.1,2.2],('N','H'):[0.5,0.2,0.3,0.3,0.5],
    #   3('O','Ni','O'):[6.6],('Na','O','Na'):[3.3]
    # }
    # The meanings of each element in different lists are discussed below

    popDict = {}

    # check if 'total_density.cube' is in the folder specified by 'iptpath'
    # terminate the function if it is not found.
    if 'total_density.cube' not in os.listdir(iptPath):
        print('No total_density.cube is found in the folder!')
        return
    
    # Read file 
    atoms = read(os.path.join(iptPath,"total_density.cube"), format='cube')
    chemical_symbols = defaultdict(list)
    nat = 0 # total number of atoms in the system
    for n,v in enumerate(atoms.get_chemical_symbols()):
        chemical_symbols[v].append(n)
        nat+=1
    
    data = open(os.path.join(iptPath,'overlap_populations.xyz')).readlines()[3:]
    tupleDict= defaultdict(list)
    for line in data:
        lst = line.split()
        tupleDict[(int(lst[0]),int(lst[1]))]=float(lst[-1])
    
    # 1-body overlap population analysis for atomic species listed in clusterDict[1]
    # the results are the overlap populations between targeted atoms and their neighbors
    # For instance, if you have 2 Na atoms in your system, the code below will find the 
    # overlap population for each Na atoms separate. And you will end up with a list of in 
    # popDict[1]['Na'] with two different values in it.
    if 1 in clusterDict.keys():
        for s in clusterDict[1]:
            popDict[s]=[]
            indices = chemical_symbols[s]
            for i in indices:
                op = 0
                for j,v in tupleDict.items():
                    if i==j[0]-1:
                        op+=v
                popDict[s].append(op)

    # 2-body overlap population analysis for atom pairs listed in clusterDict[2]. Unlike 1-body analysis, 
    # here we calculate the overlap populations between two specific kinds of atoms. For example, if you 
    # have 3 A atoms and 2 B atoms and you have a tuple of (A,B) in your clusterDict[2] dictionary, then 
    # in popDict[2] will be a 3-element list with each element corresponding to each A atoms. The value of each 
    # element depends on how many electrons are sharing between each A atom and all of its B neighbors.
    if 2 in clusterDict.keys():
        for s in clusterDict[2]:
            a,b = s
            a_indices,b_indices = chemical_symbols[a],chemical_symbols[b]
            popDict[s]=[]
            for i in a_indices:
                t = [(i+1,p+1) for p in b_indices]
                op = 0
                for j,v in tupleDict.items():
                    if j == t:
                        op+=v
                popDict[s].append(op)

    # 3-body overlap population analysis for atom pairs listed in clusterDict[3]. Each 3-body tuple has its 
    # "center body" at the first place. If the tuple is (A,B,C), then the code below calculates the number 
    # of electrons shared between the nearest neighboring pair: A-B,A-C,and B-C for each A atom.
    if 3 in clusterDict.keys():
        for s in clusterDict[3]:
            a,b,c = s
            a_indices,b_indices,c_indices = chemical_symbols[a],chemical_symbols[b],chemical_symbols[c]
            popDict[s]=[]
            for i in a_indices:
                nnb = np.argmin(distance.cdist(atoms[[i]].get_position()-atoms[b_indices].get_position()))
                nnc = np.argmin(distance.cdist(atoms[[i]].get_position()-atoms[c_indices].get_position()))
                op=0
                for j,v in tupleDict.items():
                    if j in [(i+1,nnb+1), (i+1,nnc+1),(nnb+1,nnc+1)]:
                        op+=v
                popDict[s].append(op)

    # 4-body overlap population analysis for atom pairs listed in clusterDict[4], similar to 3-body analysis
    if 4 in clusterDict.keys():
        for s in clusterDict[4]:
            a,b,c,d = s
            a_indices,b_indices,c_indices = chemical_symbols[a],chemical_symbols[b],chemical_symbols[c]
            d_indices = chemical_symbols[d]
            popDict[s]=[]
            for i in a_indices:
                nnb = np.argmin(distance.cdist(atoms[[i]].get_position()-atoms[b_indices].get_position()))
                nnc = np.argmin(distance.cdist(atoms[[i]].get_position()-atoms[c_indices].get_position()))
                nnd = np.argmin(distance.cdist(atoms[[i]].get_position()-atoms[d_indices].get_position()))
                op=0
                for j,v in tupleDict.items():
                    if j in [(i+1,nnb+1), (i+1,nnc+1),(i+1,nnd+1),(nnb+1,nnc+1),(nnb+1,nnd+1),(nnc+1,nnd+1)]:
                        op+=v
                popDict[s].append(op)
    return popDict

def bond_order(iptpath):
    # Unlike overlap population analysis, the bond order is commonly used to analyze the chemical reactivity of 
    # chemical bonds. For example the electrophilic addition reaction only happens with bonds with bond order equal
    # to 2. It could also help us to identify the formation of bonds, such as hydrogen bonding. 
    # The bond order can be defined as the number of electron pairs that exchange between two atoms due to
    # exchange-correlation effects, and it can be deducible from experiments, see
    # Manz, Thomas A. RSC advances 7.72 (2017): 45552-45581.
    #
    # Current function find the total bond order for all the atoms based on DFT-DDEC6 calculation. It also finds 
    # the contributions to the total bond order from different atomic interactions.
    # The outcome of this function will be a dictionary named as "combDict" with three entries: 'mtx', 'atomNames',
    # and 'totalBO'
    # An example output for a 3-atom system should be like:
    #
    # combDict = {
    #               'mtx':[[0,0.9,0.7],
    #                      [0.9,0,1.1],
    #                      [0.7,1.1,0]],
    #               'atomNames':[A,B,C],
    #               'totalBO':[1.6,2.0,1.8]
    #            }
    # where the list in ith entry contains all the bond order values btw ith atom and all other atoms in the system.
    # The 'atomNames' entry gives chemical symbols of all the atoms in the system starting from the first atom.

    if 'total_density.cube' not in os.listdir(iptpath):
        print('No total_density.cube is found in the folder!')
        return
    
    # Read file 
    data = read(os.path.join(iptpath,"total_density.cube"), format='cube')
    chemical_symbols = data.get_chemical_symbols()
    nat = len(chemical_symbols)
    data = open(os.path.join(iptpath,'DDEC6_even_tempered_bond_orders.xyz')).readlines()
    combDict= defaultdict(list)
    combDict['atomNames']=chemical_symbols
    startline = 0
    while 'Bonded to the' not in data[startline]:
            startline+=1

    combDict['mtx'] = []
    combDict['totalBO'] = []
    for k in range(nat):
        cur = [0]*nat
        while 'Bonded to the' in data[startline]:
            lst = data[startline].split()
            idx = cur[int(lst[12])-1]=float(lst[20])
            startline+=1
        combDict['mtx'].append(cur)
        combDict['totalBO'].append(sum(cur))
        while startline<len(data) and 'Bonded to the' not in data[startline]:
                startline+=1
    
    return combDict

