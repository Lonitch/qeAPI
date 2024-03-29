"""
This file contains the functions and classes that can be used to produce standardized input files 
for Quantum Espresso from CIF files/ASE atom objects.
Created by Sizhe @06/15/2020

Available Functionalities in qeIpt class:
    (1) set up control options that can be undertood by pw.x
    (2) prepare input files for SCF/nSCF/(vc-)relax calculations 
    (3) prepare input files for band structure/DOS/PDOS calculations
    (4) prepare input files for GW calculations using SternheimerGW code
    (5) prepare input files for charge density/HOCO/LUCO calculation using pp.x

"""

## !!! The installation of ASE package is required to run the functions in this script
import ase
import numpy as np
from ase.io import read
from collections import Counter,defaultdict
from copy import deepcopy
from qe2cif import *
import math
import os,json,sys

# Index of Bravais Lattice
# Current script has a function "check_bravais" to assign correct index of bravais lattice to your system,
# where the global variable IBRAV is used. IBRAV contains all possible shortnames for Bravais lattice,
# more information can be found here: https://en.wikipedia.org/wiki/Brillouin_zone.
# The index of "free" lattice is not included. But you can also use "update_default" function to change your 
# ibrav to 0 (see below).

IBRAV = {'CUB':1,'FCC':2,'BCC':3,'RHL':4,'TET':6,'BCT':7,'ORC':8,'ORCC':9,
         'ORCF':10,'ORCI':11,'MCL':12,'MCLC':13, 'TRI':14}

# HEAD includes all the controling panels that could be set in pw.x input files.
# we can insert options in curly brackets by using default or customized dictionary. Please note that QE will 
# ignore some of the panels listed here depending on the calculation type (e.g, &IONS panel is ignored during 
# SCF calculation).

HEAD = """&CONTROL
{}/

&SYSTEM
{}/

&ELECTRONS
{}/

&IONS
{}/

&CELL
{}/

ATOMIC_SPECIES 
{}
K_POINTS {}
{}

CELL_PARAMETERS angstrom
{}
ATOMIC_POSITIONS angstrom
{}

"""

# The following string stores high-symmetry K points for band structure calculation.

