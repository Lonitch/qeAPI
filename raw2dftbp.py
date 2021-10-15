"""
Functions for creating input file of DFTB+
Created by Sizhe Liu @IBM
"""

from collections import defaultdict
from ase.io import read, write
import os, glob
from copy import deepcopy

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
            'params':{
                'Damping':{'header':'BeckeJohnson', 'a1': 0.746,'a2':4.191},
                's8':3.209,
                'Threebody':'No',
                'HHRepulsion':'No'
            }
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
        'UnpairedElectrons':0.0,
        'InitialSpins':[{'header':'AtomSpin','Atoms':'1:-1', 'SpinPerAtom': '0.0'}]
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
        'filename':'<<< '
        },

    'Driver':{
        'header':'ConjugateGradient',
        'LatticeOpt':'No',
        'Isotropic': 'No',
        'MovedAtoms':'1:-1', # All atoms
        'MaxForceComponent':2E-4, # Ha/Bohr=0.5Ry/Bohr
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
            'Prefix':'./',
            'Separator': "-", # Dash between type names
            'Suffix': ".skf"
        },
        'MaxAngularMomentum': {},
        # Enable DFTB3 calculation, if yes, HubbardDerivs and HCorrection must be set
        'ThirdOrderFull':'Yes', 
        'HubbardDerivs':{},
        'HCorrection':{},
        'KPointsAndWeights':{
            'header':'SupercellFolding',
            'mtx':[[1,0,0],[0,1,0],[0,0,1]],
            'wgt':[0.0,0.0,0.0]
        },
        'Dispersion':{}
    },

    'Options':{
        # Store charge information as text file
        'WriteChargesAsText':'Yes',
        # Save XML for charge density calculation
        'WriteDetailedXML':'Yes',
    },

    'Analysis':{
        'CalculateForces':'Yes',
        # Setting PDOS spectra
        'ProjectStates':{
            'header':'', # No header needed here, it will print as ProjectStates={}
            'Region':[{'header':'','Atoms':'1:-1','OrbitalResolved':'No'}]
        }
    },

    'ParserOptions':{
        'ParserVersion':7
    }
}

def prep_dftb_input(cifpath='',genpath='',*arg):
    if not cifpath and not genpath:
        print('Give me at least one path to look for cif or gen file')
        return None
    elif not cifpath:
        iptdict = deepcopy(DEFAULTDICT)
        iptdict['Geometry']['filename']+=glob.glob(os.path.join(genpath,'*.gen'))[0]
    elif not genpath:
        temp = glob.glob(os.path.join(genpath,'*.gen'))[0]
        atoms = read(temp)
        filname = os.path.split(temp.replace('\\','/'))[1] # in case of windows os
        write(os.path.join(cifpath,filname.split('.')[0]+'.gen'),atoms)
        iptdict = deepcopy(DEFAULTDICT)
        iptdict['Geometry']['filename']+=os.path.join(cifpath,filname.split('.')[0]+'.gen')
    else:
        iptdict = deepcopy(DEFAULTDICT)
        iptdict['Geometry']['filename']+=glob.glob(os.path.join(genpath,'*.gen'))[0]
    return

def prep_waveplot_input():
    return