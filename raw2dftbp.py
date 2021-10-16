"""
Functions for creating input file of DFTB+
Created by Sizhe Liu @IBM
"""

from collections import defaultdict
from ase.io import read, write
import os, glob,shutil
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
        'LatticeOpt':'No',
        'Isotropic': 'No',
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
            'Prefix':'./',
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
            'mtx':[[1,0,0],[0,1,0],[0,0,1],[0.0,0.0,0.0]],
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
        elif isinstance(v,list) and isinstance(v[0],float):
            text+=k+' = '+'\t'.join(str(vv) for vv in v) +'\n'
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

def prep_dftb_input(svpath,cifpath='',genpath='',params='3ob-3-1',args={}):
    # prepare input dictionary
    ## prepare geometry card
    iptdict = deepcopy(DEFAULTDICT)
    if not os.path.isdir(svpath):
        os.mkdir(svpath)
    if not cifpath and not genpath:
        print('Give me at least one path to look for cif(cifpath) or gen(genpath) file')
        return None
    elif not cifpath:
        shutil.copy2(genpath,svpath)
        iptdict['Geometry']['<<< ']=os.path.split(genpath)[1]
        atoms = read(genpath)
    elif not genpath:
        temp = glob.glob(cifpath)[0]
        atoms = read(temp)
        filname = os.path.split(temp.replace('\\','/'))[1] # in case of windows os
        write(os.path.join(svpath,filname.split('.')[0]+'.gen'),atoms)
        iptdict['Geometry']['<<< ']=filname.split('.')[0]+'.gen'
    else:
        iptdict['Geometry']['<<< ']=os.path.split(genpath)[1]
        atoms = read(glob.glob(genpath)[0])
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
    if 'Dispersion' in args and args['Dispersion'] =='Yes':
        iptdict['Hamiltonian']['Dispersion'] = hamParams['Dispersion']
    elif 'Dispersion-3B' in args and args['Dispersion-3B'] =='Yes':
        iptdict['Hamiltonian']['Dispersion'] = hamParams['Dispersion']
        iptdict['Hamiltonian']['Dispersion']['Threebody']='Yes'
        iptdict['Hamiltonian']['Dispersion']['HHRepulsion']='Yes'
    if atmtp=={'O','N','Cl','Br','I'}:
        iptdict['Hamiltonian']['HalogenXCorr'] = hamParams['HalogenXCorr']
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
    with open(os.path.join(svpath,os.path.split(iptdict['Geometry']['<<< '])[1][:-4]+'.hsd'),'w') as f:
        f.write(txt)
    f.close()

def prep_waveplot_input():
    return


if __name__=='__main__':
    pass