HIGHSYM_KPOINTS = """        300
        0.0000000000    0.0000000000    0.0000000000    1.0
        0.0142857143    0.0000000000    0.0000000000    1.0
        0.0285714286    0.0000000000    0.0000000000    1.0
        0.0428571429    0.0000000000    0.0000000000    1.0
        0.0571428571    0.0000000000    0.0000000000    1.0
        0.0714285714    0.0000000000    0.0000000000    1.0
        0.0857142857    0.0000000000    0.0000000000    1.0
        0.1000000000    0.0000000000    0.0000000000    1.0
        0.1142857143    0.0000000000    0.0000000000    1.0
        0.1285714286    0.0000000000    0.0000000000    1.0
        0.1428571429    0.0000000000    0.0000000000    1.0
        0.1571428571    0.0000000000    0.0000000000    1.0
        0.1714285714    0.0000000000    0.0000000000    1.0
        0.1857142857    0.0000000000    0.0000000000    1.0
        0.2000000000    0.0000000000    0.0000000000    1.0
        0.2142857143    0.0000000000    0.0000000000    1.0
        0.2285714286    0.0000000000    0.0000000000    1.0
        0.2428571429    0.0000000000    0.0000000000    1.0
        0.2571428571    0.0000000000    0.0000000000    1.0
        0.2714285714    0.0000000000    0.0000000000    1.0
        0.2857142857    0.0000000000    0.0000000000    1.0
        0.3000000000    0.0000000000    0.0000000000    1.0
        0.3142857143    0.0000000000    0.0000000000    1.0
        0.3285714286    0.0000000000    0.0000000000    1.0
        0.3428571429    0.0000000000    0.0000000000    1.0
        0.3571428571    0.0000000000    0.0000000000    1.0
        0.3714285714    0.0000000000    0.0000000000    1.0
        0.3857142857    0.0000000000    0.0000000000    1.0
        0.4000000000    0.0000000000    0.0000000000    1.0
        0.4142857143    0.0000000000    0.0000000000    1.0
        0.4285714286    0.0000000000    0.0000000000    1.0
        0.4428571429    0.0000000000    0.0000000000    1.0
        0.4571428571    0.0000000000    0.0000000000    1.0
        0.4714285714    0.0000000000    0.0000000000    1.0
        0.4857142857    0.0000000000    0.0000000000    1.0
        0.5000000000    0.0000000000    0.0000000000    1.0
        0.5083335000   -0.0166665000    0.0000000000    1.0
        0.5166670000   -0.0333330000    0.0000000000    1.0
        0.5250005000   -0.0499995000    0.0000000000    1.0
        0.5333340000   -0.0666660000    0.0000000000    1.0
        0.5416675000   -0.0833325000    0.0000000000    1.0
        0.5500010000   -0.0999990000    0.0000000000    1.0
        0.5583345000   -0.1166655000    0.0000000000    1.0
        0.5666680000   -0.1333320000    0.0000000000    1.0
        0.5750015000   -0.1499985000    0.0000000000    1.0
        0.5833350000   -0.1666650000    0.0000000000    1.0
        0.5916685000   -0.1833315000    0.0000000000    1.0
        0.6000020000   -0.1999980000    0.0000000000    1.0
        0.6083355000   -0.2166645000    0.0000000000    1.0
        0.6166690000   -0.2333310000    0.0000000000    1.0
        0.6250025000   -0.2499975000    0.0000000000    1.0
        0.6333360000   -0.2666640000    0.0000000000    1.0
        0.6416695000   -0.2833305000    0.0000000000    1.0
        0.6500030000   -0.2999970000    0.0000000000    1.0
        0.6583365000   -0.3166635000    0.0000000000    1.0
        0.6666700000   -0.3333300000    0.0000000000    1.0
        0.6583365000   -0.3416635000    0.0000000000    1.0
        0.6500030000   -0.3499970000    0.0000000000    1.0
        0.6416695000   -0.3583305000    0.0000000000    1.0
        0.6333360000   -0.3666640000    0.0000000000    1.0
        0.6250025000   -0.3749975000    0.0000000000    1.0
        0.6166690000   -0.3833310000    0.0000000000    1.0
        0.6083355000   -0.3916645000    0.0000000000    1.0
        0.6000020000   -0.3999980000    0.0000000000    1.0
        0.5916685000   -0.4083315000    0.0000000000    1.0
        0.5833350000   -0.4166650000    0.0000000000    1.0
        0.5750015000   -0.4249985000    0.0000000000    1.0
        0.5666680000   -0.4333320000    0.0000000000    1.0
        0.5583345000   -0.4416655000    0.0000000000    1.0
        0.5500010000   -0.4499990000    0.0000000000    1.0
        0.5416675000   -0.4583325000    0.0000000000    1.0
        0.5333340000   -0.4666660000    0.0000000000    1.0
        0.5250005000   -0.4749995000    0.0000000000    1.0
        0.5166670000   -0.4833330000    0.0000000000    1.0
        0.5083335000   -0.4916665000    0.0000000000    1.0
        0.5000000000   -0.5000000000    0.0000000000    1.0
        0.4916665000   -0.5083335000    0.0000000000    1.0
        0.4833330000   -0.5166670000    0.0000000000    1.0
        0.4749995000   -0.5250005000    0.0000000000    1.0
        0.4666660000   -0.5333340000    0.0000000000    1.0
        0.4583325000   -0.5416675000    0.0000000000    1.0
        0.4499990000   -0.5500010000    0.0000000000    1.0
        0.4416655000   -0.5583345000    0.0000000000    1.0
        0.4333320000   -0.5666680000    0.0000000000    1.0
        0.4249985000   -0.5750015000    0.0000000000    1.0
        0.4166650000   -0.5833350000    0.0000000000    1.0
        0.4083315000   -0.5916685000    0.0000000000    1.0
        0.3999980000   -0.6000020000    0.0000000000    1.0
        0.3916645000   -0.6083355000    0.0000000000    1.0
        0.3833310000   -0.6166690000    0.0000000000    1.0
        0.3749975000   -0.6250025000    0.0000000000    1.0
        0.3666640000   -0.6333360000    0.0000000000    1.0
        0.3583305000   -0.6416695000    0.0000000000    1.0
        0.3499970000   -0.6500030000    0.0000000000    1.0
        0.3416635000   -0.6583365000    0.0000000000    1.0
        0.3333300000   -0.6666700000    0.0000000000    1.0
        0.3249967500   -0.6500032500    0.0000000000    1.0
        0.3166635000   -0.6333365000    0.0000000000    1.0
        0.3083302500   -0.6166697500    0.0000000000    1.0
        0.2999970000   -0.6000030000    0.0000000000    1.0
        0.2916637500   -0.5833362500    0.0000000000    1.0
        0.2833305000   -0.5666695000    0.0000000000    1.0
        0.2749972500   -0.5500027500    0.0000000000    1.0
        0.2666640000   -0.5333360000    0.0000000000    1.0
        0.2583307500   -0.5166692500    0.0000000000    1.0
        0.2499975000   -0.5000025000    0.0000000000    1.0
        0.2416642500   -0.4833357500    0.0000000000    1.0
        0.2333310000   -0.4666690000    0.0000000000    1.0
        0.2249977500   -0.4500022500    0.0000000000    1.0
        0.2166645000   -0.4333355000    0.0000000000    1.0
        0.2083312500   -0.4166687500    0.0000000000    1.0
        0.1999980000   -0.4000020000    0.0000000000    1.0
        0.1916647500   -0.3833352500    0.0000000000    1.0
        0.1833315000   -0.3666685000    0.0000000000    1.0
        0.1749982500   -0.3500017500    0.0000000000    1.0
        0.1666650000   -0.3333350000    0.0000000000    1.0
        0.1583317500   -0.3166682500    0.0000000000    1.0
        0.1499985000   -0.3000015000    0.0000000000    1.0
        0.1416652500   -0.2833347500    0.0000000000    1.0
        0.1333320000   -0.2666680000    0.0000000000    1.0
        0.1249987500   -0.2500012500    0.0000000000    1.0
        0.1166655000   -0.2333345000    0.0000000000    1.0
        0.1083322500   -0.2166677500    0.0000000000    1.0
        0.0999990000   -0.2000010000    0.0000000000    1.0
        0.0916657500   -0.1833342500    0.0000000000    1.0
        0.0833325000   -0.1666675000    0.0000000000    1.0
        0.0749992500   -0.1500007500    0.0000000000    1.0
        0.0666660000   -0.1333340000    0.0000000000    1.0
        0.0583327500   -0.1166672500    0.0000000000    1.0
        0.0499995000   -0.1000005000    0.0000000000    1.0
        0.0416662500   -0.0833337500    0.0000000000    1.0
        0.0333330000   -0.0666670000    0.0000000000    1.0
        0.0249997500   -0.0500002500    0.0000000000    1.0
        0.0166665000   -0.0333335000    0.0000000000    1.0
        0.0083332500   -0.0166667500    0.0000000000    1.0
        0.0000000000    0.0000000000    0.0000000000    1.0
        0.0000000000    0.0000000000    0.0172413793    1.0
        0.0000000000    0.0000000000    0.0344827586    1.0
        0.0000000000    0.0000000000    0.0517241379    1.0
        0.0000000000    0.0000000000    0.0689655172    1.0
        0.0000000000    0.0000000000    0.0862068966    1.0
        0.0000000000    0.0000000000    0.1034482759    1.0
        0.0000000000    0.0000000000    0.1206896552    1.0
        0.0000000000    0.0000000000    0.1379310345    1.0
        0.0000000000    0.0000000000    0.1551724138    1.0
        0.0000000000    0.0000000000    0.1724137931    1.0
        0.0000000000    0.0000000000    0.1896551724    1.0
        0.0000000000    0.0000000000    0.2068965517    1.0
        0.0000000000    0.0000000000    0.2241379310    1.0
        0.0000000000    0.0000000000    0.2413793103    1.0
        0.0000000000    0.0000000000    0.2586206897    1.0
        0.0000000000    0.0000000000    0.2758620690    1.0
        0.0000000000    0.0000000000    0.2931034483    1.0
        0.0000000000    0.0000000000    0.3103448276    1.0
        0.0000000000    0.0000000000    0.3275862069    1.0
        0.0000000000    0.0000000000    0.3448275862    1.0
        0.0000000000    0.0000000000    0.3620689655    1.0
        0.0000000000    0.0000000000    0.3793103448    1.0
        0.0000000000    0.0000000000    0.3965517241    1.0
        0.0000000000    0.0000000000    0.4137931034    1.0
        0.0000000000    0.0000000000    0.4310344828    1.0
        0.0000000000    0.0000000000    0.4482758621    1.0
        0.0000000000    0.0000000000    0.4655172414    1.0
        0.0000000000    0.0000000000    0.4827586207    1.0
        0.0000000000    0.0000000000    0.5000000000    1.0
        0.0142857143    0.0000000000    0.5000000000    1.0
        0.0285714286    0.0000000000    0.5000000000    1.0
        0.0428571429    0.0000000000    0.5000000000    1.0
        0.0571428571    0.0000000000    0.5000000000    1.0
        0.0714285714    0.0000000000    0.5000000000    1.0
        0.0857142857    0.0000000000    0.5000000000    1.0
        0.1000000000    0.0000000000    0.5000000000    1.0
        0.1142857143    0.0000000000    0.5000000000    1.0
        0.1285714286    0.0000000000    0.5000000000    1.0
        0.1428571429    0.0000000000    0.5000000000    1.0
        0.1571428571    0.0000000000    0.5000000000    1.0
        0.1714285714    0.0000000000    0.5000000000    1.0
        0.1857142857    0.0000000000    0.5000000000    1.0
        0.2000000000    0.0000000000    0.5000000000    1.0
        0.2142857143    0.0000000000    0.5000000000    1.0
        0.2285714286    0.0000000000    0.5000000000    1.0
        0.2428571429    0.0000000000    0.5000000000    1.0
        0.2571428571    0.0000000000    0.5000000000    1.0
        0.2714285714    0.0000000000    0.5000000000    1.0
        0.2857142857    0.0000000000    0.5000000000    1.0
        0.3000000000    0.0000000000    0.5000000000    1.0
        0.3142857143    0.0000000000    0.5000000000    1.0
        0.3285714286    0.0000000000    0.5000000000    1.0
        0.3428571429    0.0000000000    0.5000000000    1.0
        0.3571428571    0.0000000000    0.5000000000    1.0
        0.3714285714    0.0000000000    0.5000000000    1.0
        0.3857142857    0.0000000000    0.5000000000    1.0
        0.4000000000    0.0000000000    0.5000000000    1.0
        0.4142857143    0.0000000000    0.5000000000    1.0
        0.4285714286    0.0000000000    0.5000000000    1.0
        0.4428571429    0.0000000000    0.5000000000    1.0
        0.4571428571    0.0000000000    0.5000000000    1.0
        0.4714285714    0.0000000000    0.5000000000    1.0
        0.4857142857    0.0000000000    0.5000000000    1.0
        0.5000000000    0.0000000000    0.5000000000    1.0
        0.5083335000   -0.0166665000    0.5000000000    1.0
        0.5166670000   -0.0333330000    0.5000000000    1.0
        0.5250005000   -0.0499995000    0.5000000000    1.0
        0.5333340000   -0.0666660000    0.5000000000    1.0
        0.5416675000   -0.0833325000    0.5000000000    1.0
        0.5500010000   -0.0999990000    0.5000000000    1.0
        0.5583345000   -0.1166655000    0.5000000000    1.0
        0.5666680000   -0.1333320000    0.5000000000    1.0
        0.5750015000   -0.1499985000    0.5000000000    1.0
        0.5833350000   -0.1666650000    0.5000000000    1.0
        0.5916685000   -0.1833315000    0.5000000000    1.0
        0.6000020000   -0.1999980000    0.5000000000    1.0
        0.6083355000   -0.2166645000    0.5000000000    1.0
        0.6166690000   -0.2333310000    0.5000000000    1.0
        0.6250025000   -0.2499975000    0.5000000000    1.0
        0.6333360000   -0.2666640000    0.5000000000    1.0
        0.6416695000   -0.2833305000    0.5000000000    1.0
        0.6500030000   -0.2999970000    0.5000000000    1.0
        0.6583365000   -0.3166635000    0.5000000000    1.0
        0.6666700000   -0.3333300000    0.5000000000    1.0
        0.6583365000   -0.3416635000    0.5000000000    1.0
        0.6500030000   -0.3499970000    0.5000000000    1.0
        0.6416695000   -0.3583305000    0.5000000000    1.0
        0.6333360000   -0.3666640000    0.5000000000    1.0
        0.6250025000   -0.3749975000    0.5000000000    1.0
        0.6166690000   -0.3833310000    0.5000000000    1.0
        0.6083355000   -0.3916645000    0.5000000000    1.0
        0.6000020000   -0.3999980000    0.5000000000    1.0
        0.5916685000   -0.4083315000    0.5000000000    1.0
        0.5833350000   -0.4166650000    0.5000000000    1.0
        0.5750015000   -0.4249985000    0.5000000000    1.0
        0.5666680000   -0.4333320000    0.5000000000    1.0
        0.5583345000   -0.4416655000    0.5000000000    1.0
        0.5500010000   -0.4499990000    0.5000000000    1.0
        0.5416675000   -0.4583325000    0.5000000000    1.0
        0.5333340000   -0.4666660000    0.5000000000    1.0
        0.5250005000   -0.4749995000    0.5000000000    1.0
        0.5166670000   -0.4833330000    0.5000000000    1.0
        0.5083335000   -0.4916665000    0.5000000000    1.0
        0.5000000000   -0.5000000000    0.5000000000    1.0
        0.4916665000   -0.5083335000    0.5000000000    1.0
        0.4833330000   -0.5166670000    0.5000000000    1.0
        0.4749995000   -0.5250005000    0.5000000000    1.0
        0.4666660000   -0.5333340000    0.5000000000    1.0
        0.4583325000   -0.5416675000    0.5000000000    1.0
        0.4499990000   -0.5500010000    0.5000000000    1.0
        0.4416655000   -0.5583345000    0.5000000000    1.0
        0.4333320000   -0.5666680000    0.5000000000    1.0
        0.4249985000   -0.5750015000    0.5000000000    1.0
        0.4166650000   -0.5833350000    0.5000000000    1.0
        0.4083315000   -0.5916685000    0.5000000000    1.0
        0.3999980000   -0.6000020000    0.5000000000    1.0
        0.3916645000   -0.6083355000    0.5000000000    1.0
        0.3833310000   -0.6166690000    0.5000000000    1.0
        0.3749975000   -0.6250025000    0.5000000000    1.0
        0.3666640000   -0.6333360000    0.5000000000    1.0
        0.3583305000   -0.6416695000    0.5000000000    1.0
        0.3499970000   -0.6500030000    0.5000000000    1.0
        0.3416635000   -0.6583365000    0.5000000000    1.0
        0.3333300000   -0.6666700000    0.5000000000    1.0
        0.3249967500   -0.6500032500    0.5000000000    1.0
        0.3166635000   -0.6333365000    0.5000000000    1.0
        0.3083302500   -0.6166697500    0.5000000000    1.0
        0.2999970000   -0.6000030000    0.5000000000    1.0
        0.2916637500   -0.5833362500    0.5000000000    1.0
        0.2833305000   -0.5666695000    0.5000000000    1.0
        0.2749972500   -0.5500027500    0.5000000000    1.0
        0.2666640000   -0.5333360000    0.5000000000    1.0
        0.2583307500   -0.5166692500    0.5000000000    1.0
        0.2499975000   -0.5000025000    0.5000000000    1.0
        0.2416642500   -0.4833357500    0.5000000000    1.0
        0.2333310000   -0.4666690000    0.5000000000    1.0
        0.2249977500   -0.4500022500    0.5000000000    1.0
        0.2166645000   -0.4333355000    0.5000000000    1.0
        0.2083312500   -0.4166687500    0.5000000000    1.0
        0.1999980000   -0.4000020000    0.5000000000    1.0
        0.1916647500   -0.3833352500    0.5000000000    1.0
        0.1833315000   -0.3666685000    0.5000000000    1.0
        0.1749982500   -0.3500017500    0.5000000000    1.0
        0.1666650000   -0.3333350000    0.5000000000    1.0
        0.1583317500   -0.3166682500    0.5000000000    1.0
        0.1499985000   -0.3000015000    0.5000000000    1.0
        0.1416652500   -0.2833347500    0.5000000000    1.0
        0.1333320000   -0.2666680000    0.5000000000    1.0
        0.1249987500   -0.2500012500    0.5000000000    1.0
        0.1166655000   -0.2333345000    0.5000000000    1.0
        0.1083322500   -0.2166677500    0.5000000000    1.0
        0.0999990000   -0.2000010000    0.5000000000    1.0
        0.0916657500   -0.1833342500    0.5000000000    1.0
        0.0833325000   -0.1666675000    0.5000000000    1.0
        0.0749992500   -0.1500007500    0.5000000000    1.0
        0.0666660000   -0.1333340000    0.5000000000    1.0
        0.0583327500   -0.1166672500    0.5000000000    1.0
        0.0499995000   -0.1000005000    0.5000000000    1.0
        0.0416662500   -0.0833337500    0.5000000000    1.0
        0.0333330000   -0.0666670000    0.5000000000    1.0
        0.0249997500   -0.0500002500    0.5000000000    1.0
        0.0166665000   -0.0333335000    0.5000000000    1.0
        0.0083332500   -0.0166667500    0.5000000000    1.0
        0.0000000000   -0.0000000000    0.5000000000    1.0
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

# qeIpt class will be using the following template to prepare input files for visualizing 
# HOCO/LUCO orbitals.
HEAD_orb="""&inputpp
 prefix = "{}",
 filplot = "{}.orbital",
 plot_num = 7,
 outdir = "{}",
 kpoint = 1, !plot orbital calculated at gamma point
 kband = {},
 ! lsign = .TRUE. ! use this to plot negative+positive part of wfc, usually for molecules
