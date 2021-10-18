"""
Functions for creating input file of DFTB+
Created by Sizhe Liu @IBM
"""

from ase.io import read, write
import os, glob, subprocess #shutil
from copy import deepcopy
import sys,pprint,numbers


# Parameters for hamiltonian
PARAMS = {
    '3ob-3-1':{
        'HubbardDerivs':{
            'H':-0.1857,'Mg':-0.02,
            'C':-0.1492,'N':-0.1535,
            'Ca':-0.0340,'Na':-0.0454,
            'O':-0.1575,'F':-0.1623,
            'K':-0.0339,'Br':-0.0573,
            'Cl':-0.0697,'P':-0.14,
            'S':-0.11,'I':-0.0433,
            'Zn':-0.03
        },
        'MaxAngularMomentum':{
            's':['H'],
            'p':['Mg','C','N','Ca','Na','O','F','K'],
            'd':['Br','Cl','P','S','I','Zn']
        },
        'Dispersion':{'header':'DftD3',
            'Damping':{'header':'BeckeJohnson', 'a1': 0.746,'a2':4.191},
            's8':3.209,
            'Threebody':'No',
            'HHRepulsion':'No'
        },
        # Damping method modifies the short range contribution to the SCC interaction between atoms A and B 
        'HCorrection':{'header':'Damping','Exponent':4.0},
        # The HalogenXCorr keyword includes the halogen correction. This is fitted for the DFTB3-D3 model 
        # and the 3ob-3-1 parameter set. The correction is only relevant for systems including interactions 
        # between {O,N}–{Cl,Br,I} pairs of atoms.
        # !!! The following parameters will appear if {O,N}–{Cl,Br,I} pairs exist in the system
        'HalogenXCorr':{ # 
            'c1': 7.761,'c2': 0.050,'c3': 4.518,
            'O-Cl': 1.237,'O-Br': 1.099,'O-I': 1.313,
            'N-Cl': 1.526,'N-Br': 1.349,'N-I': 1.521
        }
    }
}

# Templates for setting SpinPolarisation in Hamiltonian card
SPIN_TEMPLATE = {
    'Colinear':{
        'header':'Colinear',
        'UnpairedElectrons':0.0,'RelaxTotalSpin':'No',
        'InitialSpins':[{'header':'AtomSpin','Atoms':'1:-1', 'SpinPerAtom': 0.0}]
    },
    'NonColinear':{
        'header':'NonColinear',
        # SpinPerAtom in this case must be an unitary vector
        'InitialSpins':[{'header':'AtomSpin','Atoms':'1:-1', 'SpinPerAtom': [0.0,0.0,1.0]}]
    }
}

DEFAULTDICT = {
    'Geometry':{
        'header':'GenFormat', # read from gen file
        '<<< ':'dummy.gen'
        },

    'Driver':{
        'header':'ConjugateGradient',
        # 'LatticeOpt':'No', # uncomment these two lines for cell relaxation.
        # 'Isotropic': 'No',
        'MovedAtoms':'1:-1', # All atoms
        'MaxForceComponent':1E-4, # Ha/Bohr=0.5Ry/Bohr
        'MaxSteps':100,
        'OutputPrefix':"geom.out"
    },

    'Hamiltonian':{
        'header':'DFTB',
        'SCC':'Yes',
        'SCCTolerance':1e-8,
        # the old standard DFTB code was not orbitally resolved, so that only 
        # the Hubbard U for the s-shell was used. Please check the documentation of 
        # the SK-files you intend to use as to whether they are compatible with 
        # an orbitally resolved SCC calculation.
        'ShellResolvedSCC':'No',
        'SlaterKosterFiles':{
            'header':'Type2FileNames',
            'Prefix':'/u/sizheliu/3ob-3-1/',
            'Separator': "-", # Dash between type names
            'Suffix': ".skf"
        },
        'MaxAngularMomentum': {'H':'s'},
        # Enable DFTB3 calculation, if yes, HubbardDerivs and HCorrection must be set
        'ThirdOrderFull':'Yes', 
        'HubbardDerivs':{'H':-0.1857},
        'HCorrection':{'header':'Damping','Exponent':4.0},
        'KPointsAndWeights':{
            'header':'SupercellFolding',
            # for cubic cell s_i is 0.0, if l_i is odd, and s_i is 0.5 if l_i is even.
            # for hexagonal cell s_3 is 0.5, and s_1 and s_2 are 0.0 regardless of vlues of l_1 and l_2
            'mtx':[ 
                [1,0,0], #l1
                [0,1,0], #l2
                [0,0,1], #l3
                [0.0,0.0,0.0] #s1 s2 s3
            ],
        },
    },

    'Options':{
        # Store charge information as text file
        'WriteChargesAsText':'Yes',
        # Save XML for charge density calculation
        'WriteDetailedXML':'Yes',
    },

    'Analysis':{
        'CalculateForces':'Yes',
        # Required by waveplot
        'WriteEigenvectors':'Yes',
        # Setting PDOS spectra
        'ProjectStates':{
            'header':'', # No header needed here, it will print as ProjectStates={}
            'Region':[{'header':'','Atoms':'1:-1','OrbitalResolved':'No'}]
        }
    },

    'ParserOptions':{
        'ParserVersion':7
    },
    # commend this line if you wish to run jobs in serial fashion
    # make sure you set OMP_NUM_THREADS before you run the job in parallel.
    # also, if gamma k-point scheme is used, groups must set to be 1
    'Parallel':{'Groups':1,'UseOmpThreads':'Yes'} 
}

