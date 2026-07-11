#!/usr/bin/python3
#   Author: Juan Aznar Poveda
#   Technical University of Cartagena, GIT
#   Copyright (C) 2017
# Git repo: https://juanaznarp94@bitbucket.org/juanaznarp94/tfm.git
# -*- coding: utf-8 -*-

############################################################################################

from var import *
from settings import *
import matplotlib, sys
import time
import math
import matplotlib.pyplot as plt
matplotlib.use('TkAgg')
from numpy import arange, sin, pi
import numpy as np
from matplotlib.backends.backend_tkagg import *
from matplotlib.figure import Figure
from matplotlib import * # FOr Plotting CV and CA
from tkinter import *
from tkinter import ttk
import cmath
import pylab
from decimal import Decimal
import csv
import RPi.GPIO as GPIO
import time
import datetime
import subprocess
import os
from scipy.signal import savgol_filter
# ===== NEW IMPORTS =====
from scipy import signal
from scipy import stats
from scipy.optimize import curve_fit

GPIO.setwarnings(True)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(11, GPIO.OUT) 
GPIO.setup(13, GPIO.OUT)

root = Tk()
root.wm_title("Electrochemical Sensor Development Interface")
root.geometry('1280x800+100+100')
root.style = ttk.Style()
#('clam', 'alt', 'default', 'classic')

root.style.theme_use('clam')

GPIO.output(11,False) ## RED
GPIO.output(13,True) ## GREEN

pb = ttk.Progressbar(root, mode='determinate', maximum=300, length=100)
pb.grid(column='1',row='11',columnspan='3',rowspan='1')
pb['length']=350

w = Text(root, width='60', height='12', bg='white', relief = 'groove')
results = Text(root, width='60', height='2', bg='white', relief = 'groove')
#w.grid(column='0',row='12',columnspan='1',rowspan='1')
#results.grid(column='0',row='11',columnspan='1',rowspan='1')
w.grid(column='1',row='5',columnspan='3',rowspan='1')
results.grid(column='1',row='8',columnspan='3',rowspan='1')

w.insert('1.0', 'Welcome to Chronoamperometry Client Interface.\n Please:\n 1) Insert the SPE in the adapters plug.\n 2) Choose your fit config\n    (TIA and OPMODE).\n 3) Click Start and save graph.\n'+'\n'+'\n'+'Plaksha University'+'\n')
results.insert('1.0', 'Determined concentration results\n(uM)')


GRAPH_title = Label(root, text='Graph title')
GRAPH_title.grid(column='2',row='3',columnspan='2',rowspan='1')
k = Entry(root,width='30')
k.grid(column='2',row='4',columnspan='2',rowspan='1')

TIA_dicc = {'2.75 KOhms':TIACN_TIAG_2_75_RLOAD_010,
            '3.5 KOhms':TIACN_TIAG_3_50_RLOAD_010,
            "7 KOhms":TIACN_TIAG_7_00_RLOAD_010,
            "14 KOhms":TIACN_TIAG_14_0_RLOAD_010,
            "35 KOhms":TIACN_TIAG_35_0_RLOAD_010,
            "120 KOhms":TIACN_TIAG_120__RLOAD_010,
            "350 KOhms":TIACN_TIAG_350__RLOAD_010}

TIA_values = {'2.75 KOhms':2750,
            '3.5 KOhms':3500,
            "7 KOhms":7000,
            "14 KOhms":14000,
            "35 KOhms":35000,
            "120 KOhms":120000,
            "350 KOhms":350000}

OPMODE_dicc = {"Deep Sleep":MODECN_OP_MODE_DEEPSLEEP,
               "2-Lead GRGC":MODECN_OP_MODE_2LEADGNDC,
               "Standby":MODECN_OP_MODE_STANDBY00,
               "3-Lead AC":MODECN_OP_MODE_3LEADAMPC,
               "Temperature MT-OFF":MODECN_OP_MODE_TEMPMEAOF,
               "Temperature MT-ON":MODECN_OP_MODE_TEMPMEAON}

TITLE = Label(root, text='Cyclic Voltammetry and Chronoamperometry GIT Client Interface')
INITIALIZE = Label(root, text='INITIALIZE SWEEP')

TIA_label = Label(root,text='TIA gain')
OPMODE_label = Label(root,text='OP mode')
SUBSTANCE_label = Label(root, text='Substance')
METHOD_label = Label(root, text='Method')

# ===== NEW: Storage for multiple frequency measurements =====
frequency_measurements = {}  # Store CV data at different frequencies

############################################################################################
##  PLOT CONFIG AND SWEEP MAIN FUNCTION

f = Figure(figsize=(3,3), dpi=120, facecolor='white', frameon=False,tight_layout=True)
a = f.add_subplot(111,title= "Chronoamperometry",
                  xlabel='v, V',
                  ylabel='i,'+ u"\u00B5"+'A',autoscale_on=True)

t_fv = range(1,401)
t_cv = [-0.6,-0.55,-0.5,-0.45,-0.4,-0.35,-0.3,-0.25,-0.2,-0.15,-0.1,-0.05,-0.025,0,0.025,0.05,0.1,0.15,0.2,0.25,0.3,0.35,0.4,0.45,0.5,0.55,0.6]  #Voltage Range

data_cv = [0]*len(FULL_SWEEP)
DATA_cv = data_cv
data_fv = [0]*400
DATA_fv = data_fv


###########

def smooth(y,box_pts):
    box = np.ones(box_pts)/box_pts
    y_smooth = np.convolve(y,box,mode='same')
    return y_smooth

############