/

&plot
 nfile = 1,
 filepp(1) = "{}.orbital",
 weight(1) = 1.0,
 iflag = 3,
 output_format = 6,
 fileout = '{}.cube'
/
"""

# HEAD_dos/pdos includes an input file template that should be used for the calculations with dos.x/projwfc.x.
# The options of "prefix" and "outdir" should match those in inputs for pw.x
# It is not required for DOS and PDOS calculations to have the same emax, emin, and deltae, but we always use 
# identical values to make final results consistent.

HEAD_dos ="""&DOS
    prefix='{}',
    outdir='{}',
    fildos='{}.dos.dat',
    emin=-35,
    emax=35,
    deltae=0.01
/

"""

HEAD_pdos="""&PROJWFC
    prefix='{}',
    outdir='{}',
    fildos='{}_pdos',
    degauss=1.00000e-02,
    emax=30,
    emin=-30,
    deltae=0.01
/

"""

# HEAD_band includes a template that should be used with band.x. Like the DOS calculation, 
# the "prefix" and "outdir" should match those in corresponding input files for pw.x
# You can find functions for post-processing band data file in "qeplot.py"

HEAD_band="""&BANDS
    prefix      = "{}",
    outdir      = "{}",
    filband     = "{}_bandsx.dat"
    lsym        = .TRUE.