WAVEPLOTDICT = {
  'Options':{
    'TotalChargeDensity': 'Yes',           # Total density be plotted?
    'PlottedLevels':'1:-1',
    'PlottedKPoints':1,
    'PlottedSpins':1, # use 1 2 if spin polarized
    'PlottedRegion':{'header':'Unitcell','MinEdgeLength [Bohr]':2.0},
    'NrOfPoints':{' ':[50, 50, 50]},             # Number of grid points in each direction
    'NrOfCachedGrids': -1,               # Nr of cached grids (speeds up things)
    'Verbose':'Yes'                      # Wanna see a lot of messages?
    },

    'DetailedXml': "detailed.xml",        # File containing the detailed xml output of DFTB+
    'EigenvecBin': "eigenvec.bin",
    'Basis':{'Resolution': 0.01,
  # Can be downloaded from dftb.org
  '<<+ ':"/u/sizheliu/3ob-3-1/wfc.3ob-3-1.hsd"
  }
}

def rec_reader(d,lb=-1,rb=0): # prepare input text recursively
    text = ''
    if 'header' in d.keys():
        text+=' = '+d['header']+'{\n'
        lb+=1
    elif lb>=0:
        text+='{\n'
        lb+=1
    else:
        lb+=1
    for k,v in d.items():
        if isinstance(v,dict):
            lb,rb,temp=rec_reader(v,lb,rb)
            text += k+temp
            if lb>rb:
                text+='}\n'
                rb+=1
            elif rb>lb:
                text+='{\n'
                lb+=1
        elif isinstance(v,list) and isinstance(v[0],list):
            text+='\n'.join('\t'.join(str(vvv) for vvv in vv) for vv in v)+'\n'
        elif isinstance(v,list) and isinstance(v[0],numbers.Number):
            text+=k+ ' = ' if k != ' ' else ' ' +'\t'.join(str(vv) for vv in v) +'\n'
        elif isinstance(v,list) and isinstance(v[0],dict):
            for vv in v:
                lb,rb,temp=rec_reader(vv,lb,rb)
                text += k+temp
                if lb>rb:
                    text+='}\n'
                    rb+=1
                elif rb>lb:
                    text+='{\n'
                    lb+=1
        elif k!='header':
            if '<' not in k:
                if isinstance(v,str) and v not in ['No','Yes'] and not any(c.isdigit() for c in v):
                    text+=k+' = "'+str(v)+'"\n'
                else:
                    text+=k+' = '+str(v)+'\n'
            else:
                text+=k+str(v)+'\n'
    return lb,rb,text

def prep_dftb_input(svpath,genpath='',params='3ob-3-1',args={}):
    # prepare input dictionary
    ## prepare geometry card
    iptdict = deepcopy(DEFAULTDICT)
    if not os.path.isdir(svpath):
        os.mkdir(svpath)
    if  not genpath:
        print('Give me at least a path to look for cif or gen file')
        return None
    elif genpath.endswith('.gen'):
        # shutil.copy2(genpath,svpath)
        subprocess.call(["cp",genpath,os.path.join(svpath,os.path.split(genpath)[-1])], shell=True)
        iptdict['Geometry']['<<< ']='"'+os.path.split(genpath)[1]+'"'
        atoms = read(genpath)
    elif genpath.endswith('.cif'):
        atoms = read(genpath)
        filname = os.path.split(genpath.replace('\\','/'))[1] # in case of windows os
        iptdict['Geometry']['<<< ']='"'+filname.split('.')[0]+'.gen'+'"'
        write(os.path.join(svpath,filname.split('.')[0]+'.gen'),atoms)
    else:
        print('No cif or gen file found!!')
        return None
    
    ## update essential input cards
    for key in ['Driver','Hamiltonian','Options','Analysis','PaeserOptions']:
        if key in args.keys():
            iptdict[key].update(args[key])
    
    ## update Hamiltonian params
    atmtp = set(atoms.get_chemical_symbols())
    hamParams = PARAMS[params]
    if iptdict['Hamiltonian']['ThirdOrderFull']=='Yes':
        for a in atmtp:
            iptdict['Hamiltonian']['HubbardDerivs'][a] = hamParams['HubbardDerivs'][a]
            for _k in hamParams['MaxAngularMomentum'].keys():
                if a in hamParams['MaxAngularMomentum'][_k]:
                    iptdict['Hamiltonian']['MaxAngularMomentum'][a] = _k
    if atmtp=={'O','N','Cl','Br','I'}:
        iptdict['Hamiltonian']['HalogenXCorr'] = hamParams['HalogenXCorr']
    
    ## Read additional command from user input
    ## Currently only dispersion correction and spin polarization is implemented
    if 'Dispersion' in args:
        iptdict['Hamiltonian']['Dispersion'] = hamParams['Dispersion']
    elif 'Dispersion-3B' in args:
        iptdict['Hamiltonian']['Dispersion'] = hamParams['Dispersion']
        iptdict['Hamiltonian']['Dispersion']['Threebody']='Yes'
        iptdict['Hamiltonian']['Dispersion']['HHRepulsion']='Yes'
    
    if 'Spin' in args:
        iptdict['Hamiltonian']['SpinPolarisation'] = {}
        if args['Spin'].lower()=='noncolinear':
            iptdict['Hamiltonian']['SpinPolarisation']=SPIN_TEMPLATE['NonColinear']
        else:
            iptdict['Hamiltonian']['SpinPolarisation']=SPIN_TEMPLATE['Colinear']
            if 'relax' in args['Spin'].lower():
                iptdict['Hamiltonian']['SpinPolarisation']['RelaxTotalSpin'] = 'Yes'
            
    # Write input texts
    l,r,txt = rec_reader(iptdict)
    if l!=r:
        print('Numbers of left and right brackets do not match!')
    with open(os.path.join(svpath,'dftb_in.hsd'),'w') as f:
        f.write(txt)
    f.close()

