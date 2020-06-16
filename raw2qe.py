"""
This file contains the functions and classes that can be used to produce standardized input files 
for Quantum Espresso from CIF files.

Created by Sizhe @06/15/2020
"""

## !!! The installation of ASE package is required to run the functions in this script
import ase
from ase.io import write,read
from ase.io import Trajectory
from collections import Counter
from copy import deepcopy
import math
import os

# Index of Bravais Lattice
# Current has a function "check_bravais" to assign correct index of bravais lattice to your system,
# where the global variable IBRAV is used. IBRAV contains all possible shortnames for Bravais lattice,
# more information can be found here: https://en.wikipedia.org/wiki/Brillouin_zone.
# The index of "free" lattice is not included. You can also use "update_default" function to change your 
# ibrav to 0 (free lattice).

IBRAV = {'CUB':1,'FCC':2,'BCC':3,'RHL':4,'TET':6,'BCT':7,'ORC':8,'ORCC':9,
         'ORCF':10,'ORCI':11,'MCL':12,'MCLC':13, 'TRI':14}

# HEAD includes all the controling panels that could be set in pw.x input files.
# we can insert options in curly brackets by using default or customized dictionary. Please note that QE will 
# ignore some of the panels listed here depending on the calculation type (e.g, &IONS panel is ignored during 
# SCF calculation).

HEAD = """&CONTROL
{}
/

&SYSTEM
{}
/

&ELECTRONS
{}
/

&IONS
{}
/

ATOMIC_SPECIES
{}

K_POINTS {}
{} {} {} {} {} {}

ATOMIC_POSITIONS angstrom
{}

"""

# HEAD_rho includes an input file template that should be used for charge density calculation with pp.x.
# The format of output is 3-dimensional cube file that can be read by Xcrysden or Vesta.
# The options of "prefix" and "outdir" should match those in inputs for pw.x

HEAD_rho="""&inputpp
	prefix		= "{}"
	filplot		= "{}.charge"
	plot_num 	= 0
	outdir  	= "{}" 
/

&plot
	nfile = 1
	filepp(1) = "{}.charge"
	weight(1) = 1.0
	iflag = 3
	output_format = 6
	fileout = '{}.cube'
/

"""

# HEAD_dos/pdos includes an input file template that should be used for the calculations with dos.x/projwfc.x.
# The options of "prefix" and "outdir" should match those in inputs for pw.x
# It is not required for DOS and PDOS calculations to have the same emax,emin, deltae, but we always use identical 
# values to make final results consistent.

HEAD_dos ="""&DOS
	prefix		= "{}",
    outdir      = "{}",
    fildos  =  '{}_dos.dat',
    emax        = 30,
    emin        = -30,
    deltae      = 0.05,
    degauss     =  1.00000e-02
/

"""

HEAD_pdos="""&PROJWFC
	prefix		= "{}",
    outdir      = "{}",
    filpdos     =  '{}_pdos',
    degauss     = 1.00000e-02,
    emax        = 30,
    emin        = -30,
    deltae      = 0.01
/

"""

# DEFAULTVAL is a two-layer dictionary for default values where the top layer corresponds to the names of 
# different control panels, e.g."CONTROL" and "ATOMIC_POSITIONS". The bottom layer corresponds to specific 
# default value for each option in each control panel. To check default value for a specific option, simply 
# use the name of control panel followed by the option name (e.g. use DEFAULTVAL["CONTROL"]["forc_conv_thr"] 
# to see/set force convergence criterion).

# !!!Important note: each ATOMIC_SPECIES entry below should be formulated as 
# 'atom symbol':[atomic mass,pseudopotential name]. In default, the pseudopotential is named as 
# the name of atom + ".upf", e.g. "Na.upf". But you can always update the name of pseudopotential use a 
# customized dictionary, see the "prep_pwipt" function below.