/

"""

# Below are input templates for phonon calculation using "ph.x". A workflow for phonon
# calculation is (SCF with dense k-point scheme)->(calculate dynamic matrix using ph.x)->
# ->(calculate force constants using q2r.x)->(calculate phonon frequency at a given list of q-vectors)

HEAD_ph="""&inputph
    outdir = '{}'
    prefix = '{}',
    tr2_ph = 1.0d-14
    ldisp = .true.
    {}nq1 = {}, nq2 = {}, nq3 = {}
    fildyn = '{}.dyn'
/

"""

HEAD_q2r = """&input
    fildyn = '{}.dyn'
    zasr = 'simple'
    flfrc = '{}.k{}.fc'
/

"""

HEAD_disp = """&input
    asr = 'simple'
    {}flfrc = '{}.k{}.fc'
    flfrq = '{}.freq'
    q_in_band_form = .true. !integers in the list below show numbers of sampled points btw two K-points
    q_in_cryst_coord = .true. !K points in crystal unit
/
15 !Calculated by SeeK-path (https://www.materialscloud.org/work/tools/seekpath)
  0.0000000000 0.0000000000 0.0000000000 20 !Γ 
  0.5000000000 0.5000000000 0.5000000000 30 !R
  -0.5000000000 -0.5000000000 -0.5000000000 30 !R'
  0.0000000000 0.5000000000 0.5000000000 20 !T	
  -0.0000000000 -0.5000000000 -0.5000000000 30 !T'
  0.5000000000 0.0000000000 0.5000000000 20 !U
  -0.5000000000 -0.0000000000 -0.5000000000 30 !U'
  0.5000000000 0.5000000000 0.0000000000 20 !V
  -0.5000000000 -0.5000000000 -0.0000000000 20 !V'
  0.5000000000 0.0000000000 0.0000000000 10 !X
  -0.5000000000 -0.0000000000 -0.0000000000 10 !X'
  0.0000000000 0.5000000000 0.0000000000 10 !Y
  -0.0000000000 -0.5000000000 -0.0000000000 10 !Y'
  0.0000000000 0.0000000000 0.5000000000 10 !Z
  -0.0000000000 -0.0000000000 -0.5000000000 5 !Z'

"""

HEAD_phdos ="""&input
    asr = 'simple'
    dos = .true.
    {}
    flfrc = '{}.k{}.fc'
    fldos = '{}.phdos'
    nk1=50, nk2=50, nk3=50
/

"""

HEAD_gw="""&gw_input
  title = 'GW band structure for {}.'

  ! config of the scf run
  prefix         = '{}'
  outdir         = '{}'

  ! the grid used for the linear response
  kpt_grid       = 4, 4, 4
  qpt_grid       = 4, 4, 4

  ! number of bands for which the GW correction is calculated
  num_band       = 8

  ! configuration of W in the convolution
  max_freq_coul  = 200
  num_freq_coul  = 51

  ! configuration for the correlation self energy
  ecut_corr      = 6.0

  ! configuration for the exchange self energy
  ecut_exch      = 15.0
/

&gw_output
  directory = '{}'
  file_gw   = '{}gw_band.dat'
/

FREQUENCIES
35
  0.0    0.0
  0.0    0.3
  0.0    0.9
  0.0    1.8
  0.0    3.0
  0.0    4.5
  0.0    6.3
  0.0    8.4
  0.0   10.8
  0.0   13.5
  0.0   16.5
  0.0   19.8
  0.0   23.4
  0.0   27.3
  0.0   31.5
  0.0   36.0
  0.0   40.8
  0.0   45.9
  0.0   51.3
  0.0   57.0
  0.0   63.0
  0.0   69.3
  0.0   75.9
  0.0   82.8
  0.0   90.0
  0.0   97.5
  0.0  105.3
  0.0  113.4
  0.0  121.8
  0.0  130.5
  0.0  139.5
  0.0  148.8
  0.0  158.4
  0.0  168.3
  0.0  178.5
/

K_points
{}
{}
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
        # 'A' : 7.22,
        # 'B' : 7.22,
        # 'C' : 7.22,
        # 'cosAB' : 0.5,
        # 'cosAC' : 0.5,
        # 'cosBC' : 0.5,
        'nspin' : 2,
        'degauss':1.00000e-02,
        'ecutwfc':40.0,
        'ecutrho':360.0,
        'input_dft':"rvv10",
        'lda_plus_u':'.FALSE.',
        'occupations':"smearing",
        'smearing':"cold",
        },
    'ELECTRONS':{ # convergence settings
        'mixing_beta':0.2,
        'conv_thr':1e-08,
        'diagonalization':'david',
        'electron_maxstep':300
        },
    'IONS':{ # relaxation settings
        'ion_dynamics':'bfgs'
        },
    'ATOMIC_SPECIES':{}, # a dict with each entry formulated as 'atom symbol':[atom mass, pseudopot name]
    'CELL PARAMETERS':None,
    'K_POINTS':{'scheme':'automatic','x':2,'y':2,'z':2,'xs':0,'ys':0,'zs':0},
    'CELL':{'cell_dynamics':'bfgs','cell_dofree':'all'}
    }

