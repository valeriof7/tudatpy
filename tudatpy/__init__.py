'''
Copyright (c) 2010-2024, Delft University of Technology
All rigths reserved

This file is part of the Tudat. Redistribution and use in source and
binary forms, with or without modification, are permitted exclusively
under the terms of the Modified BSD license. You should have received
a copy of the license with this file. If not, please or visit:
http://tudat.tudelft.nl/LICENSE.
'''

# Stdlib imports
import sys

# Import tudat kernel
from tudatpy import kernel

# Tudatpy version information
from tudatpy._version import *

# Import Tudat version information
from tudatpy.kernel import \
    _tudat_version, \
    _tudat_version_major, \
    _tudat_version_minor, \
    _tudat_version_patch

"""
Expose all tudat kernel modules directly from tudatpy
"""

# Retrieve all tudat kernel objects
kernel_objects = {name: object for name, object in sys.modules.items() if name.startswith('tudatpy.kernel')}

# Modify sys.modules so that all kernel objects can be imported directly from tudatpy
for name, kernel_object in kernel_objects.items():
    new_name = name.replace('tudatpy.kernel', 'tudatpy', 1)
    # If the new name does not overwrite any existing tudatpy modules
    if new_name not in sys.modules.keys():
        # Expose kernel object directly from tudatpy
        sys.modules[new_name] = kernel_object