DEFAULTVAL = {
    'CONTROL':{ # general calculation parameters
        'calculation':'scf',
        'forc_conv_thr':0.001,
        'max_seconds':1.72800e+05,
        'pseudo_dir':'/home/sliu135/pseudo/', # !!! change to your ideal path
        # the prep_pwipt will make sure that the path to output folder is always ended up with prefix name
        # i.e., different calculations will have their outputs stored in different folder.
        # the default name for prefix is dependent on your cif filname, but you can always change your prefix name
        # using a customized dictionary.
        'outdir':"/home/sliu135/scratch/",  # !!! change to your ideal path
        'tprnfor':'.TRUE.',
        'tstress':'.TRUE.',
        'prefix':""
        },
    'SYSTEM':{ # detailed info of your atomic system
        'ntyp' : 7,
        'nat' : 20,
        'ibrav' : 14,
        'A' : 7.22,
        'B' : 7.22,
        'C' : 7.22,
        'cosAB' : 0.5,
        'cosAC' : 0.5,
        'cosBC' : 0.5,
        'nspin' : 2,
        'degauss':2.00000e-02,
        'ecutwfc':40.0,
        'ecutrho':360.0,
        'input_dft':"rvv10",
        'lda_plus_u':'.FALSE.',
        'nbnd':256,
        'occupations':"smearing",
        'smearing':"gaussian",
        'U_projection_type':"atomic"
        },
    'ELECTRONS':{ # convergence settings
        'startingpot':"atomic",
        'startingwfc':"atomic+random",
        'mixing_beta':'0.2',
        'conv_thr':1e-08,
        'diagonalization':'cg',
        'diago_thr_init':1e-06,
        'electron_maxstep':300
        },
    'IONS':{ # relaxation settings
        'ion_dynamics':'bfgs'
        },
    'ATOMIC_SPECIES':{}, # a dict with each entry formulated as 'atom symbol':[atom mass, pseudopot name]
    'K_POINTS':{'scheme':'automatic','x':2,'y':2,'z':2,'xs':0,'ys':0,'zs':0}
    }

# qeIpt is a class for reading and adjusting atomic arrangements, and writing input files for pw.x, pp.x, projwfc.x,
# and dos.x. For now qeIpt only reads raw data from cif file, a standard crystalline material data format that has 
# been adopted by many online database, such as material project.

