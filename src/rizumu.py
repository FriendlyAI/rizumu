# -*- coding: utf-8 -*-
from os import getcwd, mkdir
from os.path import isfile
from sys import exit

from menu import Menu

# Check cwd
if not getcwd().endswith('rizumu'):
    print('Error: rizumu must be run from the base directory (rizumu/)\nExiting...')
    exit()

# Check ctaff dependency
if not isfile('bin/ctaff'):
    print('Error: rizumu requires ctaff to be compiled to rizumu/bin/\nExiting...')
    exit()

# Make required directories
try:
    mkdir('library/')
except FileExistsError:
    pass
try:
    mkdir('library/tracks')
except FileExistsError:
    pass

# Open menu
menu = Menu()
