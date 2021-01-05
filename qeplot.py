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
import matplotlib.pyplot as plt

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

# This function extracts the band data, and plots the bands, the fermi energy in red
def bndplot(datafile=None,scffile=None,symmetryfile=None,bdpath=None,scfpath=None,
            subplot=None,label=None,yrange=10,lw=1,unit='Ry',insanity=False):
    """
    Params:
        datafile: path+filename for band data file (dat.gnu)
        scffile: path +filename for the result of scf/nscf calc
        symmfile: path +filename for output file of bands.x calc
        ! using the following args if none of above is provided !
        bdpath: path to the results of bands calc, where you store `xx.dat.gnu` and `xx_band.out`,
                for definitions of these two files, please check the comments in `raw2qe.py`.
        scfpath: path to the result of scf calc, we need this to extract fermi energy level info.
        subplot: an axis object for plotting band structure
        label: a title string for the plot
        yrange: set limit of y axis to [-yrange, yrange] in the unit of eV.
        unit: if unit is set to be 'Ry', the code will convert energy values to 'eV'
        insanity: indicator of abnormal values in bands results, if true, will start a sanity check
    """
    # If the file name is directly given, we skip the file search
    if datafile is None or scffile is None or symmetryfile is None:
        datafiles = glob.glob(os.path.join(bdpath,'*dat.gnu'))
        symmfiles = glob.glob(os.path.join(bdpath,'*band.out'))
        scffiles = glob.glob(os.path.join(scfpath,'*.out'))
        #File search
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

    # Plot title string, could be reset outside of the function
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
            if unit=='Ry':
                bands[j][i][1] = np.multiply(sel[j][1],13.605698066)
            else:
                bands[j][i][1] = sel[j][1]
    if insanity:
        from scipy import interpolate
        newbands=[]
        for i,band in enumerate(bands):
            std=np.std(band[:,1])
            avg = np.mean(band[:,1])
            idx = [avg-2*std<_a<avg+2*std for _a in band[:,1]]
            if sum(idx)>5:
                band = band[idx]
            tck = interpolate.splrep(band[:,0], band[:,1], s=0)
            xnew = np.linspace(np.min(band[:,0])-0.5, np.max(band[:,0])+0.5, 1000)
            ynew = interpolate.splev(xnew, tck)
            temp = np.zeros((1000,2))
            temp[:,0] = xnew
            temp[:,1] = ynew
            newbands.append(temp)
        for i in newbands: #Here we plots the bands
            subplot.plot(i[:,0],i[:,1],color="black",lw=lw)
    else:
        for i in bands: #Here we plots the bands
            subplot.plot(i[:,0],i[:,1],color="black",lw=lw)

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
    return bands

# The following two functions plot dos and pdos results
def dosplot(ax,dospath=None,datafile=None,tag='_dos',fermi=None,xrange=15,lw=2):
    """
    Params:
        dospath: a path to the folder that stores `xxx_dos.dat` file
        datafile: path+filename to data file, if it is used, function will ignore `dospath`
        ax: axis object for plotting dos distribution
        tag: a substring in the file name, if multiple files with the same
             tag are find, the function will ask for clarification.
        label: title text for the plot
        xrange: set limits of x axis to be [-xrange,xrange]
    """
    if datafile is None:
        datafiles = glob.glob(os.path.join(dospath,'*{}.dat'.format(tag)))
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
    if fermi is None:
        with open(datafile,'r') as f:
            fermi = f.readlines()[0]
        fermi = float(fermi.split()[-2])
        f.close()
    dos_data = pd.read_csv(datafile, delimiter='\s+',header=None, skiprows = [0])
    dos_data = dos_data.to_numpy()
    # substract fermi energy level from the results
    elevl = dos_data[:,0]-fermi
    # spinless calculation results
    if len(dos_data[0])<=3:
        ax.plot(elevl,dos_data[:,1],'r-',linewidth=lw)
    # spin polarized results
    else:
        # red color for spin-up DOS
        ax.plot(elevl,dos_data[:,1],'r-',linewidth=lw,label='spin up')
        # blue color for spin-down DOS
        ax.plot(elevl,-dos_data[:,2],'b-',linewidth=lw,label='spin down')

    # add a vertial line at fermi energy level
    ymin,ymax=ax.get_ylim()
    ax.plot([0,0],[ymin,ymax],'k--',linewidth=lw)
    ax.set_ylim([ymin,ymax])
    # add a thin horizontal line at DOS=0
    ax.plot([-xrange,xrange],[0,0],'k-',linewidth=lw*0.5)
    ax.set_xlim([-xrange,xrange])
    ax.set_xlabel(r'$E-E_{Fermi}$')
    ax.set_ylabel('DOS(states/eV)')

