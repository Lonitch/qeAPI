"""
This file contains the functions for visualizing output data from DFT calculations.

Created by Sizhe @12/25/2020
"""

from re import sub
import ase
from ase.io import write,read
from qe2cif import *
import math,os,glob
import pandas as pd
import numpy as np

#This function extracts the high symmetry points from the output of bandx.out
# Adopted from Levi Lentz at MIT, changed into a form compatible with qeAPI functionalities
def Symmetries(fstring): 
    f = open(fstring,'r')
    x = np.zeros(0)
    for i in f:
        if "high-symmetry" in i:
            x = np.append(x,float(i.split()[-1]))
    f.close()
    return x
# This function takes in the datafile, the fermi energy, the symmetry file, a subplot, and the label
# It then extracts the band data, and plots the bands, the fermi energy in red, and the high symmetry points
def bndplot(bdpath,scfpath,subplot,label=None,yrange=20):
    datafiles = glob.glob(os.path.join(bdpath,'*dat.gnu'))
    symmfiles = glob.glob(os.path.join(bdpath,'*band.out'))
    scffiles = glob.glob(os.path.join(scfpath,'*.out'))

    # find data.gnu file
    if len(datafiles)>1:
        print('tell me which file you want using:')
        for i,f in enumerate(datafiles):
            print("{}. {}\n".format(i,f))
        idx = int(input('Type it here:'))
        datafile = datafiles[idx]
    elif not datafiles:
        print('There is no gnu data file!!!')
        return -1
    else:
        datafile = datafiles[0]

    # Find band.out file
    if len(symmfiles)>1:
        print('tell me which symmetry file you want using:')
        for i,f in enumerate(symmfiles):
            print("{}. {}\n".format(i,f))
        idx = int(input('Type it here:'))
        symmetryfile = symmfiles[idx]
    elif not symmfiles:
        print('There is no band data file!!!')
        return -1
    else:
        symmetryfile = symmfiles[0]

    # find scf/relax output file
    if len(scffiles)>1:
        print('tell me which file you want using:')
        for i,f in enumerate(scffiles):
            print("{}. {}\n".format(i,f))
        idx = int(input('Type it here:'))
        scffile = scffiles[idx]
    elif not scffiles:
        print('There is no scf output file!!!')
        return -1
    else:
        scffile = scffiles[0]

    # Plot title string
    if label is None:
        label=os.path.split(scffile)[1][:-4]

    #This loads the bandx.dat.gnu file
    z = pd.read_csv(datafile, delimiter= '\s+', header=None)
    z = z.to_numpy() 
    # Find Fermi energy
    atms = read_espresso_out(scffile,index=-1)
    calc = atms.get_calculator()
    Fermi = float(calc.get_fermi_level())
    x = np.unique(z[:,0]) #This is all the unique x-points
    bands = []
    bndl = len(z[z[:,0]==x[1]]) #This gives the number of bands in the calculation
    axis = [min(x),max(x),Fermi - 4, Fermi + 4]
    for i in range(0,bndl):
        bands.append(np.zeros([len(x),2])) #This is where we store the bands
    for i in range(0,len(x)):
        sel = z[z[:,0] == x[i]]  #Here is the energies for a given x
        for j in range(0,bndl): #This separates it out into a single band
            bands[j][i][0] = x[i]
            bands[j][i][1] = np.multiply(sel[j][1],13.605698066)
    for i in bands: #Here we plots the bands
        subplot.plot(i[:,0],i[:,1],color="black")
    temp = Symmetries(symmetryfile)
    for j in temp: #This is the high symmetry lines
        x1 = [j,j]
        x2 = [-yrange,yrange]
        subplot.plot(x1,x2,'--',lw=0.5,color='black',alpha=0.8)
    subplot.plot([min(x),max(x)],[Fermi,Fermi],color='red',)
    subplot.set_xticks(temp)
    subplot.set_xticklabels(['$\Gamma$' if a==0 else " " for a in temp])
    # subplot.set_ylim([axis[2],axis[3]])
    subplot.set_ylim([-yrange,yrange])
    subplot.set_xlim([axis[0],axis[1]])
    subplot.set_title(label)
    subplot.set_ylabel('Energy(eV)')