class qeIpt:
    def __init__(self, path, filname,svpath=None,prefix=None):

        self.atoms=read(filename=os.path.join(path, filname))
        self.pw = HEAD
        self.pp = HEAD_rho
        self.dos = HEAD_dos
        self.pdos = HEAD_pdos
        self.defaultval = deepcopy(DEFAULTVAL)
        if not svpath:
            self.svpath = path
        else:
            self.svpath = svpath

        if not prefix:
            self.defaultval['CONTROL']['prefix'] = filname[:-4] # default prefix is just the file name without suffix.
        else:
            self.defaultval['CONTROL']['prefix'] = prefix
    
    def scal_cell(self, scale): # expand or contract simulation box and scale atomic locations
        self.atoms.set_cell(self.atoms.get_cell()*scale)
        self.atoms.set_positions(self.atoms.get_positions() * scale)

    def set_masses(self, typ_val): # change the atom masses, the typ_val is a dict of atom type:mass value
        atyp = self.atoms.get_chemical_symbols()
        mass = self.atoms.get_masses()
        keys = typ_val.keys()
        for i,a in enumerate(atyp):
            if a in keys:
                mass[i] = typ_val[a]
        self.atoms.set_masses(mass)
    
    def check_bravais(self):
        c=self.atoms.get_cell()
        bravais = c.get_bravais_lattice().name
        self.defaultval['SYSTEM']['ibrav']=IBRAV[bravais]

    def update_default(self, custom_dict={}):
        # note that type_val must also be a two-layer dictionary. but no need to include all the control panel.
        nat = len(self.atoms)
        atyp = Counter(self.atoms.get_chemical_symbols())
        mass = Counter(self.atoms.get_masses())
        ntyp = len(atyp.keys())
        cellen = self.atoms.get_cell_lengths_and_angles()
        
        self.defaultval['SYSTEM']['nat']=nat
        self.defaultval['SYSTEM']['A'] = cellen[0]
        self.defaultval['SYSTEM']['B'] = cellen[1]
        self.defaultval['SYSTEM']['C'] = cellen[2]
        self.defaultval['SYSTEM']['cosAB'] = math.cos(cellen[3]/180*math.pi) 
        self.defaultval['SYSTEM']['cosAC'] = math.cos(cellen[4]/180*math.pi) 
        self.defaultval['SYSTEM']['cosBC'] = math.cos(cellen[5]/180*math.pi) 
        
        for t,m in zip(atyp.keys(),mass.keys()):
            self.defaultval['ATOMIC_SPECIES'][t]=[m,t]

        # update defaultval dict from customized dictionary
        for k in custom_dict.keys():
            self.defaultval[k].update(custom_dict[k])
            if 'hubbard_u' in custom_dict[k].keys():
                atyplst=list(atyp.keys())
                self.defaultval[k]['hubbard_u']=[]
                for item in custom_dict[k]['hubbard_u']:
                    self.defaultval[k]['hubbard_u'].append((atyplst.index(item[0])+1,item[1]))
            if 'starting_magnetization' in custom_dict[k].keys():
                atyplst=list(atyp.keys())
                self.defaultval[k]['starting_magnetization']=[]
                for item in custom_dict[k]['starting_magnetization']:
                    self.defaultval[k]['starting_magnetization'].append((atyplst.index(item[0])+1,item[1]))

        # update prefix and outdir
        if self.defaultval['CONTROL']['prefix'] not in self.defaultval['CONTROL']['outdir']:
            self.defaultval['CONTROL']['outdir']=DEFAULTVAL['CONTROL']['outdir']+self.defaultval['CONTROL']['prefix']

    # prepare input file for pw.x
    def prep_pwipt(self):
        fill = []
        for k in ['CONTROL','SYSTEM','ELECTRONS','IONS']:
            temp = ""
            for n,v in self.defaultval[k].items():
                if isinstance(v,(list,tuple)):
                    for item in v:
                        temp+=n+'({})={},\n'.format(item[0],item[1])
                elif isinstance(v, (int, float, complex)):
                    temp+="{}={},\n".format(n,v)
                else:
                    temp+="{}=\"{}\",\n".format(n,v)
            fill.append(temp)

        atom_species=''
        for n,v in self.defaultval['ATOMIC_SPECIES'].items():
            atom_species+='{},{},{}.upf\n'.format(n,v[0],v[1])
        fill.append(atom_species)

        fill+= list(self.defaultval['K_POINTS'].values())

        attyp = self.atoms.get_chemical_symbols()
        atpos = self.atoms.get_positions()
        poslst = ""
        for p,n in zip(atpos,attyp):
            poslst+="{} {} {} {}\n".format(n,p[0],p[1],p[2])
        fill.append(poslst)

        if 'restart_mode' in self.defaultval['CONTROL'].keys():
            fn = open(self.svpath+self.defaultval['CONTROL']['prefix']+'_'+
            self.defaultval['CONTROL']['calculation']+'_restart.in', "w")
        else:
            fn = open(self.svpath+self.defaultval['CONTROL']['prefix']+'_'+
            self.defaultval['CONTROL']['calculation']+'.in', "w")
        fn.write(self.pw.format(*fill))
        fn.close()


    # prepare input file for pp.x
    def prep_ppipt(self):
        prefix = self.defaultval['CONTROL']['prefix']
        self.pp=self.pp.format(prefix,prefix,self.defaultval['CONTROL']['outdir'],prefix, prefix)
        fn = open(self.svpath+self.defaultval['CONTROL']['prefix']+'_pp.in', "w")
        fn.write(self.pp)
        fn.close()

    # prepare input file for dos.x
    def prep_dosipt(self):
        prefix = self.defaultval['CONTROL']['prefix']
        self.dos=self.dos.format(prefix,self.defaultval['CONTROL']['outdir'],prefix)
        fn = open(self.svpath+self.defaultval['CONTROL']['prefix']+'_dos.in', "w")
        fn.write(self.pp)
        fn.close()

    # prepare input file for projwfc.x
    def prep_pdosipt(self):
        prefix = self.defaultval['CONTROL']['prefix']
        self.dos=self.dos.format(prefix,self.defaultval['CONTROL']['outdir'],prefix)
        fn = open(self.svpath+self.defaultval['CONTROL']['prefix']+'_pdos.in', "w")
        fn.write(self.pp)
        fn.close()

