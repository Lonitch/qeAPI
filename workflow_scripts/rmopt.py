"""
This script removes output files that have their names listed in "restart.txt".

Created by Sizhe Liu
"""

import os

pwd = os.getcwd()
good = False
for file in os.listdir(pwd):
        if file.endswith('restart.txt'):
                good = True

if good:
        with open(os.path.join(pwd,'restart.txt')) as f:
                content = f.read().split('\n')
        for line in content:
                if line is not '':
                        temp = line.split('.')[0]+'.out'
                        os.remove(os.path.join(pwd,temp))
else:
        print('No restart.txt was found here!')
