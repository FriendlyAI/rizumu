# -*- coding: utf-8 -*-
from os import getcwd, mkdir
from sys import exit

from menu import Menu

# Check cwd
if not getcwd().endswith('rizumu'):
    print('Error: rizumu must be run from the base directory (rizumu/)')
    exit()

# Make required directories
try:
    mkdir('library/')
    mkdir('library/tracks')
except FileExistsError:
    pass

# Open menu
menu = Menu()
