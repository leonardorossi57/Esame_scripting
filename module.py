import numpy as np
import pandas as pd
from scipy.fft import fft, ifft, fftshift, ifftshift

def generate_speckle_field(corr, source_size, dist, scatt_num, wavelen): # Use, for the first field, a "monte carlo" method

    corr = corr / 1e4 # Convert lengths to cm
    wavelen = wavelen / 1e7

    screen_size = 20 # [cm] (section of the beam under analysis)
    dx = 0.02 # [cm] (resolution)
    dim = int(screen_size/dx) + 1 # Dimension of the arrays
    field = np.zeros(dim, dtype = complex) # Array containing the speckle field
    screen = np.linspace(-screen_size/2, screen_size/2, dim)

    if corr == 0:
        # If there is no correlation length in the source, extract random points on the source area and add a spherical wave for each of them. The 
        # resulting sum is the speckle field.
        for i in range(scatt_num):
            scatt = np.random.uniform(-source_size/2, source_size/2) # i-th scatterer position
            phase_shift = np.random.uniform(-np.pi, np.pi) # Random phase
            # Add the field produced by the source point (Huygens principle)
            field += np.exp(1j * 2 * np.pi * np.sqrt(dist ** 2 + (scatt - screen) ** 2)/wavelen + 1j * phase_shift/wavelen)/np.sqrt(dist ** 2 + (scatt - screen) ** 2) 
    else:
        # If there is a nonzero correlation length, the wave from each scatterer is profiled by an Airy disc (or maybe a gaussian function is better). 
        # The sum and the speckle field are calculated in the same way as above

        for i in range(scatt_num):
            scatt = np.random.uniform(-source_size/2, source_size/2) # i-th scatterer position
            phase_shift = np.random.uniform(-np.pi, np.pi) # Random phase
            # Add the field produced by the source point (Huygens principle) with gaussian profile. This has not been tested yet.
            field += np.exp(1j * 2 * np.pi * np.sqrt(dist ** 2 + (scatt - screen) ** 2)/wavelen + 1j * phase_shift/wavelen) * np.exp(-((screen - scatt) * corr) ** 2)/np.sqrt(dist ** 2 + (scatt - screen) ** 2)
    
    # return the array with the field 
    return field/scatt_num, screen

def filter(filter_type, field, filter_width):

    screen_size = 20 # [cm] (section of the beam under analysis)
    dx = 0.02 # [cm] (resolution)
        
    kspace_size = 2 * np.pi/dx
    dk = 2 * np.pi/screen_size
    dim = int(kspace_size/dk) + 1 # Dimension of the arrays
    kspace = np.linspace(-kspace_size / 2, kspace_size / 2, dim)

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

    slits_dist = slits_dist / 10 # Convert lengths to cm
    slit_width = slit_width / 10
    wavelen = wavelen / 1e7

    pattern_1 = np.zeros(dim, dtype = complex) # Pattern due to first slit
    pattern_2 = np.zeros(dim, dtype = complex) # Pattern due to second slit

    index = np.arange(dim)
    slit_1 = np.logical_and(screen >= -slits_dist/2 - slit_width/2, screen <= -slits_dist/2 + slit_width/2)
    slit_2 = np.logical_and(screen >= slits_dist/2 - slit_width/2, screen <= slits_dist/2 + slit_width/2)
    index_1 = index[slit_1]
    index_2 = index[slit_2]

    for i in index_1:
        pattern_1 += field[i] * np.exp(1j * 2 * np.pi * np.sqrt(dist_2 ** 2 + (screen[i] - screen) ** 2)/wavelen)/np.sqrt(dist_2 ** 2 + (screen[i] - screen) ** 2)

    for i in index_2:
        pattern_2 += field[i] * np.exp(1j * 2 * np.pi * np.sqrt(dist_2 ** 2 + (screen[i] - screen) ** 2)/wavelen)/np.sqrt(dist_2 ** 2 + (screen[i] - screen) ** 2)


    patt_intensity = np.abs(pattern_1 + pattern_2).real ** 2
    prof_intensity = np.abs(pattern_1).real ** 2 + np.abs(pattern_2).real ** 2 
    # Simply neglecting the interference term could be a good approximation for the profile

    # Return the interference pattern and the profile.
    return patt_intensity, prof_intensity

# dist_2 = 1e4 # [cm]
# wavelen = 500 # [nm]
# slit_width = 1 # [mm]

def process_pattern(pattern_data):
    cut = 4 # [cm]

    screen = pattern_data['screen'].to_numpy()
    pattern = pattern_data['pattern'].to_numpy()
    profile = pattern_data['profile'].to_numpy()

    pattern_cut = pattern[np.logical_and(screen >= -cut, screen <= cut)] # Cut away uninteresting part
    screen_cut = screen[np.logical_and(screen >= -cut, screen <= cut)]
    profile_cut = profile[np.logical_and(screen >= -cut, screen <= cut)]

    patt_norm = pattern_cut / profile_cut # Pattern modulo finite slit size effects

    patt_data_norm = pd.DataFrame({
        'screen': screen_cut,
        'pattern': patt_norm
    })

    # Calculation of visibility

    vis = (np.max(patt_norm) - np.min(patt_norm)) / (np.max(patt_norm) + np.min(patt_norm)) 
    # The normalized pattern should be a sinusoid, so the maximum and the minimum are well defined
    
    return patt_data_norm, vis