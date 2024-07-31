import numpy as np
import pandas as pd
from scipy.fft import fft, ifft, fftshift, ifftshift
from scipy.optimize import curve_fit
import plotly.express as px

def generate_speckle_field(corr, source_size, dist, scatt_num, wavelen): # Use, for the first field, a "monte carlo" method

    corr = corr / 1e4 # Convert lengths to cm
    wavelen = wavelen / 1e7

    screen_size = 20 # [cm] (section of the beam under analysis)
    dx = 0.01 # [cm] (resolution)
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
            field += np.exp(1j * 2 * np.pi * np.sqrt(dist ** 2 + (scatt - screen) ** 2)/wavelen + 1j * phase_shift/wavelen)/np.sqrt(1 + (scatt - screen) ** 2/dist ** 2) 
    else:
        # If there is a nonzero correlation length, the wave from each scatterer is profiled by an Airy disc (or maybe a gaussian function is better). 
        # The sum and the speckle field are calculated in the same way as above

        for i in range(scatt_num):
            scatt = np.random.uniform(-source_size/2, source_size/2) # i-th scatterer position
            phase_shift = np.random.uniform(-np.pi, np.pi) # Random phase
            # Add the field produced by the source point (Huygens principle) with gaussian profile. This has not been tested yet.
            field += np.exp(1j * 2 * np.pi * np.sqrt(dist ** 2 + (scatt - screen) ** 2)/wavelen + 1j * phase_shift/wavelen) * np.exp(-((screen - scatt) * corr) ** 2)/np.sqrt(1 + (scatt - screen) ** 2 / dist ** 2)
    
    # return the array with the field 
    return field/scatt_num, screen

def filter(filter_type, field, filter_width):

    screen_size = 20 # [cm] (section of the beam under analysis)
    dx = 0.01 # [cm] (resolution)
        
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

    pattern = np.zeros(dim, dtype = complex)

    index = np.arange(dim)
    slit_1 = np.logical_and(screen >= -slits_dist/2 - slit_width/2, screen <= -slits_dist/2 + slit_width/2)
    slit_2 = np.logical_and(screen >= slits_dist/2 - slit_width/2, screen <= slits_dist/2 + slit_width/2)
    slit_index = index[np.logical_or(slit_1, slit_2)]

    for i in slit_index:
        pattern += field[i] * np.exp(1j * 2 * np.pi * np.sqrt(dist_2 ** 2 + (screen[i] - screen) ** 2)/wavelen)/np.sqrt(1 + (screen[i] - screen) ** 2 / dist_2 ** 2)

    # Return the interference pattern and the profile.
    return np.abs(pattern).real ** 2

# dist_2 = 1e4 # [cm]
# wavelen = 500 # [nm]
# slit_width = 1 # [mm]

def calc_extremal(vect, x_axis, tolerance):

    vect_max = []
    vect_min = []

    dx = x_axis[1] - x_axis[0]

    i = 0
    while i < len(vect):
        if vect[i] == np.max(vect[np.logical_and(x_axis > x_axis[i] - tolerance/2, x_axis < x_axis[i] + tolerance/2)]):
            vect_max.append(i)
            i += round(tolerance/(2 * dx))
        elif vect[i] == np.min(vect[np.logical_and(x_axis > x_axis[i] - tolerance/2, x_axis < x_axis[i] + tolerance/2)]):
            vect_min.append(i)
            i += round(tolerance/(2 * dx))
        else:
            i += 1

            
    return vect_max, vect_min