# ===== NEW: DISPLAY FFT PLOTS EMBEDDED IN TKINTER =====
def display_fft_plots_in_window(data, denoised_signal, windowed_signal, 
                                 positive_freqs, positive_magnitude, filtered_magnitude,
                                 cutoff_freq, sampling_freq):
    """
    Display FFT plots embedded in a Tkinter Toplevel window (non-blocking).
    """
    
    # Create new Toplevel window for plots
    plot_window = Toplevel(root)
    plot_window.title('FFT Denoising Analysis - Cyclic Voltammogram')
    plot_window.geometry('1600x950')
    
    # Create matplotlib figure
    fig = Figure(figsize=(16, 9.5), dpi=100)
    fig.suptitle('FFT-Based Denoising Analysis for Cyclic Voltammogram Data', 
                 fontsize=16, fontweight='bold')
    
    n = len(data)
    sample_axis = np.arange(n)
    t_cv = [-0.6,-0.55,-0.5,-0.45,-0.4,-0.35,-0.3,-0.25,-0.2,-0.15,-0.1,-0.05,-0.025,0,0.025,0.05,0.1,0.15,0.2,0.25,0.3,0.35,0.4,0.45,0.5,0.55,0.6]  #Voltage Range
    # ===== Plot 1: Original Signal =====
    ax1 = fig.add_subplot(2, 3, 1)
    ax1.plot(t_cv+t_cv[::-1], data, 'b-', linewidth=1.5)
    ax1.set_xlabel('Voltage(V)', fontsize=10)
    ax1.set_ylabel('Current (µA)', fontsize=10)
    ax1.set_title('1. Original Current Signal', fontsize=11, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    
    # ===== Plot 2: Windowed Signal =====
    ax2 = fig.add_subplot(2, 3, 2)
    ax2.plot(t_cv+t_cv[::-1], windowed_signal, 'g-', linewidth=1.5)
    ax2.set_xlabel('Voltage(V)', fontsize=10)
    ax2.set_ylabel('Current (µA)', fontsize=10)
    ax2.set_title('2. Windowed Signal (Hanning Window)', fontsize=11, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    
    # ===== Plot 3: FFT Magnitude Spectrum (Stem) =====
    ax3 = fig.add_subplot(2, 3, 3)
    markerline, stemlines, baseline = ax3.stem(positive_freqs / 1000, positive_magnitude, 
                                                basefmt=' ')
    markerline.set_markerfacecolor('red')
    markerline.set_markeredgecolor('red')
    markerline.set_markersize(4)
    stemlines.set_color('red')
    stemlines.set_linewidth(1)
    ax3.axvline(cutoff_freq / 1000, color='k', linestyle='--', linewidth=2.5, 
               label=f'Cutoff: {cutoff_freq/1000:.2f} kHz')
    ax3.set_xlabel('Frequency (kHz)', fontsize=10)
    ax3.set_ylabel('Magnitude', fontsize=10)
    ax3.set_title('3. FFT Magnitude Spectrum', fontsize=11, fontweight='bold')
    ax3.legend(fontsize=9)
    ax3.grid(True, alpha=0.3, axis='y')
    ax3.set_xlim([0, min(sampling_freq / 2 / 1000, 125)])
    
    # ===== Plot 4: Filtered FFT (Stem) =====
    ax4 = fig.add_subplot(2, 3, 4)
    print(f"Positive Frequencies = {positive_freqs}")
    print(f"Size of Positive Frequencies = {len(positive_freqs)}")
    print(f"Filtered Magnitudes = {filtered_magnitude}")
    print(f"Size of Filtered Magnitudes = {len(filtered_magnitude)}")
    markerline, stemlines, baseline = ax4.stem(positive_freqs / 1000, filtered_magnitude, 
                                                basefmt=' ')
    markerline.set_markerfacecolor('magenta')
    markerline.set_markeredgecolor('magenta')
    markerline.set_markersize(4)
    stemlines.set_color('magenta')
    stemlines.set_linewidth(1)
    ax4.axvline(cutoff_freq / 1000, color='k', linestyle='--', linewidth=2.5,
               label=f'Cutoff: {cutoff_freq/1000:.2f} kHz')
    ax4.set_xlabel('Frequency (kHz)', fontsize=10)
    ax4.set_ylabel('Magnitude', fontsize=10)
    ax4.set_title('4. Filtered FFT (Low-Pass Applied)', fontsize=11, fontweight='bold')
    ax4.legend(fontsize=9)
    ax4.grid(True, alpha=0.3, axis='y')
    ax4.set_xlim([0, min(sampling_freq / 2 / 1000, 125)])
    
    # ===== Plot 5: Denoised Signal =====
    ax5 = fig.add_subplot(2, 3, 5)
    ax5.plot(t_cv+t_cv[::-1], denoised_signal, 'c-', linewidth=1.5)
    ax5.set_xlabel('Voltage(V)', fontsize=10)
    ax5.set_ylabel('Current (µA)', fontsize=10)
    ax5.set_title('5. Denoised Signal (Inverse FFT)', fontsize=11, fontweight='bold')
    ax5.grid(True, alpha=0.3)
    
    # ===== Plot 6: Comparison =====
    ax6 = fig.add_subplot(2, 3, 6)
    ax6.plot(t_cv+t_cv[::-1], data, 'b-', linewidth=1.5, alpha=0.6, label='Original')
    ax6.plot(t_cv+t_cv[::-1], denoised_signal, 'c-', linewidth=1.5, alpha=0.8, label='Denoised')
    ax6.set_xlabel('Voltage(V)', fontsize=10)
    ax6.set_ylabel('Current (µA)', fontsize=10)
    ax6.set_title('6. Original vs Denoised Comparison', fontsize=11, fontweight='bold')
    ax6.legend(fontsize=9)
    ax6.grid(True, alpha=0.3)
    
    # Embed in Tkinter
    canvas = FigureCanvasTkAgg(fig, master=plot_window)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=BOTH, expand=True, padx=10, pady=10)
    
    return plot_window


############

# ===== NEW: FFT DENOISING FUNCTION =====
def fft_denoise(data, sampling_freq=250000, display_plots=True):
    """
    FFT-based denoising function for cyclic voltammogram data (Current vs Voltage).
    
    Parameters:
    -----------
    data : array-like
        Input signal (current values in µA from cyclic voltammogram)
    sampling_freq : float
        Sampling frequency in Hz (default: 250 kHz)
    display_plots : bool
        If True, displays plots embedded in Tkinter window
    
    Returns:
    --------
    denoised_signal : ndarray
        Denoised signal (current values)
    cutoff_freq : float
        Automatically determined cutoff frequency
    """
    
    # Convert input to numpy array
    data = np.asarray(data, dtype=float)
    segment1 = data[0:27]
    segment2 = data[27:54]
    n1 = len(segment1)
    n2 = len(segment2)
    n = len(data)
    # ============ STEP 1: Apply Hanning Window & FFT ============
    window1 = np.hanning(n1)
    window2 = np.hanning(n2)
    windowed_signal1 = segment1 * window1
    windowed_signal2 = segment2 * window2
    windowed_signal = np.concatenate((windowed_signal1,windowed_signal2))
    # Compute FFT for Segment 1 AND Segment 2
    fft_signal1 = np.fft.fft(windowed_signal1)
    fft_signal2 = np.fft.fft(windowed_signal2)
    fft_signal = np.fft.fft(windowed_signal)
    fft_magnitude1 = np.abs(fft_signal1)
    fft_magnitude2 = np.abs(fft_signal2)
    fft_magnitude = np.abs(fft_signal)
    # Frequency axis
    freq_axis1 = np.fft.fftfreq(n1, d=1/sampling_freq)
    freq_axis2 = np.fft.fftfreq(n2, d=1/sampling_freq)
    freq_axis = np.fft.fftfreq(n, d=1/sampling_freq)
    positive_frequencies_idx = freq_axis > 0
    positive_freqs = freq_axis[positive_frequencies_idx]
    positive_magnitude = fft_magnitude[positive_frequencies_idx]
    # Only keep positive frequencies for analysis of Segment 1 and Segment 2
    positive_freq_idx1 = freq_axis1 > 0
    positive_freqs1 = freq_axis1[positive_freq_idx1]
    positive_magnitude1 = fft_magnitude1[positive_freq_idx1]
    positive_freq_idx2 = freq_axis2 > 0
    positive_freqs2 = freq_axis2[positive_freq_idx2]
    positive_magnitude2 = fft_magnitude2[positive_freq_idx2]
  
    # ============ STEP 2: Automatic Cutoff Frequency Detection ============
    threshold_percentage = 0.05  # 5% of maximum magnitude
    threshold_magnitude = threshold_percentage * np.max(positive_magnitude)
    threshold_magnitude1 = threshold_percentage * np.max(positive_magnitude1)
    threshold_magnitude2 = threshold_percentage * np.max(positive_magnitude2)
    cutoff_indices = np.where(positive_magnitude < threshold_magnitude)[0]
    cutoff_indices1 = np.where(positive_magnitude1 < threshold_magnitude1)[0]
    cutoff_indices2 = np.where(positive_magnitude2 < threshold_magnitude2)[0]
    #Cutoff Frequency for full data
    if len(cutoff_indices) > 0:
        cutoff_idx = cutoff_indices[0]
    else:
        # Fallback: use 30% of Nyquist frequency
        cutoff_idx = int(len(positive_freqs) * 0.3)
    #Cutoff Frequency for Segment 1
    if len(cutoff_indices1) > 0:
        cutoff_idx1 = cutoff_indices1[0]
    else:
        # Fallback: use 30% of Nyquist frequency
        cutoff_idx1 = int(len(positive_freqs1) * 0.3)
    
    cutoff_freq1 = positive_freqs1[cutoff_idx1]
    #Cutoff Frequency for Segment 2
    if len(cutoff_indices2) > 0:
        cutoff_idx2 = cutoff_indices2[0]
    else:
        # Fallback: use 30% of Nyquist frequency
        cutoff_idx2 = int(len(positive_freqs2) * 0.3)
    
    cutoff_freq2 = positive_freqs2[cutoff_idx2]
    cutoff_freq = positive_freqs[cutoff_idx]
    # Create frequency-domain filter mask (brick-wall filter) for Segment 1
    filter_mask1 = np.ones(n1)
    filter_mask1[freq_axis1 >= cutoff_freq1] = 0
    filter_mask1[freq_axis1 <= -cutoff_freq1] = 0
    # Create frequency-domain filter mask (brick-wall filter) for Segment 2
    filter_mask2 = np.ones(n2)
    filter_mask2[freq_axis2 >= cutoff_freq2] = 0
    filter_mask2[freq_axis2 <= -cutoff_freq2] = 0
     # Create frequency-domain filter mask (brick-wall filter) for full data
    filter_mask = np.ones(n)
    filter_mask[freq_axis >= cutoff_freq] = 0
    filter_mask[freq_axis <= -cutoff_freq] = 0
    
    # ============ STEP 2 (continued): Apply Low-Pass Filter ============
    filtered_fft = fft_signal * filter_mask
    filtered_fft1 = fft_signal1 * filter_mask1
    filtered_fft2 = fft_signal2 * filter_mask2
    filtered_magnitude1 = np.abs(filtered_fft1)
    filtered_magnitude2 = np.abs(filtered_fft2)
    filtered_magnitude = np.abs(filtered_fft)
    filtered_magnitude = filtered_magnitude[0:len(positive_freqs)]
    # ============ STEP 3: Inverse FFT to Time Domain ============
    denoised_signal1 = np.fft.ifft(filtered_fft1).real
    denoised_signal2 = np.fft.ifft(filtered_fft2).real
    denoised_signal = np.concatenate((denoised_signal1,np.negative(denoised_signal2)))
    # ===== NEW: RESCALE DENOISED SIGNAL TO MATCH ORIGINAL PEAK =====
# Find peak magnitudes
    original_peak = np.max(np.abs(data))
    denoised_peak = np.max(np.abs(denoised_signal))

# Avoid division by zero
    if denoised_peak > 0:
        scaling_factor = original_peak / denoised_peak
        denoised_signal = denoised_signal * scaling_factor
    else:
        scaling_factor = 1.0

    print(f"Peak Rescaling:")
    print(f"  - Original Peak Magnitude:      {original_peak:.6f} µA")
    print(f"  - Denoised Peak (before scale): {denoised_peak:.6f} µA")
    print(f"  - Scaling Factor:               {scaling_factor:.6f}")
    print(f"  - Denoised Peak (after scale):  {np.max(np.abs(denoised_signal)):.6f} µA")
    print(f"{'='*70}\n")
    # ============ STEP 4: Display Results ============
    if display_plots:
        # Call the embedded plotting function (non-blocking)
        plot_window = display_fft_plots_in_window(
            data, denoised_signal, windowed_signal,
            positive_freqs, positive_magnitude, filtered_magnitude,
            cutoff_freq, sampling_freq
        )
    
    # ============ Print Analysis Summary ============
    nyquist_freq = sampling_freq / 2
    snr_improvement = 10 * np.log10(np.sum(data**2) / (np.sum((data - denoised_signal)**2) + 1e-10))
    
    print(f"\n{'='*70}")
    print(f"{'FFT DENOISING ANALYSIS SUMMARY - CYCLIC VOLTAMMOGRAM':^70}")
    print(f"{'='*70}")
    print(f"Number of Samples:                {n} samples")
    print(f"Sampling Frequency (ADC):         {sampling_freq / 1000:.1f} kHz")
    print(f"Nyquist Frequency:                {nyquist_freq / 1000:.1f} kHz")
    print(f"Determined Cutoff Frequency:      {cutoff_freq / 1000:.3f} kHz")
    print(f"Cutoff as % of Nyquist:           {(cutoff_freq / nyquist_freq) * 100:.2f}%")
    print(f"\nOriginal Current Signal Statistics:")
    print(f"  - Maximum Current:              {np.max(np.abs(data)):.6f} µA")
    print(f"  - Minimum Current:              {np.min(data):.6f} µA")
    print(f"  - Mean Current:                 {np.mean(data):.6f} µA")
    print(f"  - Std Dev (Noise):              {np.std(data):.6f} µA")
    print(f"\nDenoised Current Signal Statistics:")
    print(f"  - Maximum Current:              {np.max(np.abs(denoised_signal)):.6f} µA")
    print(f"  - Minimum Current:              {np.min(denoised_signal):.6f} µA")
    print(f"  - Mean Current:                 {np.mean(denoised_signal):.6f} µA")
    print(f"  - Std Dev (Noise):              {np.std(denoised_signal):.6f} µA")
    print(f"\nSignal Quality Improvement:")
    print(f"  - SNR Improvement:              {snr_improvement:.2f} dB")
    print(f"  - Energy Retained:              {(np.sum(denoised_signal**2) / np.sum(data**2)) * 100:.2f}%")
    print(f"  - Noise Reduction:              {((np.std(data) - np.std(denoised_signal)) / np.std(data)) * 100:.2f}%")
    print(f"{'='*70}\n")
    
    return denoised_signal, cutoff_freq

############

# ===== NEW: PEAK-TO-RMS CALCULATION FUNCTION =====
def calculate_peak_to_rms(data, window_size=None):
    """
    Calculate the Peak-to-RMS current ratio for a single measurement.
    
    Parameters:
    -----------
    data : array-like
        Current values (µA) from cyclic voltammogram
    window_size : int, optional
        Size of analysis window around peak. If None, uses entire data.
    
    Returns:
    --------
    peak_to_rms_ratio : float
        Ratio of peak current to RMS current
    i_peak : float
        Maximum current value
    i_rms : float
        RMS current value
    """
    
    data = np.asarray(data, dtype=float)
    
    if window_size is not None and len(data) > window_size:
        # Find peak location
        peak_idx = np.argmax(np.abs(data))
        # Center window around peak
        start_idx = max(0, peak_idx - window_size // 2)
        end_idx = min(len(data), start_idx + window_size)
        
        if end_idx - start_idx < window_size:
            start_idx = max(0, end_idx - window_size)
        
        analysis_window = data[start_idx:end_idx]
    else:
        analysis_window = data
    
    # Calculate peak current (absolute maximum)
    i_peak = np.max(np.abs(analysis_window))
    
    # Calculate RMS current
    i_rms = np.sqrt(np.mean(analysis_window ** 2))
    
    # Avoid division by zero
    if i_rms == 0:
        i_rms = 1e-10
    
    # Peak-to-RMS ratio
    peak_to_rms_ratio = i_peak / i_rms
    
    return peak_to_rms_ratio, i_peak, i_rms


############

# ===== NEW: DISPLAY FREQUENCY DEGRADATION PLOTS EMBEDDED IN TKINTER =====
def display_degradation_plots_in_window(frequencies, peak_to_rms_ratios, peak_currents, 
                                        rms_currents, freq_smooth, fitted_curve, 
                                        fit_quality):
    """
    Display frequency degradation plots embedded in a Tkinter Toplevel window.
    """
    
    # Create new Toplevel window
    plot_window = Toplevel(root)
    plot_window.title('Frequency Degradation Analysis')
    plot_window.geometry('1400x900')
    
    # Create matplotlib figure
    fig = Figure(figsize=(14, 9), dpi=100)
    fig.suptitle('Peak-to-RMS Current Ratio Analysis: Frequency Degradation', 
                 fontsize=14, fontweight='bold')
    
    # Plot 1: Peak-to-RMS Ratio vs Frequency (Linear Scale)
    ax1 = fig.add_subplot(2, 2, 1)
    ax1.plot(frequencies / 1000, peak_to_rms_ratios, 'bo-', linewidth=2, 
            markersize=8, label='Measured Data')
    if fitted_curve is not None:
        ax1.plot(freq_smooth / 1000, fitted_curve, 'r-', linewidth=2.5, 
                label=f'Fit (R² = {fit_quality:.4f})')
        ax1.legend(fontsize=10)
    ax1.set_xlabel('Frequency (kHz)', fontsize=11)
    ax1.set_ylabel('Peak-to-RMS Current Ratio', fontsize=11)
    ax1.set_title('1. Linear Frequency Scale', fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Peak-to-RMS Ratio vs Frequency (Log Scale)
    ax2 = fig.add_subplot(2, 2, 2)
    ax2.semilogx(frequencies / 1000, peak_to_rms_ratios, 'bo-', linewidth=2, 
                markersize=8, label='Measured Data')
    if fitted_curve is not None:
        ax2.semilogx(freq_smooth / 1000, fitted_curve, 'r-', linewidth=2.5, 
                    label=f'Inverse Log Fit (R² = {fit_quality:.4f})')
        ax2.legend(fontsize=10)
    ax2.set_xlabel('Frequency (kHz)', fontsize=11)
    ax2.set_ylabel('Peak-to-RMS Current Ratio', fontsize=11)
    ax2.set_title('2. Log Frequency Scale (Decay Visualization)', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3, which='both')
    
    # Plot 3: Peak Current vs Frequency
    ax3 = fig.add_subplot(2, 2, 3)
    ax3.semilogx(frequencies / 1000, peak_currents, 'g^-', linewidth=2, 
                markersize=8, label='Peak Current')
    ax3.set_xlabel('Frequency (kHz)', fontsize=11)
    ax3.set_ylabel('Peak Current (µA)', fontsize=11)
    ax3.set_title('3. Peak Current Degradation with Frequency', fontsize=12, fontweight='bold')
    ax3.grid(True, alpha=0.3, which='both')
    ax3.legend(fontsize=10)
    
    # Plot 4: RMS Current vs Frequency
    ax4 = fig.add_subplot(2, 2, 4)
    ax4.semilogx(frequencies / 1000, rms_currents, 'ms-', linewidth=2, 
                markersize=8, label='RMS Current')
    ax4.set_xlabel('Frequency (kHz)', fontsize=11)
    ax4.set_ylabel('RMS Current (µA)', fontsize=11)
    ax4.set_title('4. RMS Current (Noise) vs Frequency', fontsize=12, fontweight='bold')
    ax4.grid(True, alpha=0.3, which='both')
    ax4.legend(fontsize=10)
    
    # Embed in Tkinter
    canvas = FigureCanvasTkAgg(fig, master=plot_window)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=BOTH, expand=True, padx=10, pady=10)
    
    return plot_window


############

# ===== NEW: FREQUENCY DEGRADATION ANALYSIS FUNCTION =====
def analyze_frequency_degradation(frequencies, cv_data_list, window_size=None, plot=True):
    """
    Analyze peak-to-RMS ratio degradation across different measurement frequencies.
    Includes inverse logarithmic curve fitting.
    
    Parameters:
    -----------
    frequencies : array-like
        List of frequencies (Hz) at which CV measurements were taken
    cv_data_list : list of arrays
        List of current data arrays corresponding to each frequency
    window_size : int, optional
        Analysis window size (samples around peak)
    plot : bool
        If True, generates degradation curve plots
    
    Returns:
    --------
    results : dict
        Dictionary containing analysis results
    """
    
    frequencies = np.asarray(frequencies)
    peak_to_rms_ratios = []
    peak_currents = []
    rms_currents = []
    
    # Calculate ratios for each frequency
    for i, cv_data in enumerate(cv_data_list):
        ratio, i_peak, i_rms = calculate_peak_to_rms(cv_data, window_size)
        peak_to_rms_ratios.append(ratio)
        peak_currents.append(i_peak)
        rms_currents.append(i_rms)
    
    peak_to_rms_ratios = np.asarray(peak_to_rms_ratios)
    peak_currents = np.asarray(peak_currents)
    rms_currents = np.asarray(rms_currents)
    
    # ============ Inverse Logarithmic Curve Fitting ============
    def inverse_log_function(x, a, b):
        """Inverse logarithmic function: y = a + b*ln(x)"""
        return a + b * np.log(x)
    
    try:
        # Initial guess for parameters
        p0 = [np.max(peak_to_rms_ratios), -1]
        
        # Curve fitting
        popt, pcov = curve_fit(inverse_log_function, frequencies, peak_to_rms_ratios, 
                               p0=p0, maxfev=10000)
        
        # Calculate fitted curve
        freq_smooth = np.logspace(np.log10(np.min(frequencies)), 
                                  np.log10(np.max(frequencies)), 100)
        fitted_curve = inverse_log_function(freq_smooth, *popt)
        
        # Calculate R² (coefficient of determination)
        ss_res = np.sum((peak_to_rms_ratios - inverse_log_function(frequencies, *popt)) ** 2)
        ss_tot = np.sum((peak_to_rms_ratios - np.mean(peak_to_rms_ratios)) ** 2)
        r_squared = 1 - (ss_res / ss_tot)
        
        fit_params = popt
        fit_quality = r_squared
        fit_equation = f"Peak-to-RMS = {popt[0]:.4f} + {popt[1]:.4f} × ln(f)"
        
    except Exception as e:
        print(f"Curve fitting error: {e}")
        fit_params = None
        fit_quality = None
        fit_equation = "Fitting failed"
        freq_smooth = None
        fitted_curve = None
    
    # ============ Generate Plots (Embedded in Tkinter) ============
    if plot:
        plot_window = display_degradation_plots_in_window(
            frequencies, peak_to_rms_ratios, peak_currents, rms_currents,
            freq_smooth, fitted_curve, fit_quality
        )
    
    # ============ Print Summary Statistics ============
    print(f"\n{'='*80}")
    print(f"{'PEAK-TO-RMS CURRENT RATIO ANALYSIS SUMMARY':^80}")
    print(f"{'='*80}")
    print(f"\n{'Frequency (kHz)':>15} {'Peak (µA)':>15} {'RMS (µA)':>15} {'Peak/RMS Ratio':>15}")
    print(f"{'-'*80}")
    
    for i, freq in enumerate(frequencies):
        print(f"{freq/1000:>15.3f} {peak_currents[i]:>15.6f} {rms_currents[i]:>15.6f} {peak_to_rms_ratios[i]:>15.4f}")
    
    print(f"{'-'*80}")
    print(f"\nStatistical Summary:")
    print(f"  - Max Peak-to-RMS Ratio:        {np.max(peak_to_rms_ratios):.4f}")
    print(f"  - Min Peak-to-RMS Ratio:        {np.min(peak_to_rms_ratios):.4f}")
    print(f"  - Mean Peak-to-RMS Ratio:       {np.mean(peak_to_rms_ratios):.4f}")
    print(f"  - Ratio Degradation:            {((np.max(peak_to_rms_ratios) - np.min(peak_to_rms_ratios)) / np.max(peak_to_rms_ratios) * 100):.2f}%")
    
    if fit_params is not None:
        print(f"\nCurve Fitting Results (Inverse Logarithmic):")
        print(f"  - Equation:                     {fit_equation}")
        print(f"  - Parameter a:                  {fit_params[0]:.6f}")
        print(f"  - Parameter b:                  {fit_params[1]:.6f}")
        print(f"  - R² (Goodness of Fit):         {fit_quality:.6f}")
        print(f"\n  Interpretation:")
        print(f"  - Peak sharpness decreases logarithmically with frequency")
        print(f"  - Negative b coefficient indicates expected decay")
        print(f"  - Reflects: increased capacitive interference & kinetic suppression")
    
    print(f"{'='*80}\n")
    
    # Return results dictionary
    results = {
        'frequencies': frequencies,
        'peak_to_rms_ratios': peak_to_rms_ratios,
        'peak_currents': peak_currents,
        'rms_currents': rms_currents,
        'fit_params': fit_params,
        'fit_quality': fit_quality,
        'fit_equation': fit_equation
    }
    
    return results

############

a.plot(t_cv+t_cv[::-1],data_cv,'darkblue')
a.grid(True,linestyle='--')
#a.plot(t_fv,smooth(data,4),'darkblue')
dataPlot = FigureCanvasTkAgg(f, master=root)
dataPlot.draw()
dataPlot.get_tk_widget().grid(column='5',row='3', columnspan='2', rowspan='10')
#dataPlot.get_tk_widget().grid(column='4',row='4', columnspan='1', rowspan='10')
def on_change(k,method):
   if method=="Cyclic Voltammetry":
        f = Figure(figsize=(3,3), dpi=120, facecolor='white', frameon=False,tight_layout=True)
        a = f.add_subplot(111,title="Cyclic Voltammetry",
        xlabel='v, V',
        ylabel='i,'+ u"\u00B5"+'A',autoscale_on=True)
   if method == "Fixed Voltage":
        f = Figure(figsize=(3,3), dpi=120, facecolor='white', frameon=False,tight_layout=True)
        a = f.add_subplot(111,title="ChronoAmperometry",
        xlabel='t, s',
        ylabel='i,'+ u"\u00B5"+'A',autoscale_on=True)

def update(data, method):
    if method=="Cyclic Voltammetry":
        a.cla()
        a.grid(True)
        a.set_xlabel('v, V')
        a.set_ylabel('i, '+ u"\u00B5"+'A')
        a.set_title(k.get())
        print(f"X axis={t_cv}")
        print(f"Y axis={data[0:27]}")
        line1=a.plot(t_cv,data[0:27],'darkblue')
        line2=a.plot(t_cv[::-1],data[27:54],'darkred')
        a.legend([line1,line2],['Forward Scan','Reverse Scan'])
        dataPlot.draw()
    if method == "Fixed Voltage":
        a.cla()
        a.grid(True)
        a.set_xlabel('t, s')
        a.set_ylabel('i, '+ u"\u00B5"+'A')
        a.set_title(k.get())
        a.plot(t_fv,smooth(data,64),'darkblue')
        #a.axvspan(int(int1.get()),int(int2.get()), facecolor='#1f77b4', alpha=0.15)
        #a.axvspan(int(int3.get()),299, facecolor='#1f77b4', alpha=0.15)
        dataPlot.draw()
        

def printdout(num):
    TIAG = TIA_values["{}".format(variable_TIA.get())] #Optimized TIA Gain = 14 kilo Ohm
    value = readadc()
    vref = 2.5
    vmax = 5
    N = 16
    binmax = ((2**N)-1)
    volts = (vref/2)+(vmax-(vref/2))*(value)/(binmax)
    current = 571.59 + ((volts-(vref/2))/(TIAG))*1000000
    #print( ">> Step: %5.3f\n >> Voltage: %5.3f V\m >> Current: %5.3f uA" %(num,volts,current))
    return [current,">> Step: %5.3f\n >> Voltage: %5.3f V\m >> Current: %5.3f uA" %(num,volts,current)]
    
def sweep(TIA,OPMODE):
    #SWEEP_1 (-0.6 to 0.6, 50mV/s)
    #init(LOCK,TIACN,REFCNinit,MODECN)
    #step(REFCN)
    init(LOCKWR,\
        TIA,\
        REFCN_BIAS_N[0],\
        OPMODE)
    #BOTTOMUP:
    ##TIME CONTROL
    #start_time = time.time()
    #print("--- %s seconds ---" % (time.time() - start_time))

    pb['maximum']=300
    pval = 0
    time.sleep(20) #Warm up Time
    if ("{}".format(variable_METHOD.get())=="Cyclic Voltammetry"):
        for p in range(len(FULL_SWEEP)):
            
            step(FULL_SWEEP[p]) #ADC measurement
            aux = printdout(p)
            #current[i]=aux[0]
            #current = np.round_(current,decimals=1)
            #result = stats.mode(current,keepdims=True)
            #mode_current = result.mode[0]
            #print(f"Mode={mode_current}")
            DATA_cv[p] = aux[0]
            pval = pval + 12 # Update Progress Bar
            pb['value']=pval
            pb.update_idletasks()
           # w.insert('1.0', string +'\n'+'\n')
            method = "{}".format(variable_METHOD.get())
            update(DATA_cv, method) # Update Graph
            time.sleep(1) #sleep
          
          
        DATA = DATA_cv
  
            
    elif ("{}".format(variable_METHOD.get())=="Fixed Voltage"):
        #Reference Voltage = VREF = 2.5Vdatasheet)
        for p in range(400):
            #Negative Bias Potentials
            step(REFCN_BIAS_N[0]) #0% of VREF = 0
            #step(REFCN_BIAS_N[1]) #1% of VREF = -0.025
            #step(REFCN_BIAS_N[2]) #2% of VREF = -0.05
            #step(REFCN_BIAS_N[3]) #4% of VREF = -0.1
            #step(REFCN_BIAS_N[4]) #6% of VREF = -0.15
              #step(REFCN_BIAS_N[5]) #8% of VREF = -0.2
            #step(REFCN_BIAS_N[6])#10% of VREF = -0.25
            #step(REFCN_BIAS_N[7]) #12% of VREF = -0.3
            #step(REFCN_BIAS_N[8])  #14% of VREF = -0.35
              #step(REFCN_BIAS_N[9]) #16% of VREF = -0.4
            #step(REFCN_BIAS_N[10])#18% of VREF = -0.45
            #step(REFCN_BIAS_N[11]) #20% of VREF = -0.5
            #step(REFCN_BIAS_N[12])   #22% of VREF = -0.55
            #step(REFCN_BIAS_N[13])   #24% of VREF = -0.6
            #Positve Bias Potentials
             #step(REFCN_BIAS_P[0]) #0% of VREF = 0
            #step(REFCN_BIAS_P[1]) #1% of VREF = +0.025
            #step(REFCN_BIAS_P[2]) #2% of VREF = +0.05
            #step(REFCN_BIAS_P[3]) #4% of VREF = +0.1
            #step(REFCN_BIAS_P[4]) #6% of VREF = +0.15
              #step(REFCN_BIAS_P[5]) #8% of VREF = 0.2
            #step(REFCN_BIAS_P[6])#10% of VREF = +0.25
            #step(REFCN_BIAS_P[7]) #12% of VREF = +0.3
            #step(REFCN_BIAS_P[8])  #14% of VREF = +0.35
              #step(REFCN_BIAS_P[9]) #16% of VREF = +0.4
            #step(REFCN_BIAS_P[10])#18% of VREF = +0.45
            #step(REFCN_BIAS_P[11]) #20% of VREF = +0.5
            #step(REFCN_BIAS_P[12])   #22% of VREF = +0.55
            #step(REFCN_BIAS_P[13])   #24% of VREF = +0.6
            aux = printdout(p)
            DATA_fv[p] = aux[0]
            #string = aux[1]
            pval = pval + 1
            pb['value']=pval
            pb.update_idletasks()
            #w.insert('1.0', string +'\n'+'\n')
            method = "{}".format(variable_METHOD.get())
            update(DATA_fv, method)
            time.sleep(1)
        DATA = DATA_fv
    else:
        w.insert('1.0', 'Choose a right method' +'\n'+'\n')

    pb.stop()
    init(LOCKRO,\
        TIACN_TIAG_350__RLOAD_010,\
        REFCN_BIAS_N[0],\
        MODECN_OP_MODE_DEEPSLEEP)
    return DATA

############################################################################################
##  TEXT and BUTTONS

def startCV():
    GPIO.output(11,True) ## RED
    GPIO.output(13,False) ## GREEN
    #Capturing Measurement Times
    method = "{}".format(variable_METHOD.get())
    
    if method == 'Fixed Voltage':
        current_time= datetime.datetime.now().strftime(f"%H:%M:%S %d-%m-%y")    
        k.insert(0,f"ChronoAmperometry Measurement at {current_time}")
    if method == 'Cyclic Voltammetry':
        current_time= datetime.datetime.now().strftime(f"%H:%M:%S %d-%m-%y")    
        k.insert(0,f"Cyclic Voltammetry Measurement at {current_time}")
    on_change(k,method)
    w.insert('1.0', ">> Transimpedance value selected: {}".format(variable_TIA.get())+'\n'+'\n')
    w.insert('1.0', ">> Operation mode selected: {}".format(variable_OPMODE.get())+'\n'+'\n')
    w.insert('1.0', ">> Starting sweep..."+'\n'+'\n')
    print(">> Transimpedance value selected: {}".format(variable_TIA.get())) 
    print( ">> Operation mode selected: {}".format(variable_OPMODE.get()))
    print (f">> Starting {method}.")
    TIA = TIA_dicc["{}".format(variable_TIA.get())]
    OPMODE = OPMODE_dicc["{}".format(variable_OPMODE.get())]
    SUBSTANCE = "{}".format(variable_SUBSTANCE.get())
    DATA = sweep(TIA,OPMODE)
    
    # ===== NEW: OPTIONAL - DENOISE DATA AFTER COLLECTION =====
    # Uncomment the following 3 lines to enable FFT denoising
    denoised_data, cutoff_freq = fft_denoise(DATA, sampling_freq=250000, display_plots=True)
    DATA = denoised_data
    w.insert('1.0', f">> Data denoised. Cutoff frequency: {cutoff_freq/1000:.3f} kHz\n\n")
    
    # ===== NEW: OPTIONAL - CALCULATE PEAK-TO-RMS FOR SINGLE MEASUREMENT =====
    # Uncomment to analyze single measurement
    peak_to_rms_ratio, i_peak, i_rms = calculate_peak_to_rms(DATA, window_size=None)
    w.insert('1.0', f">> Peak-to-RMS Ratio: {peak_to_rms_ratio:.4f}\n")
    w.insert('1.0', f">> Peak Current: {i_peak:.6f} µA\n")
    w.insert('1.0', f">> RMS Current: {i_rms:.6f} µA\n\n")
    
    #method = "{}".format(variable_METHOD.get())
    #update(DATA, method)

    file_csv = "/home/plaksha/Results/LMP91000 Sensor BlindTesting/"+k.get()+".csv" #Chronoamperometry
    file_csv_1 = "/home/plaksha/Results/LMP91000 Sensor BlindTesting/"+k.get()+"Forward Scan"+".csv" #CV FOrward Scan
    file_csv_2 = "/home/plaksha/Results/LMP91000 Sensor BlindTesting/"+k.get()+"Reverse Scan"+".csv" #CV Reverse Scan
    if ("{}".format(variable_METHOD.get())=="Cyclic Voltammetry"):
           # .CSV CREATION
           #Forward Scan
        peak_Anodic_Current = max(DATA[0:len(t_cv)])
        print(f"Peak Anodic Current(uA) =  {peak_Anodic_Current}"+'\n'+'\n') 
        w.insert('1.0',f"Peak Anodic Current(uA) = {peak_Anodic_Current}"+'\n'+'\n')
        with open(file_csv_1,'w',newline='') as csv_out:
            mywriter = csv.writer(csv_out)
            for row in zip(t_cv, DATA[0:len(t_cv)]):
                mywriter.writerow(row)
        csv_out.close()
        w.insert('1.0', f"Data exported to {file_csv_1} succesfully!"+'\n'+'\n')
           #Reverse Scan
        peak_Cathodic_Current = max(DATA[len(t_cv):],key=abs)
        print(f"Peak Cathodic Current(uA) = {peak_Cathodic_Current}"+'\n'+'\n') 
        w.insert('1.0',f"Peak Cathodic Current(uA) = {peak_Cathodic_Current}"+'\n'+'\n')
        with open(file_csv_2,'w',newline='') as csv_out:
            mywriter = csv.writer(csv_out)
            for row in zip(t_cv, DATA[len(t_cv):]):
                mywriter.writerow(row)
        csv_out.close()
        w.insert('1.0', f"Data exported to {file_csv_2} succesfully!"+'\n'+'\n')
    
    elif ("{}".format(variable_METHOD.get())=="Fixed Voltage"):
        max_current_val = max(DATA[50:350]) #Remove Padding Error At the Edges 
        print(f"Max current value (uA): {max_current_val}"+'\n')
        w.insert('1.0',f"Max current value (uA): {max_current_val}"+'\n')
        # .CSV CREATION
        
        with open(file_csv,'w',newline='') as csv_out:
            mywriter = csv.writer(csv_out)
            for row in zip(t_fv, DATA):
                mywriter.writerow(row)
        csv_out.close()
        
        w.insert('1.0', f"Data exported to {file_csv} succesfully!"+'\n'+'\n')
        try:
            with open("/home/plaksha/touchscreen_app/current.txt", "w") as f_current:
                f_current.write(f"{ max_current_val:.8f}\n") 
                w.insert('1.0', "Steady-state current saved to current.txt\n\n")
                print("Steady-state current saved to current.txt")
        except Exception as e:
                w.insert('1.0', f"Error saving steady-state current to current.txt: {e}\n\n")
                print(f"Error saving steady-state current to current.txt: {e}")
    #Lock registers
    write(1,1)
    GPIO.output(11,False) ## RED
    GPIO.output(13,True) ## GREEN

   
    
    #Calibration curves of available substances
    ##############################################
    #Copy this paragraph to add another substance
    #Calibration curve must have logarithmic axis
    if (SUBSTANCE=='Ascorbic Acid'):
            ########## DATA TO FILL ############
            W = 176.12 #Molecular weight (g/mol)
            m = 0.9033 #Slope of CC
            b = 4.1644 #Offset of CC
            V = 1
            ####################################
            log_current = math.log10(max_current_val)
            log_M = (log_current-b)/m
            M = math.pow(10,log_M)
            mg = (V*W*M)/1000
            print (">> AA (M): %5.5f\n >> AA (mg): %5.5f" %(M,mg))
            results.insert('1.0', ">> AA (M): %5.5f  \n >> AA (mg): %5.5f " %(M,mg))

    ##############################################
    if (variable_SUBSTANCE.get()=='Progesterone'):
            current = max(DATA)
            ########## DATA TO FILL ############
            W = 176.12 #Molecular weight (g/mol)
            m = 0.9033 #Slope of CC
            b = 4.1644 #Offset of CC
            V = 1
            ####################################
            log_current = math.log10(max_current_val)
            log_M = (log_current-b)/m
            M = math.pow(10,log_M)
            mg = (V*W*M)/1000
            print( ">> AA (M): %5.5f\n >> AA (mg): %5.5f" %(M,mg))
            results.insert('1.0', ">> AA (M): %5.5f  \n >> AA (mg): %5.5f " %(M,mg))

    ##############################################
    if (variable_SUBSTANCE.get()=='Catechol'):
            ########## DATA TO FILL ############
            W = 110.1 #Molecular weight (g/mol)
            m =  0.1499#Slope of CC
            b = -0.4881 #Offset of CC
            ####################################
            if ("{}".format(variable_METHOD.get())=="Fixed Voltage"):
                Concentration = (max_current_val-b)/m
                print(f"Catechol Concentration(uM) = {Concentration} "+'\n'+'\n')
                results.insert('1.0', f"Catechol Concentration(uM) = {Concentration} "+'\n'+'\n')
            elif ("{}".format(variable_METHOD.get())=="Cyclic Voltammetry"):
                Concentration = (max(peak_Cathodic_Current,peak_Anodic_Current)-b)/m
                print(f"Catechol Concentration(uM) = {Concentration} "+'\n'+'\n')
                results.insert('1.0', f"Catechol Concentration(uM) = {Concentration} \n")
    ##############################################

def clearCV():
    a.cla()
    a.set_xlabel('Applied voltage (V)')
    a.set_ylabel('Registered current ('+ u"\u00B5"+'A)')
    a.set_title(k.get())
    data = [0]*20
    t = [0]*20
    a.plot(t,data,'darkblue')
    dataPlot.draw()
    init(LOCKRO,\
        TIACN_TIAG_350__RLOAD_010,\
        REFCN_BIAS_N[0],\
        MODECN_OP_MODE_DEEPSLEEP)
    ## w.insert('1.0', "Graph removed succesfully!"+'\n'+'\n')
    k.delete(0 ,'end')
    print('Graph removed succesfully!')
    data_cv = [0]*len(FULL_SWEEP)
    DATA_cv = data_cv
    data_fv = [0]*400
    DATA_fv = data_fv

    return 0

def saveCV():
    file_eps =  "/home/plaksha/Results/LMP91000 Sensor BlindTesting/"+k.get()+".eps"
    f.savefig(file_eps, dpi=1000, facecolor='w', edgecolor='w',
              orientation='landscape', format='eps',
              transparent=False, bbox_inches=None, pad_inches=0.1
              )
    w.insert('1.0', f"Graph saved succesfully to {file_eps}!"+'\n'+'\n')
    k.delete(0 ,'end')

# ===== NEW: MENU COMMAND TO ANALYZE FREQUENCY DEGRADATION =====
def analyzeFrequencyDegradation():
    """
    This function should be called when you have multiple CV measurements at different frequencies.
    Example usage: After collecting measurements at 50, 100, 150, 200, 250 kHz
    """
    global frequency_measurements
    
    if len(frequency_measurements) < 2:
        w.insert('1.0', ">> Error: Need at least 2 frequency measurements for degradation analysis\n\n")
        return
    
    # Extract frequencies and data
    frequencies = np.array(sorted(frequency_measurements.keys()))
    cv_data_list = [frequency_measurements[freq] for freq in frequencies]
    
    # Run analysis
    results = analyze_frequency_degradation(frequencies, cv_data_list, 
                                           window_size=None, plot=True)
    
    w.insert('1.0', f">> Frequency degradation analysis completed!\n\n")
    
    # Save results to file
    try:
        results_file = "/home/plaksha/Results/LMP91000 Sensor BlindTesting/frequency_degradation_analysis.txt"
        with open(results_file, 'w') as f:
            f.write(f"FREQUENCY DEGRADATION ANALYSIS RESULTS\n")
            f.write(f"{'='*80}\n\n")
            for i, freq in enumerate(frequencies):
                f.write(f"Frequency: {freq/1000:.1f} kHz\n")
                f.write(f"  Peak Current: {results['peak_currents'][i]:.6f} µA\n")
                f.write(f"  RMS Current: {results['rms_currents'][i]:.6f} µA\n")
                f.write(f"  Peak-to-RMS Ratio: {results['peak_to_rms_ratios'][i]:.4f}\n\n")
            
            if results['fit_params'] is not None:
                f.write(f"\nFit Equation: {results['fit_equation']}\n")
                f.write(f"R² = {results['fit_quality']:.6f}\n")
        
        w.insert('1.0', f">> Results saved to {results_file}\n\n")
    except Exception as e:
        w.insert('1.0', f">> Error saving results: {e}\n\n")

def closeCV():
    init(LOCKRO,\
        TIACN_TIAG_350__RLOAD_010,\
        REFCN_BIAS_N[0],\
        MODECN_OP_MODE_DEEPSLEEP)
    print('Bye!')
    GPIO.output(13,False) ## GREEN
    root.destroy()
    return 0

############################################################################################
##  MAIN MENU

menubar = Menu(root)
menubar.add_command(label="Start", command=startCV)
menubar.add_command(label="Clear",command=clearCV)
menubar.add_command(label="Save high resolution graph", command=saveCV)
# ===== NEW: ADD ANALYSIS MENU COMMAND =====
menubar.add_command(label="Analyze Frequency Degradation", command=analyzeFrequencyDegradation)
menubar.add_command(label="Close", command=closeCV)

############################################################################################
##  OPTIONS MENU
variable_TIA = StringVar(root)
variable_TIA.set("14 KOhms") 
variable_OPMODE = StringVar(root)
variable_OPMODE.set("3-Lead AC") 
variable_SUBSTANCE = StringVar(root)
variable_SUBSTANCE.set("Catechol") 
variable_METHOD = StringVar(root)
variable_METHOD.set("Cyclic Voltammetry")


SUBSTANCE = OptionMenu(root, variable_SUBSTANCE, "None", "Ascorbic Acid", "Progesterone","Catechol")
METHOD = OptionMenu(root, variable_METHOD, "None", "Cyclic Voltammetry", "Fixed Voltage")

TIA = OptionMenu(root, variable_TIA, "Default", "2.75 KOhms",
                 "3.5 KOhms", "7 KOhms", "14 KOhms",
                 "35 KOhms", "120 KOhms", "350 KOhms")
OPMODE = OptionMenu(root, variable_OPMODE, "Deep Sleep", "2-Lead GRGC",
                 "Standby", "3-Lead AC", "Temperature MT-OFF", "Temperature MT-ON")

def option_changed_SUBSTANCE(*args):
    print ("Substance selected: {}".format(variable_SUBSTANCE.get()))
    w.insert('1.0', ">> Substance selected: {}".format(variable_SUBSTANCE.get())+'\n'+'\n')

def option_changed_TIA(*args):
    print ("Transimpedance value selected: {}".format(variable_TIA.get()))
    w.insert('1.0', ">> TIA value selected: {}".format(variable_TIA.get())+'\n'+'\n')
           
def option_changed_OPMODE(*args):
    print ("Operation mode selected: {}".format(variable_OPMODE.get()))
    w.insert('1.0', ">> Operation mode selected: {}".format(variable_OPMODE.get())+'\n'+'\n')

def option_changed_METHOD(*args):
    print ("Method selected: {}".format(variable_METHOD.get()))
    w.insert('1.0', ">> Method selected: {}".format(variable_METHOD.get())+'\n'+'\n')

variable_TIA.trace("w", option_changed_TIA)
variable_OPMODE.trace("w", option_changed_OPMODE)
variable_SUBSTANCE.trace("w", option_changed_SUBSTANCE)
variable_METHOD.trace("w", option_changed_METHOD)


############################################################################################
##  GRID CONFIG

root.grid_columnconfigure(0, minsize=60)

root.grid_columnconfigure(1, minsize=100)
root.grid_columnconfigure(2, minsize=100)
root.grid_columnconfigure(3, minsize=100)
root.grid_columnconfigure(4, minsize=60)

##root.grid_rowconfigure(2, minsize=100)

TITLE.grid(column='1',row='0',columnspan='3',rowspan='1')

SUBSTANCE_label.grid(column='1',row='1',columnspan='1',rowspan='1')
SUBSTANCE.grid(column='1',row='2',columnspan='1',rowspan='1')

METHOD_label.grid(column='2',row='1',columnspan='1',rowspan='1')
METHOD.grid(column='2',row='2',columnspan='1',rowspan='1')

TIA_label.grid(column='3',row='1',columnspan='1',rowspan='1')
TIA.grid(column='3',row='2',columnspan='1',rowspan='1')

OPMODE_label.grid(column='1',row='3',columnspan='1',rowspan='1')
OPMODE.grid(column='1',row='4',columnspan='1',rowspan='1')

LOGO = PhotoImage(file='/home/plaksha/touchscreen_app/Plakshalogo-removebg-preview.png')
LOGO = LOGO.subsample(3,3)
Label(root, image=LOGO).grid(column='0',row='0',columnspan='1',rowspan='1')

#GRAPH.grid(column='2',row='2', columnspan='2', rowspan='7')
root.config(menu=menubar)
root.mainloop()
