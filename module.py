import numpy as np
import pandas as pd
from scipy.fft import fft, ifft, fftshift, ifftshift

def generate_speckle_field(corr, source_size, dist, scatt_num, wavelen): # Use, for the first field, a "monte carlo" method

    corr = corr / 1e4 # Convert to cm
    wavelen = wavelen / 1e7

    screen_size = 10 # [cm] (section of the beam under analysis)
    dx = 0.05 # [cm] (resolution)
    dim = int(screen_size/dx) + 1 # Dimension of the arrays
    field = np.zeros(dim, dtype = complex) # Array containing the speckle field
    screen = np.linspace(-screen_size/2, screen_size/2, dim)

    if corr == 0:
        # If there is no correlation length in the source, extract random points on the source area and add a spherical wave for each of them. The 
        # resulting sum is the speckle field.
        for i in range(scatt_num):
            scatt = np.random.uniform(-source_size/2, source_size/2) # i-th scatterer position
            phase_shift = np.random.uniform(-np.pi, np.pi) # Random phase
            field += np.exp(1j * 2 * np.pi * np.sqrt(dist ** 2 + (scatt - screen) ** 2)/wavelen + 1j * phase_shift/wavelen)/scatt_num # Add the field produced by the source point (Huygens principle)
    else:
        # If there is a nonzero correlation length, the wave from each scatterer is profiled by an Airy disc (or maybe a gaussian function is better). 
        # The sum and the speckle field are calculated in the same way as above

        for i in range(scatt_num):
            scatt = np.random.uniform(-source_size/2, source_size/2) # i-th scatterer position
            phase_shift = np.random.uniform(-np.pi, np.pi) # Random phase
            # Add the field produced by the source point (Huygens principle) with gaussian profile
            field += np.exp(1j * 2 * np.pi * np.sqrt(dist ** 2 + (scatt - screen) ** 2)/wavelen + 1j * phase_shift/wavelen) * np.exp(-((screen - scatt)/corr) ** 2)/scatt_num
    
    # return the array with the field 
    return field, screen

def filter(filter_type, field, filter_width):

    filter_width = filter_width / 10 # Convert to cm

    screen_size = 10 # [cm] (section of the beam under analysis)
    dx = 0.05 # [cm] (resolution)
        
    kspace_size = np.pi/dx
    dk = 2 * np.pi/screen_size
    dim = int(2 * kspace_size/dk) + 1 # Dimension of the arrays
    kspace = np.linspace(-kspace_size, kspace_size, dim)

    # This functions just performs a FFT, profiles the spectrum with the appropriate function (step or gaussian) and then IFFTs.
    if filter_type == 'Rectangular':
        # Do what explained above

        transf = fftshift(fft(field))
        transf[abs(kspace) > filter_width/2] = 0

        filt_field = ifft(ifftshift(transf))
    else:
        # Do what explained above
        profile = np.exp(-(kspace / filter_width) ** 2)
        transf = fftshift(fft(field))
        transf = transf * profile

        filt_field = ifft(ifftshift(transf))

    return filt_field

def create_pattern(field, dist_2, slits_dist, slit_width, screen, dim, wavelen):
    # This function profiles the filtered speckle field with a double slit and then propagates it on the final screen, 
    # creating the interference pattern to analyze.

    pattern = np.zeros(dim, dtype = complex)
    index = np.arange(dim)
    slit_1 = np.logical_and(screen[index] > -slits_dist/2 - slit_width, screen[index] < -slits_dist/2 + slit_width)
    slit_2 = np.logical_and(screen[index] > slits_dist/2 - slit_width, screen[index] < slits_dist/2 + slit_width)
    slit_index = index[np.logical_or(slit_1, slit_2)]

    for i in slit_index:
        pattern += field[i] * np.exp(1j * 2 * np.pi * np.sqrt(dist_2 ** 2 + (screen[i] - screen) ** 2)/wavelen)/dim

    # Return the interference pattern.
    return pattern