#!/usr/bin/env bash

## You might want to use this script to install QE on computational cluster platform
#SBATCH --job-name=config-quantum-espresso
#SBATCH --account=use300
#SBATCH --partition=shared
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --time=01:00:00
#SBATCH --output=config-quantum-espresso.o%j.%N

declare -xr COMPILER_MODULE='gcc/10.2.0'
declare -xr MPI_MODULE='openmpi/4.0.5-gcc10.2.0'
declare -xr MKL_MODULE='mkl/2020.4.304'

declare -xr QUANTUM_ESPRESSO_VERSION='6.7'
declare -xr QUANTUM_ESPRESSO_BUILD='mpi'
declare -xr QUANTUM_ESPRESSO_INSTALL_DIR="${PWD}/qe-6.7"


module purge
module load "${COMPILER_MODULE}"
module load "${MPI_MODULE}"
module load "${MKL_MODULE}"
module list
printenv

cd "${QUANTUM_ESPRESSO_INSTALL_DIR}"
./configure --prefix="${QUANTUM_ESPRESSO_INSTALL_DIR}"
make all
