## Important Things about the Partitions on Expanse@XSEDE
- New partition of `compute`, having 128 cores per node, runs out your core time very quickly. So use it cautiously.

- Unless for extremely extensive job, one might want to submit job to `shared` partition

- GPU nodes are separate from CPU nodes

- The limit of walltime on Expanse is still 48hrs

- time limit on debug node is 30min.

- docker container is not supported on expanse

## Manage Software Environment on Expanse

- Separate shell sessions allow you to set default environments separately. Shell variables are only available in the session where they are created

- `LD_LIBRARY_PATH` is an environmental variable that allow you to tell the system where to find the softwares that you compiled

- Common commands for manipulating modules:
    - `module purge` unload all packages
    - `module load` load packages
    - `module spider` a new way to search for packages that might be pre-installed on Expanse (details of package dependence included)
    - Bridges2 and Expanse are running on `CentOS`

- Examples for different packages
    - you can find example `.sb` files at `/cm/shared/examples/sdsc/`, which is only available on Expanse.

- Good practice before submitting jobs
    - check if the `slurm`,`cpu`, and `gcc` modules are loaded, replace `cpu` with `gpu` if you want to run jobs with GPUs.
    - if you specify the version numbers of `gcc`, and use the command of `module load`, the system will **only list the packages that compatible with `gcc`.**

- Currently, no MPI support for python codes (i.e. mpi4py).

- The file system can also be accessed through `https://portal.expanse.sdsc.edu`, where files can be uploaded and job can be submitted directly.
