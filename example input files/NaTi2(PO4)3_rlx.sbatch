#!/bin/bash
#SBATCH --nodes=4
#SBATCH --ntasks-per-node=12
#SBATCH --time=3:00:00
#SBATCH --job-name="bands"
#SBATCH --partition=beckman


module load python/3
module load intel/18.0
cd C:\Users\liu_s\Desktop\CODE\qeAPI

# make a private copy of the potentials in the RAM disk
# aprun -n8 -N1 cp -a /home/$USER/pseudo /dev/shm/pseudo

 

mpirun  ./pw.x -npool 8 -in C:\Users\liu_s\Desktop\CODE\qeAPI\NaTi2(PO4)3_rlx.in > C:\Users\liu_s\Desktop\CODE\qeAPI\NaTi2(PO4)3_rlx.out 