# qeIpt is a class for reading and adjusting atomic arrangements, and writing input files for pw.x, pp.x, projwfc.x,
# and dos.x. For now qeIpt only reads raw data from cif file, a standard crystalline material data format that has 
# been adopted by many online database, such as material project.

class qeIpt:
    def __init__(self, path=None, filname=None,svpath=None,prefix=None, outdir=None,atoms=None):
        # path: where your cif file is.
        # filname: file name of your cif file.
        # atoms: an ASE atoms object
        # svpath: path to where you want your QE input files stored,same as 'path' if not given.
        # prefix: the prefix for your calculation job, same as 'filname' if not given.
        # outdir: a path to the directory where the output data repository is stored.  
        if atoms:
            self.atoms = atoms
        else:
            if path and filname:
                self.atoms=read(filename=os.path.join(path, filname))
            else:
                print('Please tell me the file path and file name!!!')
        self.atsymb = self.atoms.get_chemical_symbols()
        self.atpos = self.atoms.get_positions()
        self.pw = HEAD
        self.pp = HEAD_rho
        self.dos = HEAD_dos
        self.pdos = HEAD_pdos
        self.band = HEAD_band
        self.ph = HEAD_ph
        self.phdos = HEAD_phdos
        self.q2r = HEAD_q2r
        self.disp = HEAD_disp
        self.defaultval = deepcopy(DEFAULTVAL)
        if not svpath:
            self.svpath = path
        else:
            self.svpath = svpath

        
        if prefix:
            self.defaultval['CONTROL']['prefix'] = prefix
        # elif atoms:
        #     self.defaultval['CONTROL']['prefix'] = atoms.get_chemical_formula()
        elif filname:
            temp = os.path.split(filname)[-1][:-4]
            self.defaultval['CONTROL']['prefix'] = temp
        else:
            print('You need to set defaultval["CONTROL"]["prefix"], NOW!!!')

        if outdir:
            self.defaultval['CONTROL']['outdir']=outdir
        
        ## Print prefix and outdir info
        # print("!!!Initiation info\n prefix:{}\n outdir:{}".format(self.defaultval['CONTROL']['prefix'], self.defaultval['CONTROL']['outdir']))
    
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
    
    # build a supercell based on self.atoms
    def build_supercell(self, s=3, wrap=False):
        if isinstance(s,int):
            mtx = np.array([[s, 0, 0], [0, s, 0], [0, 0, s]])
        elif isinstance(s,list) or isinstance(s,np.ndarray):
            mtx = np.array([[s[0], 0, 0], [0, s[1], 0], [0, 0, s[2]]])
        else:
            raise Exception('wrong type')
        self.atoms=ase.build.make_supercell(self.atoms, mtx,wrap=wrap)

    def check_bravais(self):
        c=self.atoms.get_cell()
        bravais = c.get_bravais_lattice().name
        self.defaultval['SYSTEM']['ibrav']=IBRAV[bravais]

    def set_pseudo_names(self,pseudotag):
        """Description: change names of pseudopot
        ---Params---
        pseudotag could be one of the following three things:
        1. a list of 2-tuples of (symbol,name),
        2. a string of 'precision', which add "_SSSP_precision" in pseudopot names, 
        3. or 'efficiency'which add "_SSSP_efficiency" in pseudopot names.
        """
        if isinstance(pseudotag,list):
            for item in pseudotag:
                self.defaultval['ATOMIC_SPECIES'][item[0]]=[np.round(read_atomInfo(item[0])['atomic_mass'],8),item[1]]
        elif pseudotag=='precision':
            ct = Counter(self.atsymb)
            for k in ct.keys():
                self.defaultval['ATOMIC_SPECIES'][k]=[np.round(read_atomInfo(k)['atomic_mass'],8),
                k+'_SSSP_precision.upf']
        elif pseudotag=='efficiency':
            ct = Counter(self.atsymb)
            for k in ct.keys():
                self.defaultval['ATOMIC_SPECIES'][k]=[np.round(read_atomInfo(k)['atomic_mass'],8),
                k+'_SSSP_efficiency.upf']

    def nbnd_from_pseudo(self,jsonfile,bndscale=1.2):
        """
        Description: calculate band number using valence values in pseudopot files.
            The function also update cutoff energy and rho by using the largest 
            recommended values among all the elements in the system.
        ---Params---
        jsonfile: 
            currently, it could be 'sssp_precision.json' or 'sssp_efficiency.json'
        bndscale:
            nbnd = int((total electron number)/2*bndscale)
        ------------
        """
        i,path =0, ''
        while 'qeAPI' not in path: # find the root path for qeAPI
            path = sys.path[i]
            i+=1
        atyp = Counter(self.atoms.get_chemical_symbols())
        with open(os.path.join(path,jsonfile)) as json_file:
            table=json.load(json_file)
        json_file.close()
        opt_cutoff = [0,0]
        nbnd = 0
        for k in atyp.keys():
            nbnd+=read_atomInfo(k)['number']*atyp[k]
            if table[k]['cutoff']>opt_cutoff[0]:
                    opt_cutoff[0]=table[k]['cutoff']
            if table[k]['rho_cutoff']>opt_cutoff[1]:
                opt_cutoff[1]=table[k]['rho_cutoff']
                
        self.defaultval['SYSTEM']['nbnd']=int(nbnd/2*bndscale)
        self.defaultval['SYSTEM']['ecutwfc']=int(opt_cutoff[0])
        self.defaultval['SYSTEM']['ecutrho']=int(opt_cutoff[1])

    def update_default(self, custom_dict={}):
        # note that type_val must also be a two-layer dictionary. but no need to include all the control panel.
        nat = len(self.atoms)
        atyp = Counter(self.atoms.get_chemical_symbols())
        mass = Counter(self.atoms.get_masses())
        ntyp = len(atyp.keys())
        # cellen = self.atoms.get_cell_lengths_and_angles()
        self.atsymb = self.atoms.get_chemical_symbols()
        self.atpos = self.atoms.get_positions()
        # self.atpos = np.round(self.atpos,8)
        indices = defaultdict(list)
        for i,v in enumerate(self.atsymb):
            indices[v].append(i)

        # calculate number of bands (electronNum/2*1.2)
        # nbnd = 0
        # for k in atyp.keys():
        #     nbnd+=read_atomInfo(k)['number']*atyp[k]
        # nbnd = int(nbnd/2+16)
        
        self.defaultval['SYSTEM']['nat']=nat
        self.defaultval['SYSTEM']['ntyp']=ntyp
        self.defaultval['CELL_PARAMETERS'] = np.array(self.atoms.get_cell())
        # self.defaultval['SYSTEM']['A'] = np.round(cellen[0],8)
        # self.defaultval['SYSTEM']['B'] = np.round(cellen[1],8)
        # self.defaultval['SYSTEM']['C'] = np.round(cellen[2],8)
        # self.defaultval['SYSTEM']['cosAB'] = np.round(math.cos(cellen[3]/180*math.pi),8)
        # self.defaultval['SYSTEM']['cosAC'] = np.round(math.cos(cellen[4]/180*math.pi),8)
        # self.defaultval['SYSTEM']['cosBC'] = np.round(math.cos(cellen[5]/180*math.pi),8)
        # self.defaultval['SYSTEM']['nbnd'] = nbnd
        if not self.defaultval['ATOMIC_SPECIES']:
            for t,m in zip(atyp.keys(),mass.keys()):
                self.defaultval['ATOMIC_SPECIES'][t]=[np.round(m,8),t+'.upf']

        # update defaultval dict from customized dictionary
        for k in custom_dict.keys():
            if k=='SYSTEM':
                for tk in custom_dict[k].keys():
                    if tk in ['hubbard_u','hubbard_alpha','starting_magnetization','starting_charge']:
                        atyplst=list(atyp.keys())
                        if tk not in self.defaultval[k].keys():
                            self.defaultval[k][tk] = []
                            tempdict = defaultdict()
                        else:
                            tempdict = dict(self.defaultval[k][tk])
                        for item in custom_dict[k][tk]:
                            tempdict[atyplst.index(item[0])+1]=item[1]
                        self.defaultval[k][tk]=list(tempdict.items())
                    else:
                        self.defaultval[k][tk]=custom_dict[k][tk]
            else:
                self.defaultval[k].update(custom_dict[k])
        # update prefix and outdir
        if self.defaultval['CONTROL']['prefix'] not in self.defaultval['CONTROL']['outdir']:
            self.defaultval['CONTROL']['outdir']=os.path.join(self.defaultval['CONTROL']['outdir'],
            self.defaultval['CONTROL']['prefix'])

    def delete_entry(self,entries):
        # This function is used to delete entries in self.defaultval.
        # the argument "entries" is a list of tuple with first and second element being panel name 
        # and option name respectively. For example, the commend below delete the 'input_dft' option 
        # in 'SYSTEM' panel
        #
        # obj.delete_entry([('SYSTEM','input_dft')])
        # 

        for a,b in entries:
            self.defaultval[a].pop(b,None)
        return

    # prepare input file for pw.x
    def prep_pwipt(self):
        fill = []
        for k in ['CONTROL','SYSTEM','ELECTRONS','IONS','CELL']:
            temp = ""
            for n,v in self.defaultval[k].items():
                if isinstance(v,(list,tuple)):
                    for item in v:
                        temp+=n+'({})={},\n'.format(item[0],item[1])
                elif isinstance(v, (int, float, complex)) or (isinstance(v,str) and v.isnumeric()):
                    temp+="{}={},\n".format(n,v)
                elif v in ['.TRUE.','.FALSE.']:
                    temp+="{}={},\n".format(n,v)
                else:
                    temp+="{}=\"{}\",\n".format(n,v)
            fill.append(temp)

        atom_species=''
        for n,v in self.defaultval['ATOMIC_SPECIES'].items():
            atom_species+=' {} {} {}\n'.format(n,v[0],v[1])
        fill.append(atom_species)

        if self.defaultval['CONTROL']['calculation']=='bands':
            fill+= ['crystal',HIGHSYM_KPOINTS]

        # nscf calc is precursory calculation for dos/pdos and perturbative calc.
        # The K-point scheme is supposed to be much denser than those for relax calc. The code below 
        elif self.defaultval['CONTROL']['calculation']=='nscf':
            cellen = self.atoms.cell.cellpar()[0]
            kn = math.ceil(cellen/0.8)
            self.defaultval['K_POINTS']['x']=kn
            self.defaultval['K_POINTS']['y']=kn
            self.defaultval['K_POINTS']['z']=kn
            print('conduct nscf on a K-point scheme of {}*{}*{}'.format(kn,kn,kn))
            kpvals = list(self.defaultval['K_POINTS'].values())
            fill+=[kpvals[0],' '.join([str(item) for item in kpvals[1:]])]

        else:
            kpvals = list(self.defaultval['K_POINTS'].values())
            if kpvals[0] in ['Gamma','gamma','GAMMA']:
                fill+=[kpvals[0],' ']
            else:
                fill+=[kpvals[0],' '.join([str(item) for item in kpvals[1:]])]

        cellst = ""
        for _x in range(3):
            temp=self.defaultval['CELL_PARAMETERS'][_x]
            cellst+="{} {} {}\n".format(temp[0],temp[1],temp[2])
        fill.append(cellst)

        poslst = ""
        for p,n in zip(self.atpos,self.atsymb):
            poslst+="  {} {} {} {}\n".format(n,p[0],p[1],p[2])
        fill.append(poslst)

        if 'restart_mode' in self.defaultval['CONTROL'].keys() and self.defaultval['CONTROL']['restart_mode']=='restart':
            temp = self.defaultval['CONTROL']['prefix']+'_'+self.defaultval['CONTROL']['calculation']+'_restart.in'
            fn = open(os.path.join(self.svpath,temp), "w")
        else:
            temp = self.defaultval['CONTROL']['prefix']+'_'+self.defaultval['CONTROL']['calculation']+'.in'
            fn = open(os.path.join(self.svpath,temp), "w")
        fn.write(self.pw.format(*fill))
        fn.close()

        # input file for bands calc. will be named as "prefix_bands.in" while input for bands.x will 
        # be "prefix_band.in"
        if self.defaultval['CONTROL']['calculation']=='bands':
            temp = self.defaultval['CONTROL']['prefix']+'_'+'band'+'.in'
            fn = open(os.path.join(self.svpath,temp), "w")
            prefix = self.defaultval['CONTROL']['prefix']
            outdir = self.defaultval['CONTROL']['outdir']
            self.band = self.band.format(prefix,outdir,prefix)
            fn.write(self.band)
            fn.close()

        print("!!!Initial info\n pseudodir:{}\n outdir:{}".format(self.defaultval['CONTROL']['pseudo_dir'], 
        self.defaultval['CONTROL']['outdir']))


    # prepare input file for pp.x, the "usrdir" is a path to the source data file,
    # define "usrdir" when you moved your data file to a location different than the default path.
    def prep_ppipt(self, usrdir=None, tag='charge',pseudoval=None):
        # `tag` specifies the type of calculation, for now, only 'charge' and 'HOCO'/'LUCO' are implemented.
        # 'charge' calculates charge distribution
        # 'HOCO' calculates highest occupied crystal orbital
        # 'LUCO' calculates lowest occupied crystal orbital
        prefix = self.defaultval['CONTROL']['prefix']

        if usrdir:
            outdir = usrdir
        else:
            outdir=self.defaultval['CONTROL']['outdir']

        if tag=='charge':
            self.pp=self.pp.format(prefix,prefix,outdir,prefix, prefix)
            fn = open(os.path.join(self.svpath,self.defaultval['CONTROL']['prefix']+'_pp.in'), "w")
            fn.write(self.pp)
            fn.close()
        else:
            if pseudoval is None:
                print('please tell me electron numbers of each atomic type, according to your pseudopotential file!')
                return
            nbnd = 0
            atyp = Counter(self.atoms.get_chemical_symbols())
            for k in pseudoval.keys():
                nbnd+=pseudoval[k]*atyp[k]
            nbnd = int(nbnd/2) # !!! assuming no degeneracy
            if tag in ['HOCO','hoco']:
                self.pp = HEAD_orb.format(prefix,prefix+'_hoco',outdir,nbnd,prefix+'_hoco',prefix+'_hoco')
                fn = open(os.path.join(self.svpath,self.defaultval['CONTROL']['prefix']+'_hoco_pp.in'), "w")
                fn.write(self.pp)
                fn.close()
            elif tag in ['LUCO','luco']:
                self.pp = HEAD_orb.format(prefix,prefix+'_luco',outdir,nbnd+1,prefix+'_luco',prefix+'_luco')
                fn = open(os.path.join(self.svpath,self.defaultval['CONTROL']['prefix']+'_luco_pp.in'), "w")
                fn.write(self.pp)
                fn.close()

    # prepare input file for dos.x
    # define "usrdir" when you moved your data file to a location different than the default path.
    def prep_dosipt(self,usrdir=None):
        prefix = self.defaultval['CONTROL']['prefix']
        if usrdir:
            outdir = usrdir
        else:
            outdir=self.defaultval['CONTROL']['outdir']

        self.dos=self.dos.format(prefix,outdir,prefix)
        fn = open(os.path.join(self.svpath,self.defaultval['CONTROL']['prefix']+'_dos.in'), "w")
        fn.write(self.dos)
        fn.close()

    # prepare input file for projwfc.x
    # define "usrdir" when you moved your data file to a location different than the default path.
    def prep_pdosipt(self,usrdir=None):
        prefix = self.defaultval['CONTROL']['prefix']
        if usrdir:
            outdir = usrdir
        else:
            outdir=self.defaultval['CONTROL']['outdir']

        self.pdos=self.pdos.format(prefix,outdir,prefix)
        fn = open(os.path.join(self.svpath,self.defaultval['CONTROL']['prefix']+'_pdos.in'), "w")
        fn.write(self.pdos)
        fn.close()

    # prepare input file for bands.x
    def prep_bandipt(self,usrdir=None):
        prefix = self.defaultval['CONTROL']['prefix']
        if usrdir:
            outdir = usrdir
        else:
            outdir=self.defaultval['CONTROL']['outdir']

        self.band=self.band.format(prefix,outdir,prefix)
        fn = open(os.path.join(self.svpath,self.defaultval['CONTROL']['prefix']+'_band.in'), "w")
        fn.write(self.band)
        fn.close()

    def prep_phipt(self,usrdir=None):
        print('Input for SCF calc with dense K point scheme is also prepared!')
        self.defaultval['CONTROL']['calculation']='scf'
        a = self.atoms.cell.cellpar()[0]
        kn = math.floor(a/0.8)
        self.defaultval['K_POINTS']['x']=kn
        self.defaultval['K_POINTS']['y']=kn
        self.defaultval['K_POINTS']['z']=kn
        print('conduct nscf on a K-point scheme of {}*{}*{}'.format(kn,kn,kn))
        if usrdir is not None:
            self.defaultval['CONTROL']['outdir']=usrdir
        print('outdir:{}'.format(self.defaultval['CONTROL']['outdir']))
        self.prep_pwipt()
        masses = ""
        for i,v in enumerate(self.defaultval['ATOMIC_SPECIES'].items()):
            masses+="amass({})={},\n".format(i+1,v[-1][0])

        qn = int(kn/3*2)
        prefix = self.defaultval['CONTROL']['prefix']
        outdir = self.defaultval['CONTROL']['outdir']

        temp = self.defaultval['CONTROL']['prefix']+'_'+'ph'+'.in'
        fn = open(os.path.join(self.svpath,temp), "w")
        self.ph = self.ph.format(outdir,prefix,masses,qn,qn,qn,prefix)
        fn.write(self.ph)
        fn.close()

        temp = self.defaultval['CONTROL']['prefix']+'_'+'q2r'+'.in'
        fn = open(os.path.join(self.svpath,temp), "w")
        self.q2r = self.q2r.format(prefix,prefix,qn)
        fn.write(self.q2r)
        fn.close()

        temp = self.defaultval['CONTROL']['prefix']+'_'+'disp'+'.in'
        fn = open(os.path.join(self.svpath,temp), "w")
        self.disp = self.disp.format(masses,prefix,qn,prefix)
        fn.write(self.disp)
        fn.close()

        temp = self.defaultval['CONTROL']['prefix']+'_'+'phdos'+'.in'
        fn = open(os.path.join(self.svpath,temp), "w")
        self.phdos = self.ph.format(masses,prefix,qn,prefix)
        fn.write(self.phdos)
        fn.close()

    # prepare input file for Sternheimer GW band calculation using gw.x in qe-6.3
    def prep_gwipt(self,kpoints,directory='/home/sliu135/bands'):
        prefix = self.defaultval['CONTROL']['prefix']
        outdir=self.defaultval['CONTROL']['outdir']

        temp=HEAD_gw.format(prefix,prefix,outdir,directory,prefix,len(kpoints.split('\n')),kpoints)
        fn = open(os.path.join(self.svpath,self.defaultval['CONTROL']['prefix']+'_gw.in'), "w")
        fn.write(temp)
        fn.close()
        temp = self.defaultval['CONTROL']['prefix']+'_'+'band'+'.in'
        fn = open(os.path.join(self.svpath,temp), "w")
        prefix = self.defaultval['CONTROL']['prefix']
        outdir = self.defaultval['CONTROL']['outdir']
        self.band = self.band.format(prefix,outdir,prefix)
        fn.write(self.band)
        fn.close()