"""
This file contains the functions that can be used to produce standardized input files 
for DDEC6 analysis based on charge density distribtions from QE calcualtions.

Some functions for extacting useful data from DDEC analysis results are also listed here

Created by Sizhe @06/15/2020
"""

import os, shutil
from ase.io import read
from collections import Counter

# The dictionary of core electron numbers for common atomic species
# !!! please check if the values below coincide with the parameters in your pseudopotential files.
# Specifically, coure number=atomic number-valence number. And valence number should be in every
# self-respecting pseudopotential file.
CORENUM = {'Li':0,'Na':2,'Cu':10,'Fe':10,'H':0,'K':10,'Mg':2,'N':2,
'Ni':10,'O':2,'Rb':28,'S':10,'Se':28,'Ag':28,'Br':28,'C':2,'Cl':10,'Cs':46}

def redistri_opt(optRoot,a=0,b=6):
    # we use this function to build separate folders for different pp.x calculation cases
    # so that the results of DDEC analysis for each pp.x case will be found in the same folder 
    # with charge density files. Two indices (a,b) are used here to specify similar substrings 
    # in file names. For example, the files 'aabb01.opt' and 'aabb02.in' share the same substring 
    # "aabb" in their names, and we can put them into the same folder by using a=0, b=4.
    # The parameter 'optRoot' is required to tell the function where all the pp.x calc results are stored.
    onlyfiles = [f for f in os.listdir(optRoot) if os.path.isfile(os.path.join(optRoot, f))]
    for f in onlyfiles:
        folderName = f[a:b]
        if not os.path.exists(os.path.join(optRoot,folderName)):
            os.mkdir(folderName)
            shutil.copy(os.path.join(optRoot, f), os.path.join(optRoot,folderName))
        else:
            shutil.copy(os.path.join(optRoot, f), os.path.join(optRoot,folderName))


def prep_DDECipt(iptPath):
    # This function is used to prepare input files for DDEC6 analysis using CUBE files from pp.x calcualtions
    # 'iptPath' tells where the "CUBE" file is stored, and the input file must be named as 'job_control.txt'.
    # Notice that the cube file should also be renamed as 'total_density.cube' in the same folder.
    # !!! Please change "atomic densities directory complete path" in "head" to your DDEC installation!!!
    head = """<net charge>
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
    # change cube file's name into "total_density.cube"
    for f in os.listdir(iptPath):
        if f[-4:]=='cube':
            lst = f.split('//')[:-1]+["total_density.cube"]
            newName = '//'.join(lst)
            os.rename(f,newName)

    # calculate total number of core charges
    data = read(os.path.join(iptPath,"total_density.cube"), format='cube')
    chemical_symbols = Counter(data.get_chemical_symbols())
    coren = 0
    for n,v in chemical_symbols.items():
        coren += v*CORENUM[n]

    # create 'job_control.txt'
    fn = open(os.path.join(iptPath,'job_control.txt'), "w")
    fn.write(head.format(coren))
    fn.close()


def overlap_pop_extract(iptPath, clusterDict):
    # one of the outputs from DDEC analysis is the overlap population, which gives the amount of electrons pairing
    # btw two atoms. Current function calculate the total number of electrons pairing between all possible atom 
    # pairs in atomic clusters defined in 'clusterDict'. 
    popDict = {}
    return popDict