# Python-QE API
A set of tools are listed here for preparing and analyzing DFT calculations using Quantum Espresso. This repository(or **repo**) contains three pieces of Python scripts:

- `raw2qe.py`,a collection of functions and classes that transform CIF files into input texts.
- `qe2cif.py`, a collection of functions that reads output files from QE calculations and write atomic configurations into CIF files
- `qe2DDEC.py`, a collection of functions that reads charge density CUBE files, and analyze them using DDEC6 method to give bond order, and overlap population information of arbitrary atomic configurations.

And three **jupyter notebooks** are inluded to show some examples of using functions in the three script files:

- `pWprep_test.ipynb` shows the use of `raw2qe.py`

- `qe2DDEC_test.ipynb` shows the use of `qe2DDEC.py`

- `qe2cif_test.ipynb` shows the use of `qe2cif.py`

The sections below are arranged as
- [Install Python](#install-python)       
- [Install Packages](#install-packages)    
- [Compile Quantum Espresso](#compile-quantum-espresso)        
    - [Without libxc](#without-libxc)        
    - [With Libxc](#with-libxc)  
- [Set up file system ready for DFT calculation](#set-up-file-system-ready-for-dft-calculation)   
- [Submit Calculation jobs](#submit-calculation-jobs)        
    - [!!! The workflow for running calculations](#-the-workflow-for-running-calculations)
- [Navigation of the Repo](#navigation-of-the-repo)
- [Citation](#citation)

## Install Python

Due to the variety of Windows/Mac/Linux OS distributions, the arguably easiest way to install Python is to install [Anaconda](https://www.anaconda.com/products/individual), a distribution of Python 3.7 along with some pre-installed numerical packages (e.g. [numpy](https://numpy.org/), and [scipy](https://www.scipy.org/)). The complete list of pre-installed packages in anaconda can be found [here](https://www.anaconda.com/open-source).

- For installation instruction on Windows OS, click [here](https://docs.anaconda.com/anaconda/install/windows/).
- For installation instruction on Mac OS, click [here](https://docs.anaconda.com/anaconda/install/mac-os/).

Once you installed `Anaconda`, open the `Anaconda Navigator` by finding it in your start navigation or in search bar. And the initial GUI looks like the picture shown below:
![nav](images/nav-defaults.png)

Now click the `install` button below **jupyter notebook**. Jupyter notebook provides an intuitive way to write and inteprete your Python code as we shall see later.
### Install Packages
We need to install `ASE` package (check the documentation [here](https://wiki.fysik.dtu.dk/ase/)) in your `Anaconda` distribution. To do so, click the `Environment` in the navigator shown above to get
![pkg-list](images/nav-pkg-list.png)
1. If `ASE` is not installed, you can find it by navigating to the drop-down menu `Not installed` and then searching for `ASE`:
![nav-pkg-opt](images/nav-pkg-list-options.png)
2. Select the package you want to install, and click `Apply` in the popup window. 
3. Now you can use `ASE` in your python code.

To use **jupyter notebook**, we simply open **Anaconda Navigation** and click the **jupyter** icon. Your browser will start automatically and show the following GUI:
![init-jupyter](images/init-jupyter.PNG)
You can start by creating a **folder** with the `New` drop-down menu:
![init-jupyter-2](images/init-jupyter-2.PNG)
The name of your new folder will be **Untitled folder** but you can always change its name later. We now open **Untitled folder** in **jupyter** to arrive at the following interface:
![init-jupyter-3](images/init-jupyter-3.PNG)
Create a `Python 3` notebook and open it to get
![init-jupyter-4](images/init-jupyter-4.PNG)
where the command window in green rectangle is the **current active window**. Let's write a simple command and run it using `shift+enter` combo:
![init-jupyter-5](images/init-jupyter-5.PNG)
From the picture above, we know that
- **Jupyter notebook** create new empty command window below the previously active window
- The output of the previously active window shows up right before the current active window.
## Compile Quantum Espresso
In this section we provide a way to compile Quantum Espresso on normal university-level computation platform, with and without external libraries. The file system for each individual user is run on a Linux system with an access to `home` folder.
### Without libxc
- Create a folder `dft` in your `home` folder 
- Enter new folder `cd dft`
- Download newest QE package [here](https://github.com/QEF/q-e/releases/tag/qe-6.4) to your personal computer, then upload the downloaded `tar.gz` file to `dft` folder using **FileZilla** or similar software.
- Run `tar -xvf qe-XXXX.tgz` to unzip the source files in `dft\qe-X.Y.Z` where `X`,`Y`, and `Z` are version numbers.
- Load required compiling modules by 
`module load gcc`
and
`module load intel/18.0` or `module load python/3`
- `cd qe-X.Y.Z`to get into source folder
- Configure source files by running 
`./configure -enable-openmp=yes -with-scalapack=intel`
- Compile
`make all`

### With Libxc
>**Important Note:** Some exchange-correlation functionals in [Libxc](https://www.tddft.org/programs/libxc/) is not well-tested for all classes of materials. Make sure you know what you're doing if you want to use Libxc with QE.

- Install libxc using autotool:
(1) Download `libxc` [here](https://www.tddft.org/programs/libxc/download/)
(2) Upload the `tar.gz` file to `dft` folder
(3) Unzip the file by using `tar -xvf libxc-x.y.z.tar.gz`, where `x`,`y`, and `z` are version numbers again
(3) Run the following command(no change is needed):
`./configure --prefix=PATH/TO/LIBXC`
`make`
`make check`
`make install`
- Configure QE
`cd qe-X.Y.Z/`
`module load gcc intel/18.0`
`./configure -enable-openmp=yes -with-scalapack=intel -with-libxc=yes -with-libxc-prefix=PATH/TO/LIBXC -with-libxc-include=PATH/TO/LIBXC/include`

- Change make.inc file and make
(1) open the `make.inc` file in the folder `qe-X.Y.Z` using `nano make.inc`
(2) change the `DFLAGS` line into
`	DFLAGS         =  -D__DFTI -D__LIBXC -D__MPI -D__SCALAPACK -D__SPIN_BALANCED
`
(3) save the file, and run `make all`

## Set up file system ready for DFT calculation
1. create a folder at `/home/` named as `/pseudo/` to store your pseudopotential files
2. Download full-element pseudopotential package. My personal favorite is [GBRV Pseudopotential](https://www.physics.rutgers.edu/gbrv/). Other good resources are [Pseudo Dojo](http://www.pseudo-dojo.org/), and [SSSP](https://www.materialscloud.org/discover/sssp/table/efficiency) on Material cloud.
3. Before you upload your pseudopotential files onto computation platform, **it is recommended to change your commonly-used pseudopotentials' name into a format of `X.upf`**, with `X` being the element symbol. Below is what my `pseudo` folder looks like
![pseudo-folder](images/pseudo-folder.PNG)

where `rVV10_kernel_table` and `vdW_kernel_table` are generated by runing the `generate_rVV10_kernel_table.x` and `generate_vdW_kernel_table.x` in the `/PW/src` subfolder of your QE installation. **You will use them when you have strong van der Waals' interactions in your atomic system**.
4. The `outdir` option in your input file should always be `"/home/netID/scratch/"`+**unique name** to your calculation case. If your `.in` files have unique names, `raw2qe.py` sets the `outdir` to be `/home/netID/scratch/`+ your input file name automatically.
>Scratch is a **temporary storage space** that saves your output files for at most 30 days. Make sure you transfer your data after the calculations are done.
5. Create a `inputdir` folder to store all your input file. In the same folder, create shortcuts to your QE executables by using the following command(in your `inputdir` folder):

- `ln -s /path/to/qe/installation/PW/src/pw.x pw.x`
- `ln -s /path/to/qe/installation/PP/src/pp.x pp.x`
- `ln -s /path/to/qe/installation/PP/src/dos.x dos.x`
- `ln -s /path/to/qe/installation/PP/src/projwfc.x projwfc.x`
> We use symbolic links to avoid complicated path when we run DFT calculations.

## Submit Calculation jobs
The `run_cases.py` in this repo prepares `PBS` files for batch job submission on computation platform(i.e. campuscluster). It generates `PBS` files for all the `.in` files in your `inputdir` folder. It changes executable command based on the names of input files. The complete rules for running QE according to `run_cases.py` are listed below:

- If the file is named as `xxxx.in` without symbol of `_`, `run_cases.py` ask the system to run the command of 
`mpirun ./pw.x -npool 8 -in xxxx_pp.in > xxxx_pp.out`

- If `_pp` in the name of a `.in` file, ask the system to run the command of `mpirun ./pp.x -in xxxx_pp.in > xxxx_pp.out`

- If `_dos` in the name of a `.in` file, ask the system to run the command of `./dos.x -in xxxx_dos.in > xxxx_dos.out`

- If `_pdos` in the name of a `.in` file, ask the system to run the command of `./projwfc.x -in xxxx_pdos.in > xxxx_pdos.out`.

A typical `PBS` file is shown below:
![pbs](images/pbs.PNG)

where 

1. `#PBS -l nodes=X:ppn=12` set how many number of computation nodes and how many CPU cores per node you want to use for the calculation.

2. `#PBS -q eng-research` choose your job queue (the queue is `eng-research`).

3. `#PBS -l walltime=01:00:00` tells the system to kill your job after some time (the job will be killed after 1 hr in this case). **The maximum walltime is 4hrs**.

4. `#PBS -N rlx` gives a name for your job(the name is `rlx` in this case).

5. `#PBS -j os` combines all the system error message in to a single file.

6. `cd /home/yourID/inputdir` is required for the system to find your links to `pw.x`, `pp.x` etc.

### !!! The workflow for running calculations
1. Upload all your input files to `inputdir` folder
2. Make sure `run_cases.py` is also in the `inputdir` folder and load python3 module by `module load python/3`
3. Run `run_cases.py` by `python3 run_cases.py`
4. Many `pbs` files should be created now, run `./serialjob` in your command line to submit all your jobs.
5. Wait till `./serialjob` command finishes and use `qstat -u yourNetID` to check the status of your jobs. 
6. Jobs with `C` status are finished or they are running out of the walltime. Jobs with `R` are running, and jobs with `Q` status are still waiting in the queue.
7. Once all your calculations are done, download your data and use the functions in `qe2DDEC.py` and `qe2cif.py` to start your analysis.
 
## Navigation of the Repo
>**Important note:** Please pay attention to the comment lines starting with **!!!** in the code. Those lines tell you how to change the code if you're using different pseudopotential or you are using it in different operating system environment.
- `pwPrep_test.ipynb` shows the examples of using `raw2qe.py` to
(1) Update options in input files
(2) Prepare input files for `pw.x`,`dos.x`, and `projwfc.x`
- `qe2DDEC.ipynb` shows the examples of using `qe2DDEC.py` to 
(1) prepare `job_control.txt` to initialize DDEC6 analysis
(2) run DDEC6 binary executable in a pythonic way
(3) extract useful infomation from the analyses, e.g. overlap population, bond orders (**under construction**)
- `qe2cif.ipynb` shows the examples of using `qe2cif.py` to
(1) read atomic configurations from QE outputs
(2) save relaxed atomic configurations in a `cif` format
(3) adjust atoms' info using `ASE`


## Citation
Please cite our [paper](https://pubs.acs.org/doi/abs/10.1021/acs.jpcc.8b12455?casa_token=xfrdGK26yPoAAAAA:DTUMcL_IFY5QfN4QwbwBKDjPrjIRaytsUORZEgbSFpGsNX2euNxbZKN0djXgdFbOv8QqF7LFRhvX56A) if you decide to use our code for your research:

[1] Liu, Sizhe, and Kyle C. Smith. "Intercalated Cation Disorder in Prussian Blue Analogues: First-Principles and Grand Canonical Analyses." The Journal of Physical Chemistry C 123.16 (2019): 10191-10204.

If you end up using our `qe2DDEC.py`, please cite the following papers too:

[2] T. A. Manz and N. Gabaldon Limas, “Introducing DDEC6 atomic population analysis: part 1. Charge partitioning theory and methodology,” RSC Adv., 6 (2016) 47771-47801. 

[3] N. Gabaldon Limas and T. A. Manz, “Introducing DDEC6 atomic population analysis: part 2. Computed results for a wide range of periodic and nonperiodic materials,” RSC Adv., 6 (2016) 45727-45747. 