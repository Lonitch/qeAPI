"""
This file contains the functions and classes that can be used to produce standardized input files 
for Quantum Espresso.

Created by Sizhe @06/15/2020
"""

## The installation of ASE package is required to run the functions in this script
from ase.io import write,read
from ase.io import Trajectory
from collections import Counter
import os

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

HEAD_rho="""
&inputpp
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

HEAD_dos ="""
&DOS
	prefix		= "{}",
    outdir      = "{}",
    fildos  =  '{}_dos.dat',
    emax        = 30,
    emin        = -30,
    deltae      = 0.05,
    degauss     =  1.00000e-02
/

"""

HEAD_pdos="""
&PROJWFC
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


DEFAULTVAL = {
    'CONTROL':{ # general calculation parameters
        'calculation':'scf',
        'forc_conv_thr':0.001,
        'max_seconds':1.72800e+05,
        'pseudo_dir':"/home/sliu135/pseudo",
        'outdir':"/home/sliu135/scratch/",
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
        'lda_plus_u':'.TRUE.',
        'nbnd':256,
        'occupations':"smearing",
        'smearing':"gaussian",
        'U_projection_type':"atomic",
        'hubbard_u': [(1,1.0),(2,3.0)],
        'starting_magnetization':[(1,0.5),(2,0.5)]
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
    'K_POINTS':{'scheme':'automatic','x':2,'y':2,'z':2,'xs':0,'ys':0,'zs':0}
    }

# qeIpt is a class for reading and adjusting atomic arrangements, and writing input files for pw.x, pp.x, projwfc.x,
# and dos.x. For now qeIpt only reads raw data from cif file, a standard crystalline material data format that has 
# been adopted by many online database, such as material project.

class qeIpt:
    def __init__(self, path, filname,svpath=None,prefix=None):

        self.atoms=read(filename=os.path.join(path, filname))
        if not svpath:
            self.svpath = path
        else:
            self.svpath = path

        if not prefix:
            self.prefix = filname[:-4] # default prefix is just the file name without suffix.
        else:
            self.prefix = prefix
        self.pw = HEAD.copy()
        self.pp = HEAD_rho.copy()
        self.dos = HEAD_dos.copy()
        self.pdos = HEAD_pdos.copy()
        self.defaultval = DEFAULTVAL.copy()
    
    def scal_cell(self, scale): # expand or contract simulation box and scale atomic locations
        self.atoms.set_cell(self.atoms.get_cell()*scale)
        self.atoms.set_positions(self.atoms.get_positions() * scale)

    def set_masses(self, typ_val): # change the atom masses, the typ_val is a dict of atom type:mass value
        atyp = self.atoms.get_chemical_symbols()
        masses = self.get_masses()
        keys = typ_val.keys()
        for i,a in enumerate(atyp):
            if a in keys:
                masses[i]=typ_val[a]
        self.set_masses(masses)
    
    def update_default(self, custom_dict):
        # note that type_val must also be a two-layer dictionary. but no need to include all the control panel.
        nat = len(self.atoms)
        ntyp = len(''.join([i for i in self.atoms.get_chemical_formula() if not i.isdigit()]))
        cellen = self.atoms.get_cell_lengths_and_angles()
        self.defaultval['CONTROL']['prefix']=self.prefix
        self.defaultval['CONTROL']['outdir']+=self.prefix
        self.defaultval['SYSTEM']['nat']=nat
        self.defaultval['SYSTEM']['A'] = cellen[0]
        self.defaultval['SYSTEM']['B'] = cellen[1]
        self.defaultval['SYSTEM']['C'] = cellen[2]
        self.defaultval['SYSTEM']['cosAB'] = cellen[3]
        self.defaultval['SYSTEM']['cosAC'] = cellen[4]
        self.defaultval['SYSTEM']['cosBC'] = cellen[5]
        for k in custom_dict.keys():
            self.defaultval[k].update(custom_dict[k])

    # prepare input file for pw.x
    def prep_pwipt(self):
        fill = []
        for k in ['CONTROL','SYSTEM','ELECTRONS','IONS']:
            temp = ""
            for n,v in self.defaultval[k]:
                temp+="{}={},\n".format(n,v)
            fill.append(temp)

        fill+= list(self.defaultval['K_POINTS'].values())

        attyp = self.atoms.get_chemical_symbols()
        atpos = self.atoms.get_positions()
        poslst = ""
        for p,n in zip(atpos,attyp):
            poslst+="{} {} {} {}\n".format(n,p[0],p[1],p[2])
        fill.append(poslst)

        self.pw=self.pw.format(*fill)
        fn = open(self.svpath+self.prefix+'.in', "w")
        fn.write(self.pw)
        fn.close()

    # prepare input file for pp.x
    def prep_ppipt(self):
        self.pp=self.pp.format(self.prefix,self.defaultval['CONTROL']['outdir'],self.prefix)
        fn = open(self.svpath+self.prefix+'_pp.in', "w")
        fn.write(self.pp)
        fn.close()

    # prepare input file for dos.x
    def prep_dosipt(self):
        self.dos=self.dos.format(self.prefix,self.prefix,self.defaultval['CONTROL']['outdir'],
        self.prefix,self.prefix)
        fn = open(self.svpath+self.prefix+'_dos.in', "w")
        fn.write(self.pp)
        fn.close()

    # prepare input file for projwfc.x
    def prep_pdosipt(self):
        self.dos=self.dos.format(self.prefix,self.defaultval['CONTROL']['outdir'],self.prefix)
        fn = open(self.svpath+self.prefix+'_pdos.in', "w")
        fn.write(self.pp)
        fn.close()

