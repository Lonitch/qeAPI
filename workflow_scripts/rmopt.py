"""
This script removes output files that have their names listed in "restart.txt" 
or "modify.txt".

Created by Sizhe Liu
"""

import os

print('Which list of files you want to delete?'+
' ("c" for "complete.txt", "r" for "restart.txt", and "m" for "modify.txt")')
look = input('Type it here: ')
if look =='r':
        look = 'restart.txt'
elif look=='m':
        look = 'modify.txt'
elif look=='c':
        look = 'complete.txt'
else:
        print('You just gave me an unrecognized input!!!')

pwd = os.getcwd()
good = False
for file in os.listdir(pwd):
        if file.endswith(look):
                good = True
                break

if good:
        with open(os.path.join(pwd,look)) as f:
                content = f.read().split('\n')
        for line in content:
                if line is not '':
                        temp = line.split('.')[0]+'.out'
                        try:
                                os.remove(os.path.join(pwd,temp))
                        except:
                                print('{} is already removed!'.format(temp))
else:
        print('No restart.txt was found here!')