def pdosplot(pdospath,ax,dospath=None,nscfpath=None,orbital=None,tag='pdos_atm',cm='coolwarm',xrange=10,lw=2):
    """
    Params:
        pdospath: a path to where pdos results are stored
        dospath: a path to where dos data is stored in which we find fermi energy level
        nscfpath: a path to where nscf output file is stored in which we can find fermi energy level
        cm: color map for plotting multiple curves 
        ax, tag, xrange: same as in dosplot function
        orbital: a dictionary/string that tells how the function
                 should prepare the plot. It has three format:
                 (1) "by element": plot pdos by elemental types
                 (2) "by orbital": plot pdos by orbital types(i.e.,1s,2s,2p,etc)
                 (3) a list of tuples containing specific elemental and orbital names,
                     for instance, [('Na','2p'),('Fe','3d')].
    """
    # First find fermi energy level
    if dospath is None and nscfpath is None:
        print('tell me where to find fermi energy level!!!')
        return
    elif nscfpath is None:
        datafiles = glob.glob(os.path.join(dospath,'*_dos.dat'))
        if len(datafiles)>1:
            print('tell me which file you want using:')
            for i,f in enumerate(datafiles):
                print("{}. {}\n".format(i,f))
            idx = int(input('Type it here:'))
            datafile = datafiles[idx]
        elif not datafiles:
            print('No DOS dat file found!!!')
            return
        else:
            datafile = datafiles[0]

        with open(datafile,'r') as f:
            fermi = f.readlines()[0]
        fermi = float(fermi.split()[-2])
        f.close()
    else:
        datafiles = glob.glob(os.path.join(nscfpath,'*_nscf.out'))
        if len(datafiles)>1:
            print('tell me which file you want using:')
            for i,f in enumerate(datafiles):
                print("{}. {}\n".format(i,f))
            idx = int(input('Type it here:'))
            datafile = datafiles[idx]
        elif not datafiles:
            print('No nscf output file found!!!')
            return
        else:
            datafile = datafiles[0]

        with open(datafile,'r') as f:
            content = f.readlines()
        f.close()

        fermi,i = None,80
        while i <len(content):
            if 'the Fermi energy is' in content[i]:
                fermi = float(content[i].split()[-2])
                i +=len(content)
            i+=1
        if fermi is None:
            print('did not find fermi energy in nscf output!!!')
            return
    
    # now load pdos files
    pdosfiles = glob.glob(os.path.join(pdospath,'*{}*'.format(tag)))
    temp = pd.read_csv(pdosfiles[0], delimiter='\s+',header=None,skiprows=[0]).to_numpy()
    totlen = len(temp)
    totcol = len(temp[0])
    if orbital=='by element':
        pdos = {}
        atmtyp = []
        for f in pdosfiles:
            mid = f.split('#')[-2]
            atm=mid[mid.find('(')+1:mid.find(')')]
            if atm in atmtyp:
                temp = pd.read_csv(f, delimiter='\s+',header=None,skiprows=[0]).to_numpy()[:,:3]
                pdos[atm][:,1:]+=temp[:,1:]
            else:
                atmtyp.append(atm)
                pdos[atm]=pd.read_csv(f, delimiter='\s+',header=None,skiprows=[0]).to_numpy()[:,:3]
    elif orbital=='by orbital':
        pdos = {}
        orbtyp = []
        for f in pdosfiles:
            mid = f.split('#')[-1]
            n,m = mid[:-1].split('(')
            orb=n+m
            if orb in orbtyp:
                temp = pd.read_csv(f, delimiter='\s+',header=None,skiprows=[0]).to_numpy()[:,:3]
                pdos[orb][:,1:]+=temp[:,1:]
            else:
                orbtyp.append(orb)
                pdos[orb]=pd.read_csv(f, delimiter='\s+',header=None,skiprows=[0]).to_numpy()[:,:3]
    elif isinstance(orbital,list):
        pdos = {}
        keytyp = []
        for comb in orbital:
            t1, t2 = comb
            key = t1+t2
            pdos[t1+'('+t2+')']=np.zeros((totlen,3))
            keytyp.append(key)
        for f in pdosfiles:
            mid1,mid2 = f.split('#')[-2:]
            atm=mid1[mid1.find('(')+1:mid1.find(')')]
            n,m = mid2[:-1].split('(')
            if atm+n+m in keytyp:
                pdos[atm+'('+n+m+')']+=pd.read_csv(f, delimiter='\s+',header=None,skiprows=[0]).to_numpy()[:,:3]

    else:
        print('No orbital info provided,exiting...')
        return

    # prepare color
    clrs = plt.get_cmap(cm,len(list(pdos.keys())))
    for i,k in enumerate(list(pdos.keys())):
        if totcol>3:
            ax.plot(pdos[k][:,0]-fermi,pdos[k][:,1],color=clrs(i),linewidth=lw)
            ax.plot(pdos[k][:,0]-fermi,-pdos[k][:,2],color=clrs(i),label=k,linewidth=lw)
        else:
            ax.plot(pdos[k][:,0]-fermi,pdos[k][:,1],color=clrs(i),label=k,linewidth=lw)

    ymin,ymax=ax.get_ylim()
    ax.plot([0,0],[ymin,ymax],'k--',linewidth=lw)
    ax.set_ylim([ymin,ymax])
    # add a thin horizontal line at DOS=0
    ax.plot([-xrange,xrange],[0,0],'k-',linewidth=lw*0.5)
    ax.set_xlim([-xrange,xrange])
    ax.set_xlabel(r'$E-E_{Fermi}$')
    ax.set_ylabel('PDOS(states/eV)')
    return pdos,fermi

def pdosplot_soc():
    """
    Plot pdos from noncolin+soc calculation
    """
    pass

if __name__ == "__main__":
    pdospath = 'C://Users//liu_s//Documents//BW_results//SA//Naf1//GS//DOS-PDOS'
    dospath = 'C://Users//liu_s//Documents//BW_results//SA//Naf1//GS//DOS-PDOS'
    nscfpath = 'C://Users//liu_s//Documents//BW_results//SA//Naf1//GS//DOS-PDOS'
    fig = plt.figure(figsize=(8,6))
    ax = fig.add_subplot(111)
    res,femiE=pdosplot(pdospath,ax,nscfpath=nscfpath,orbital='by element',xrange=15)