def process_pattern(pattern_data, slit_width, wavelen, dist_2, guess, A_1, A_2):

    cut = 2.5 # [cm]
    slits_dist = pattern_data['slits_dist'][0]

    with open('numbers.txt', 'r') as f:
        avg_intensity = float(f.read())

    def fit_up(vect, vis, A): # Function for fitting the upper profile
        return 2 * A * avg_intensity * (np.sinc( (vect + slits_dist/2) * slit_width / (wavelen * dist_2)) ** 2 + np.sinc((vect - slits_dist/2) * slit_width / (wavelen * dist_2)) ** 2 + 2 * np.sinc(vect * slit_width / (wavelen * dist_2)) ** 2 * vis )
    
    # def fit_down(vect, vis, A): # Function for fitting the lower profile
    #     return 2 * A * avg_intensity * (np.sinc((vect + slits_dist/2) * slit_width / (wavelen * dist_2)) ** 2 + np.sinc((vect - slits_dist/2) * slit_width / (wavelen * dist_2)) ** 2 - 2 * np.sinc(vect * slit_width / (wavelen * dist_2)) ** 2 * vis )

    slits_dist = slits_dist / 10 # Convert lengths to cm
    slit_width = slit_width / 10
    wavelen = wavelen / 1e7 

    tolerance = 0.1 # [cm] (consider adding this as an input)

    screen = pattern_data['screen'].to_numpy()
    pattern = pattern_data['pattern'].to_numpy()

    pattern_cut = pattern[np.logical_and(screen >= -cut, screen <= cut)] # Cut away uninteresting part (the approximation used for the fit only works for small y)
    screen_cut = screen[np.logical_and(screen >= -cut, screen <= cut)]

    patt_max, patt_min = calc_extremal(pattern_cut, screen_cut, tolerance)

    popt_up, pcov_up = curve_fit(fit_up, screen_cut[patt_max], pattern_cut[patt_max], p0 = (guess, A_1))
    # popt_down, pcov_up = curve_fit(fit_down, screen_cut[patt_min], pattern_cut[patt_min], p0 = (guess, A_2))

    patt_up = fit_up(screen, *popt_up)
    # patt_down = fit_down(screen, *popt_down)

    norm = fit_up(screen_cut, *popt_up)

    patt_norm = pattern_cut/norm # Normalized pattern

    patt_data_proc = pd.DataFrame({
        'screen': screen,
        'pattern': pattern,
    #     'prof_down': patt_down,
        'prof_up': patt_up
    })

    patt_data_norm = pd.DataFrame({
        'screen_cut': screen_cut,
        'patt_norm': patt_norm
    })

    # Calculation of visibility

    vis = (np.max(patt_norm) - np.min(patt_norm)) / (np.max(patt_norm) + np.min(patt_norm)) 
    # The normalized pattern should be a sinusoid, so the maximum and the minimum are well defined
    
    return patt_data_proc, patt_data_norm, round(vis, 3)

def pre_process(pattern_data, slit_width, wavelen, dist_2, options, guess, A_1, A_2):

    slits_dist = pattern_data['slits_dist'][0]
    
    slits_dist = slits_dist / 10 # Convert lengths to cm
    slit_width = slit_width / 10
    wavelen = wavelen / 1e7 
    
    screen = pattern_data['screen'].to_numpy()
    pattern = pattern_data['pattern'].to_numpy()

    fig1 = px.line(pattern_data, x = 'screen', y = 'pattern')
    fig1.update_traces(line = dict(color = 'rgba(50,50,50,0.2)'))
    fig_data = fig1.data

    for i in options:
        if i == 'Extremal points':
            tolerance = 0.1 # [cm] (consider adding this as an input)
            patt_max, patt_min = calc_extremal(pattern, screen, tolerance)

            which = ['max' for l in range(len(patt_max))] + ['min' for l in range(len(patt_min))]

            maxmin_data = pd.DataFrame({
                'points': np.concatenate((screen[patt_max], screen[patt_min])),
                'maxes': np.concatenate((pattern[patt_max], pattern[patt_min])),
                'which': which
            })

            fig2 = px.scatter(maxmin_data, x = 'points', y = 'maxes', color = 'which')

            fig_data += fig2.data
        
        elif i == 'Fit guess':

            with open('numbers.txt', 'r') as f:
                avg_intensity = float(f.read())
            
            prof_up = 2 * A_1 * avg_intensity * (np.sinc((screen + slits_dist/2) * slit_width / (wavelen * dist_2)) ** 2 + np.sinc((screen - slits_dist/2) * slit_width / (wavelen * dist_2)) ** 2 + 2 * np.sinc(screen * slit_width / (wavelen * dist_2)) ** 2 * guess )
            # prof_down = 2 * A_2 * avg_intensity * (np.sinc((screen + slits_dist/2) * slit_width / (wavelen * dist_2)) ** 2 + np.sinc((screen - slits_dist/2) * slit_width / (wavelen * dist_2)) ** 2 - 2 * np.sinc(screen * slit_width / (wavelen * dist_2)) ** 2 * guess )

            guess_data = pd.DataFrame({
                'screen': screen,
                'prof_up': prof_up,
            #     'prof_down': prof_down
            })

            # fig3 = px.line(guess_data.melt(id_vars = 'screen', value_vars = ['prof_up', 'prof_down']), x = 'screen', y = 'value', line_group = 'variable', color = 'variable')
            fig3 = px.line(guess_data, x = 'screen', y = 'prof_up')
            fig_data += fig3.data

    return fig_data