# Logs for Major Changes in the Codes
---
>**Update @05/01/21**: collect useful scripts in the folder `workflow_scripts` for running
batch jobs on different HPC platform.

>**Update @04/21/21**: updated `run_cases.py` for running multi-node jobs on HPC server configured with the slurm system.

>**Update @01/21/21**: updated README to clarify some aspects of running jobs on slurm system.

>**Update @12/28/20**: due to the change of system environment on campuscluster, `run_cases.py`,`run_cases_bridges2.py` and `run_cases_phonon.py` in the folder `run_cases_script` are updated for submitting jobs to SLURM batch system.

>**Update @12/22/20**: add interactive commands in `run_cases.py` to ask users if they want to change information of node number, core number per node, and walltime in `.pbs` file.

>**Update @12/15/20**: (1) edited the "singlePointCalculator" class in qe2cif.py, enabling it reading total force and cell pressure; (2) updated "run_cases.py" so that 'restart' input file can also be submitted to computing platform.

>**Update @06/22/20**: (1)fixed typos in `prep_ppipt`,`prep_dosipt`,and `prep_pdosipt`,(2)add job dependency in `run_cases.py`,(3) finished the tests on `qe2DDEC.py`.