# prepare input for waveplot (total density distribution calc)
def prep_waveplot_input(svpath):
    l,r,txt = rec_reader(WAVEPLOTDICT)
    if l!=r:
        print('Numbers of left and right brackets do not match!')
    with open(os.path.join(svpath,'waveplot_in.hsd'),'w') as f:
        f.write(txt)
    f.close()


# User input dictionary
USRIPT = {
    '--dispersion':{'Dispersion':'Yes'},
    '--dispersion-3b':{'Dispersion-3B':'Yes'},
    '--colinear':{'Spin':'Colinear'},
    '--colinear-rlx':{'Spin':'Colinear','RelaxTotalSpin':'Yes'},
    '--noncolinear':{'Spin':'NonColinear'},
    '-h':"""
    -dict        show default settings for DFTB+ calculation
    -spindict    show default spin settings for DFTB+ calculation
    -setlst      show a list of available control for turn on advanced feature of DFTB+
    !!! To prep input.hsd, type "python raw2dftbp.py (--set1) (--set2) /path/to/saving/dir/ (path/to/cif(gen)/file)"
    !!!If cif(gen) path not given, input file will be saved in first directory
    """,
    '-dict':pprint.pformat(DEFAULTDICT),
    '-spindict':pprint.pformat(SPIN_TEMPLATE),
    '-setlst':"""
    You can turn on dispersion correction and/or spin polarization by typing:
    --dispersion     dispersion correction without 3-body correction
    --dispersion-3b  dispersion correction with 3-body correction
    --colinear       colinear spin polarization without total spin relaxation
    --colinear-rlx   colinear spin polarization with total spin relaxation
    --noncolinear    noncolinear spin polarization
    """
}

if __name__=='__main__':
    sysargv = sys.argv
    if not sysargv[1].startswith('--'):
        if len(sysargv)==3:
            prep_dftb_input(sysargv[-2],genpath=sysargv[-1])
            prep_waveplot_input(sysargv[-2])
        else:
            ciffiles = glob.glob(os.path.join(sysargv[-1],'*.cif'))
            genfiles = glob.glob(os.path.join(sysargv[-1],'*.gen'))
            if not ciffiles and not genfiles:
                print('No cif or gen file found!')
            elif not ciffiles:
                prep_dftb_input(sysargv[-1],genpath=genfiles[0])
            else:
                prep_dftb_input(sysargv[-1],genpath=ciffiles[0])
            prep_waveplot_input(sysargv[-1])
    elif sysargv[1].startswith('--'):
        usrargs = {}
        usrargs.update(USRIPT[sysargv[1]])
        if sysargv[2].startswith('--'):
            usrargs.update(USRIPT[sysargv[2]])

        # Prepare input files
        if sysargv[-1].split('.')[-1] in ['cif','gen']:
            svpath = sysargv[-2]
            prep_waveplot_input(svpath)
            if sysargv[-1].endswith('gen'):
                genpath = sysargv[-1]
                prep_dftb_input(svpath,genpath=genpath,args=usrargs)
            elif sysargv[-1].endswith('cif'):
                cifpath = sysargv[-1]
                prep_dftb_input(svpath,genpath=cifpath,args=usrargs)
        elif not sysargv[-1].startswith('--'):
            ciffiles = glob.glob(os.path.join(sysargv[-1],'*.cif'))
            genfiles = glob.glob(os.path.join(sysargv[-1],'*.gen'))
            if not ciffiles and not genfiles:
                print('No cif or gen file found!')
            elif not ciffiles:
                prep_dftb_input(sysargv[-1],genpath=genfiles[0],args=usrargs)
            else:
                prep_dftb_input(sysargv[-1],genpath=ciffiles[0],args=usrargs)
            prep_waveplot_input(sysargv[-1])
        else:
            print('No path info is given!')