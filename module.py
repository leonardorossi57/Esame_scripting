import numpy as np
import pandas as pd

def generate_speckle_field(corr, source_size, dist, scatt_num): # Use, for the first field, a "monte carlo" method
    if corr == 0:
        pass
        # If there is no correlation length in the source, extract random points on the source area and add a spherical wave for each of them. The 
        # resultung sum is the speckle field.
    else:
        pass
        # If there is a nonzero correlation length, the wave from each scatterer is profiled by an Airy disc. The sum and the speckle field are 
        # calculated in the same way as above
    
    # return the array with the field (I will probably use a pandas data structure)

def filter(filter_type, field, dist_2):
    # This functions just performs a FFT, profiles the spectrum with the appropriate function (step or gaussian) and then IFFTs.
    if filter_type == 'Rectangular':
        # Do what explained above
        pass
    else:
        # Do what explained above
        pass

def create_pattern(field):
    # This function profiles the filtered speckle field with a double slit and then propagates it on the final screen, 
    # creating the interference pattern to analyze.
    pass
    # Return the interference pattern.