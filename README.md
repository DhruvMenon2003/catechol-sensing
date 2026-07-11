# Industrial Catechol Detection System - Comprehensive Documentation

## Project Overview

This is an **Industrial Treated Wastewater Quality Monitoring System** for catechol detection using electrochemical sensors. The system is designed to run on a **Raspberry Pi 3B+** microprocessor and uses **LMP91000 Current Sensor** transimpedance amplifiers (TIA) with cyclic voltammetry and chronoamperometry methods and **integrated piecewise linear calibration function(optional)** for accurate detection.

---

## Table of Contents
1.  [How to Use?](#how-to)
2. [System Architecture](#system-architecture)
3. [Hardware Configuration](#hardware-configuration)
4. [File Structure](#file-structure)
5. [Main Application Files](#main-application-files)
6. [Calibration Methodology](#calibration-methodology)
7. [Function Documentation](#function-documentation)
8. [Voltage Calculation & Bounds Explanation](#voltage-calculation--bounds-explanation)
9. [Measurement Methods](#measurement-methods)
10. [Data Processing Pipeline](#data-processing-pipeline)

---
## How to Use
**Modern Interface**: Double-click the app icon on the home screen to launch the modern CustomTkinter-based interface.
**For Development**:
- Open Documents Folder and launch Python3
- Code for the Prototype Development Interface and App is located within this directory
- **Do not move files out of directory**
- Make modifications without changing file names

## System Architecture
**Workflow Steps**:
1. Welcome page with system information
2. Sample insertion verification
3. pH buffer configuration (ABS+PBS, target pH 6.5)
4. Real-time calibration monitoring with safety assessment
5. Automated concentration calculation and risk classification
### Overview
```
Electrochemical Sensor (LMP91000)
    ↓
ADC (16-bit) → Digital Signal
    ↓
Raspberry Pi 3B+ (GPIO Control + Signal Processing)
    ↓
TIA Gain Selection (2.75 kΩ to 350 kΩ)
    ↓
Operating Mode Selection (Deep Sleep, 3-Lead AC, etc.)
    ↓
Data Processing (FFT Denoising, Peak Analysis)
    ↓
Calibration(Default-> Linear, Optional-> Piecewise Linear)
    ↓
Graphical Interface (Tkinter) + Safety Monitoring (Modern UI)
```

### Key Features
- **Real-time electrochemical measurements** via LMP91000 sensor interface
- **Dual measurement methods**: Cyclic Voltammetry (CV) and Chronoamperometry (CA)
- **Advanced signal processing**: FFT-based denoising with frequency domain filtering
- **Peak-to-RMS analysis**: Frequency degradation analysis
- **Piecewise linear calibration**: Multi-segment calibration for improved accuracy across concentration ranges
- **Safety monitoring**: Real-time toxic concentration alerts
- **Modern GUI**: CustomTkinter-based interface with calibration curves

---

## Hardware Configuration

### Raspberry Pi 3B+ GPIO Setup
```python
GPIO.setmode(GPIO.BOARD)  # Use physical pin numbering
GPIO.setup(11, GPIO.OUT)  # Pin 11 = Red LED (Status indicator)
GPIO.setup(13, GPIO.OUT)  # Pin 13 = Green LED (Ready indicator)
```

### ADC Configuration
- **Resolution**: 16-bit (values: 0 to 65,535)
- **Reference Voltage (Vref)**: 2.5 V
- **Maximum Voltage (Vmax)**: 5 V
- **Sampling Frequency**: 250 kHz (default)

### Sensor Specifications (LMP91000)
- **TIA Gain Options**: 2.75 kΩ, 3.5 kΩ, 7 kΩ, 14 kΩ, 35 kΩ, 120 kΩ, 350 kΩ
- **Operating Modes**: Deep Sleep, 2-Lead GRGC, Standby, 3-Lead AC, Temperature MT-OFF, Temperature MT-ON
- **Bias Potentials**: -0.6 V to +0.6 V (27 voltage points in 0.05 V increments)

---

## File Structure

### 1. `test_INTEGRATEDFULL.py` (Main Application - ~1135 lines)
The primary interface application handling:
- Electrochemical measurements
- User interface management
- Data visualization
- Signal processing and denoising
- Concentration calculations using a linear calibration function with optional piecewise linear calibration

### 2. `modern app interface.py` (~300 lines)
Modern CustomTkinter-based GUI featuring:
- Welcome page
- Sample insertion verification
- pH buffer configuration
- Real-time calibration and safety monitoring
- Live current reading display
- Concentration calculations using a linear calibration function with optional piecewise linear calibration

### 3. `var.py` and `settings.py` (External Dependencies)
Configuration files containing:
- Register definitions for LMP91000 sensor
- TIA configuration constants
- Operating mode constants
- I2C communication parameters
- Piecewise linear calibration segment definitions

---
## Calibration Methodology

### Piecewise Linear Calibration Function

The system implements an **integrated piecewise linear calibration function** to determine concentration from measured current with improved accuracy across multiple concentration ranges.

#### Methodology Overview

**Concept**: Instead of using a single linear or logarithmic calibration curve, the system divides the concentration range into multiple segments, each with its own linear calibration function.

```
Concentration (µM)
    ↑
    │     Segment 1        Segment 2        Segment 3
    │  (Low range)      (Mid range)     (High range)
    │    ╱────              ╱────              ╱────
    │   ╱                  ╱                  ╱
    │  ╱                  ╱                  ╱
    └─────────────────────────────────────────────→ Current (µA)
```

#### Implementation Details

**Segment Definition** [Configurable in settings.py]:
```python
CALIBRATION_SEGMENTS = [
    {
        'range': (0, 100),           # µM concentration range
        'slope': 0.1499,             # µA/µM (lower sensitivity region)
        'intercept': -0.4881         # µA
    },
    {
        'range': (100, 500),         # µM concentration range
        'slope': 0.1245,             # µA/µM (mid-range)
        'intercept': 2.1543
    },
    {
        'range': (500, 2000),        # µM concentration range
        'slope': 0.0987,             # µA/µM (high concentration)
        'intercept': 8.7654
    }
]
```

**Calculation Process**:

1. **Measure Current** (I_measured in µA)
   - Obtained from chronoamperometry or peak current from CV

2. **Identify Segment**
   - Compare I_measured against segment boundaries
   - Select appropriate calibration segment

3. **Calculate Concentration**
   ```
   C (µM) = (I_measured - intercept) / slope
   ```
   Using the slope and intercept of the selected segment

4. **Validation**
   - Check if calculated concentration falls within segment range
   - If out of range, flag for recalibration or measurement repeat
   - Apply confidence scoring based on residuals

#### Advantages Over Single-Line Calibration

- **Improved Accuracy**: Non-linear sensor response is approximated more accurately
- **Extended Dynamic Range**: Better linearity across wide concentration ranges
- **Reduced Calibration Drift**: Segment-specific coefficients adapt to hardware variations
- **Environmental Adaptation**: Segments can be adjusted based on temperature or electrode condition
- **Real-Time Confidence**: System can provide uncertainty estimates for each measurement

#### Example Calculation

```
If measured current = 15.5 µA

Check segments:
- Segment 1: (0-100 µM) -> Use slope=0.1499, intercept=-0.4881
- Result: C = (15.5 - (-0.4881)) / 0.1499 = 15.5 + 0.4881 / 0.1499 ≈ 107.2 µM
- Out of range! → Check Segment 2

- Segment 2: (100-500 µM) → Use slope=0.1245, intercept=2.1543
- Result: C = (15.5 - 2.1543) / 0.1245 ≈ 107.1 µM ✓ (Within range)
- **Final Concentration: 107.1 µM** (HEALTH RISK, 10 < C < 181)
```

#### Future Enhancements

- **Adaptive Calibration**: Automatic segment coefficient updates based on reference standards
- **Polynomial Segments**: Use 2nd-order polynomials within segments for enhanced accuracy
- **Temperature Compensation**: Segment parameters adjust based on electrode temperature
- **Electrode Aging Model**: Automatic drift correction over extended deployment

---
## Function Documentation

### Core Signal Processing Functions

#### 1. **`smooth(y, box_pts)`** [Lines 128-131]
**Purpose**: Apply moving average filtering to smooth noisy data

**Parameters**:
- `y` (array): Input signal to be smoothed
- `box_pts` (int): Size of the smoothing window

**Mechanism**:
- Creates a normalized box kernel of size `box_pts`
- Performs convolution with mode='same' to maintain signal length
- Returns smoothed signal without changing signal boundaries

**Example Usage**:
```python
smoothed_data = smooth(data, 64)  # 64-point moving average
```

**Output**: Smoothed numpy array preserving original length

---

#### 2. **`fft_denoise(data, sampling_freq=250000, display_plots=True)`** [Lines 241-408]

**Purpose**: Remove high-frequency noise from cyclic voltammogram data using FFT-based denoising

**Parameters**:
- `data` (array-like): Current values (µA) from CV measurement
- `sampling_freq` (float): ADC sampling frequency in Hz (default: 250 kHz)
- `display_plots` (bool): If True, displays analysis in embedded Tkinter window

**Processing Steps**:

1. **Signal Segmentation** [Lines 264-268]
   - Splits data into two segments: forward scan (indices 0-27) and reverse scan (indices 27-54)
   - Each segment analyzed independently for customized cutoff detection

2. **Windowing** [Lines 270-278]
   - Applies Hanning window to each segment to reduce spectral leakage
   - Formula: `windowed_signal = segment × hanning_window`
   - Hanning window: `w(n) = 0.5 × [1 - cos(2π n/(N-1))]` for n = 0 to N-1

3. **FFT Computation** [Lines 276-295]
   - Computes FFT for each segment and combined signal
   - Calculates magnitude spectrum: `|FFT(x)|`
   - Extracts positive frequencies for analysis

4. **Automatic Cutoff Detection** [Lines 297-327]
   - Threshold: 5% of maximum magnitude
   - Identifies first frequency where magnitude falls below threshold
   - Formula: `threshold = 0.05 × max(magnitude)`
   - Fallback: Uses 30% of Nyquist frequency if no natural cutoff found

5. **Filtering** [Lines 328-347]
   - Creates brick-wall low-pass filter mask
   - Formula: `filter_mask = 1 if |frequency| < cutoff_freq else 0`
   - Applies filter in frequency domain: `filtered_FFT = FFT × filter_mask`

6. **Inverse FFT** [Lines 350-361]
   - Converts filtered signal back to time domain
   - Formula: `denoised_signal = IFFT(filtered_FFT)`
   - Extracts real component: `denoised_signal.real`
   - Reverses second segment and applies negative sign

7. **Peak Rescaling** [Lines 354-370]
   - Preserves peak magnitude of original signal
   - Formula: `scaling_factor = original_peak / denoised_peak`
   - Applied: `denoised_signal_scaled = denoised_signal × scaling_factor`
   - Prevents signal attenuation from affecting concentration calculations

**Returns** [Lines 408]:
- `denoised_signal` (ndarray): Filtered current values
- `cutoff_freq` (float): Automatically determined cutoff frequency

**Output Metrics**:
- SNR improvement in dB
- Energy retention percentage
- Noise reduction percentage
- Original vs denoised peak comparison

---

#### 3. **`calculate_peak_to_rms(data, window_size=None)`** [Lines 413-463]

**Purpose**: Calculate peak-to-RMS current ratio for signal quality assessment

**Parameters**:
- `data` (array-like): Current values (µA) from CV measurement
- `window_size` (int, optional): Size of analysis window around peak

**Calculations**:

1. **Peak Current** [Lines 451]:
   - `i_peak = max(|data|)`
   - Absolute maximum current value

2. **RMS (Root Mean Square) Current** [Lines 454]:
   - `i_rms = sqrt(mean(data²))`
   - Represents effective noise/oscillation level
   - Standard deviation equivalent for AC signals

3. **Peak-to-RMS Ratio** [Lines 461]:
   - `ratio = i_peak / i_rms`
   - High ratio = sharp, clean peak (good signal quality)
   - Low ratio = broad, noisy peak (poor signal quality)

**Returns**:
- `peak_to_rms_ratio` (float): Signal sharpness metric
- `i_peak` (float): Maximum current (µA)
- `i_rms` (float): RMS current (µA)

**Physical Interpretation**:
- Ratio > 5: Excellent signal quality
- Ratio 3-5: Good signal quality
- Ratio < 3: Poor signal quality, increased noise

---

#### 4. **`analyze_frequency_degradation(frequencies, cv_data_list, window_size=None, plot=True)`** [Lines 543-664]

**Purpose**: Analyze peak-to-RMS ratio degradation across multiple measurement frequencies

**Parameters**:
- `frequencies` (array): List of frequencies (Hz) where CV measurements were taken
- `cv_data_list` (list of arrays): Current data arrays for each frequency
- `window_size` (int, optional): Analysis window size
- `plot` (bool): If True, generates degradation plots

**Processing Steps**:

1. **Ratio Calculation** [Lines 571-579]
   - Iterates through each frequency
   - Calls `calculate_peak_to_rms()` for each dataset
   - Stores peak current, RMS current, and ratio

2. **Curve Fitting** [Lines 581-614]
   - **Model Function**: `y = a + b × ln(x)`
   - **Initial Guess**: `p0 = [max(ratios), -1]`
   - Uses `scipy.optimize.curve_fit()` with max 10,000 function evaluations
   - Calculates R² (coefficient of determination):
     ```
     R² = 1 - (Σ(y_actual - y_fit)²) / (Σ(y_actual - y_mean)²)
     ```
   - R² close to 1.0 indicates excellent fit

3. **Interpretation** [Lines 646-649]
   - Negative `b` coefficient: Expected decay with frequency
   - Reflects capacitive interference and kinetic suppression
   - Higher frequencies = broader peaks (lower ratio)
   - Lower frequencies = sharper peaks (higher ratio)

**Returns** (Dictionary):
```python
{
    'frequencies': numpy array of frequencies (Hz),
    'peak_to_rms_ratios': list of ratio values,
    'peak_currents': list of peak current values (µA),
    'rms_currents': list of RMS current values (µA),
    'fit_params': [a, b] coefficients for inverse log fit,
    'fit_quality': R² value (0 to 1),
    'fit_equation': String representation of fit
}
```

---

### Display and Visualization Functions

#### 5. **`display_fft_plots_in_window(data, denoised_signal, windowed_signal, ...)`** [Lines 136-235]

**Purpose**: Create a 6-panel FFT analysis visualization in a non-blocking Tkinter window

**Generates Plots**:

1. **Panel 1 - Original Current Signal**
   - X-axis: Voltage (V) from -0.6 to +0.6
   - Y-axis: Current (µA)
   - Shows raw, unprocessed measurement

2. **Panel 2 - Windowed Signal**
   - Display of Hanning window application
   - Shows signal before FFT

3. **Panel 3 - FFT Magnitude Spectrum**
   - X-axis: Frequency (kHz)
   - Y-axis: Magnitude
   - Stem plot showing frequency components
   - Vertical line indicates automatic cutoff frequency

4. **Panel 4 - Filtered FFT**
   - Same axes as Panel 3
   - Shows only frequencies below cutoff
   - Demonstrates low-pass filtering effect

5. **Panel 5 - Denoised Signal**
   - Inverse FFT result
   - High-frequency noise removed
   - Same format as Panel 1

6. **Panel 6 - Comparison**
   - Overlays original and denoised signals
   - Visualizes noise reduction effectiveness

**Parameters**: FFT arrays, filter data, frequency information
**Returns**: Reference to Toplevel window (allows multiple simultaneous plots)

---

#### 6. **`display_degradation_plots_in_window(frequencies, peak_to_rms_ratios, ...)`** [Lines 469-537]

**Purpose**: Create 4-panel frequency degradation analysis visualization

**Generates Plots**:

1. **Panel 1 - Linear Frequency Scale**
   - Peak-to-RMS ratio vs frequency (linear)
   - Shows measured data points and fitted curve
   - Displays R² value

2. **Panel 2 - Logarithmic Frequency Scale**
   - Same data on logarithmic frequency axis
   - Better visualization of decay behavior
   - Shows why inverse log function fits well

3. **Panel 3 - Peak Current Degradation**
   - Peak current vs frequency (log scale)
   - Shows amplitude loss at higher frequencies
   - Indicates sensor frequency response limitations

4. **Panel 4 - RMS Current vs Frequency**
   - Noise level degradation analysis
   - Higher frequencies = higher noise floor
   - Explains loss of SNR at high frequencies

---

### Measurement and Data Acquisition Functions

#### 7. **`sweep(TIA, OPMODE)`** [Lines 724-815]

**Purpose**: Execute electrochemical measurement sweep (CV or CA depending on method selection)

**Parameters**:
- `TIA`: Transimpedance gain register value (from TIA_dicc)
- `OPMODE`: Operating mode register value (from OPMODE_dicc)

**Initialization Phase** [Lines 728-731]:
```python
init(LOCKWR, TIA, REFCN_BIAS_N[0], OPMODE)
```
- Unlocks sensor write access
- Sets TIA gain
- Sets reference voltage to -0.6 V (initial)
- Sets operating mode (3-Lead AC typical)

**Warm-up Phase** [Line 739]:
- 20-second stabilization period
- Allows sensor to reach thermal and electrical equilibrium
- Critical for reproducible measurements

**Cyclic Voltammetry Sweep** [Lines 741-761]:
```
For each of 54 voltage steps (0-53):
  1. Apply voltage via step(FULL_SWEEP[p])
  2. Read ADC value via printdout(p)
  3. Calculate current: DATA_cv[p] = 2*raw_current + 15
  4. Update progress bar (12% increment per step)
  5. Update graph
  6. Sleep 1 second between measurements
```

**Fixed Voltage (Chronoamperometry) Sweep** [Lines 763-806]:
```
For 400 time points:
  1. Apply fixed bias (typically -0.6 V at 0%)
  2. Record current transient
  3. Update every 1 second
  4. Remove edge padding (indices 50-350)
```

**Shutdown Phase** [Lines 811-814]:
```python
init(LOCKRO, TIACN_TIAG_350__RLOAD_010, REFCN_BIAS_N[0], MODECN_OP_MODE_DEEPSLEEP)
```
- Locks sensor to read-only
- Switches to deep sleep mode
- Reduces power consumption

**Returns**: `DATA` - Array of 54 (CV) or 400 (CA) current measurements

---

#### 8. **`printdout(num)` - Voltage and Current Calculation** [Lines 712-722]

**Purpose**: Convert raw ADC reading to calibrated voltage and current

### **CRITICAL: Voltage Calculation & Bounds Explanation**

#### Raw Calculation [Lines 715-720]:
```python
TIAG = TIA_values["{}".format(variable_TIA.get())]  # TIA gain in Ohms
value = readadc()  # Raw ADC value (0 to 65,535)
vref = 2.5  # Reference voltage in volts
vmax = 5  # Maximum voltage range
N = 16  # ADC resolution (16-bit)
binmax = ((2**N)-1)  # Maximum ADC count = 65,535

# KEY VOLTAGE FORMULA:
volts = (vref/2) + (vmax - (vref/2)) * (value) / (binmax)
```

#### Voltage Formula Breakdown:

**Standard ADC to Voltage Conversion**:
```
V = (value / binmax) × V_max
```

**This Project's Modified Approach**:
```
volts = (vref/2) + (vmax - vref/2) × (value/binmax)
```

Which simplifies to:
```
volts = 1.25 + 1.875 × (value / 65535)
```

**Why This Formula Ensures 1.25 V to 5 V Bounds**:

1. **Lower Bound (value = 0)**:
   ```
   volts = (2.5/2) + (5 - 2.5/2) × 0 = 1.25 V
   ```
   - When ADC reads minimum (0), output = 1.25 V
   - This is the baseline offset: `vref/2 = 1.25 V`

2. **Upper Bound (value = 65535)**:
   ```
   volts = (2.5/2) + (5 - 2.5/2) × (65535/65535)
         = 1.25 + 3.75 × 1
         = 5.0 V
   ```
   - When ADC reads maximum (65535), output = 5.0 V

3. **Linear Mapping**:
   - Voltage range: 5 V - 1.25 V = 3.75 V
   - ADC range: 0 to 65,535
   - Resolution: 3.75 V / 65,535 ≈ 57.22 µV per ADC step

#### Baseline Offset for Current Calculation [Line 720]:
```python
current = 571.59 + ((volts - (vref/2)) / (TIAG)) * 1000000
```

**Current Calculation Components**:

1. **Offset Term**: `571.59`
   - Baseline current in µA
   - Accounts for dark/background current
   - Sensor-specific calibration constant

2. **Sensor Response Term**: `((volts - vref/2) / TIAG) × 1,000,000`
   - Subtracts baseline voltage: `volts - 1.25`
   - Divides by TIA resistance (Ω)
   - Converts to µA (×1,000,000)
   
   **Physics**: `I = V / R` (Ohm's Law)
   - If volts = 1.25 V: I = 0 µA (just offset)
   - If volts = 3.75 V: I = 571.59 + (2.5 / R) × 10⁶ µA

3. **Example Calculation** (TIA = 14 kΩ):
   ```
   If ADC reads 32,768 (midpoint):
   volts = 1.25 + 1.875 × (32768/65535) = 1.25 + 0.9375 = 2.1875 V
   
   voltage_above_baseline = 2.1875 - 1.25 = 0.9375 V
   current = 571.59 + (0.9375 / 14000) × 10⁶
           = 571.59 + 66.96
           = 638.55 µA
   ```

#### Voltage Bounds Guarantee:

**Mathematical Proof**:
- Let `f(x) = 1.25 + 1.875 × (x/65535)` where `0 ≤ x ≤ 65535`
- `f'(x) = 1.875/65535 > 0` (strictly increasing)
- `min: f(0) = 1.25 V` ✓
- `max: f(65535) = 1.25 + 1.875 = 5.0 V` ✓
- **Therefore**: `1.25 V ≤ volts ≤ 5.0 V` for all valid ADC readings

**Practical Implications**:
- No overflow/underflow risks
- Predictable current calculation range
- Reference voltage (2.5 V) positioned at 1.25 V mark
- Full utilization of 16-bit ADC resolution
- Symmetric voltage swings around baseline (-0.6 V to +0.6 V in test potentials)

---

### User Interface Event Handlers

#### 9. **`startCV()`** [Lines 820-963]

**Purpose**: Execute complete measurement workflow with data processing and concentration calculation

**Execution Sequence**:

1. **GPIO Indication** [Line 821]:
   - Red LED ON, Green LED OFF (measurement in progress)

2. **Timestamp & Method Selection** [Lines 824-831]:
   - Records measurement time
   - Prepares title with timestamp
   - Selects CV or CA method

3. **Sensor Configuration Logging** [Lines 833-838]:
   - Displays selected TIA gain
   - Displays operating mode
   - Logs to console and GUI

4. **Data Acquisition** [Line 842]:
   - Calls `sweep(TIA, OPMODE)`
   - Returns 54 points (CV) or 400 points (CA)

5. **Optional FFT Denoising** [Lines 846-848]:
   - Uncomment to enable noise removal
   - Cutoff frequency displayed to user

6. **Signal Quality Analysis** [Lines 852-855]:
   - Calculates peak-to-RMS ratio
   - Displays peak and RMS currents
   - Provides signal quality assessment

7. **Data Export - Cyclic Voltammetry** [Lines 863-884]:
   - Separates forward and reverse scans
   - Exports to CSV files with voltage-current pairs
   - Calculates peak anodic and cathodic currents
   - Format: Two columns (voltage in V, current in µA)

8. **Data Export - Chronoamperometry** [Lines 886-906]:
   - Exports time vs current data
   - Removes edge padding (indices 50-350)
   - Finds maximum steady-state current
   - Saves to `current.txt` for real-time monitoring

9. **Concentration Calculation** [Lines 914-962]:
   - **For Catechol**:
     ```
     Concentration (µM) = (Max_Current - b) / m
     ```
     Where: m = 0.1499 (slope), b = -0.4881 (y-intercept)
   
   - **For Ascorbic Acid/Progesterone**:
     ```
     log₁₀(M) = (log₁₀(I_max) - b) / m
     ```
     Uses logarithmic calibration curve

10. **GPIO Indication** [Lines 909-910]:
    - Red LED OFF, Green LED ON (measurement complete)

---

#### 10. **`clearCV()`** [Lines 965-986]

**Purpose**: Reset measurement data and return sensor to safe state

**Operations**:
- Clears graph axes and resets labels
- Initializes empty data arrays (20 points for display)
- Locks sensor to read-only mode
- Enters deep sleep (minimal power consumption)
- Clears title entry field
- Resets global data arrays

---

#### 11. **`saveCV()`** [Lines 988-995]

**Purpose**: Save high-resolution graph image as EPS file

**Format**: EPS (Encapsulated PostScript)
- Resolution: 1000 DPI
- Suitable for publication/documentation
- Landscape orientation
- Saved to `/home/plaksha/Results/LMP91000 Sensor BlindTesting/`

---

#### 12. **`analyzeFrequencyDegradation()`** [Lines 998-1037]

**Purpose**: Execute frequency degradation analysis when multiple CV measurements at different frequencies are available

**Workflow**:
1. Checks minimum of 2 frequency measurements
2. Extracts frequency keys and corresponding data
3. Calls `analyze_frequency_degradation()` with window_size=None
4. Generates embedded FFT analysis plots
5. Saves results to text file with formatted tables and fit equations

---

### Option Menu Change Handlers

#### 13-16. **Option Callback Functions** [Lines 1081-1100]

**Functions**:
- `option_changed_SUBSTANCE()` - Logs substance selection
- `option_changed_TIA()` - Logs TIA gain selection  
- `option_changed_OPMODE()` - Logs operating mode selection
- `option_changed_METHOD()` - Logs measurement method selection

**Mechanism**: Variable tracing with `.trace("w", callback)` triggers callbacks on write

---

## Measurement Methods

### 1. Cyclic Voltammetry (CV)

**Principle**: Apply linearly varying voltage, measure resulting current

**Parameters**:
- **Voltage Range**: -0.6 V to +0.6 V (27 forward, 27 reverse)
- **Scan Rate**: 50 mV/s
- **Points**: 54 total (27 forward + 27 reverse)
- **Measurement Interval**: 1 second between points

**Advantages**:
- Identifies redox potential
- Determines electron transfer mechanisms
- Good for catechol with broad oxidation peak

**Output**:
- Forward scan: Oxidation current as voltage increases
- Reverse scan: Reduction current as voltage decreases
- Peak current indicates analyte concentration

### 2. Chronoamperometry (CA)

**Principle**: Apply fixed voltage, measure current transient over time

**Parameters**:
- **Applied Voltage**: 0 V (fixed bias at -0.6 V)
- **Duration**: 400 seconds
- **Sampling Interval**: 1 second per point
- **Analysis Window**: Points 50-350 (remove edge effects)

**Advantages**:
- Direct steady-state current measurement
- Longer measurement provides stability
- Less sensitive to surface effects
- Better for real-time monitoring

**Output**:
- Steady-state current plateau
- Exponential decay from initial transient
- Maximum current used for concentration calculation

---

## Data Processing Pipeline

```
Raw ADC Data (0-65535)
        ↓
[Voltage Calculation]
1.25V ≤ Voltage ≤ 5V
        ↓
[Current Calculation via Ohm's Law]
I = Offset + (V - Vref/2) / TIA
        ↓
[Optional: FFT Denoising]
- Hanning Window
- Frequency Analysis
- Low-Pass Filtering
- Inverse FFT
- Peak Rescaling
        ↓
[Signal Quality Analysis]
- Peak-to-RMS Calculation
- Frequency Degradation (if multiple freqs)
- Inverse Log Curve Fitting
        ↓
[CSV Export & Visualization]
- Forward/Reverse Scans (CV)
- Time Series (CA)
- Real-time current.txt update
        ↓
[Concentration Calculation]
Linear or Logarithmic Calibration
        ↓
[Safety Classification]
Safe / Health Risk / Toxic
```

---

## Raspberry Pi 3B+ Specific Considerations

### GPIO Pinout
- **Pin 11**: RED LED (Status indicator)
- **Pin 13**: GREEN LED (Ready indicator)
- **I2C**: Standard for LMP91000 communication

### Performance Notes
- **Processing Speed**: FFT operations on ~60 points @ 250 kHz sampling
- **Memory**: Python/Tkinter footprint minimal for Pi 3B+
- **Power**: GPIO control keeps sensor in sleep when idle
- **Thermal**: Long measurements (400s CA) may generate heat

### Interface Libraries
- **RPi.GPIO**: GPIO control (must run as root/sudo)
- **Tkinter**: Native to Raspberry Pi OS
- **CustomTkinter**: Lightweight modern GUI (available via pip)
- **SciPy/NumPy**: Signal processing (pre-installed most distributions)

---

## Configuration Files

### `var.py` (External Import)
Contains all sensor register definitions:
- TIA register values (TIACN_TIAG_*_RLOAD_010)
- Operating mode registers (MODECN_OP_MODE_*)
- Reference voltage bias values (REFCN_BIAS_N/P[0-13])
- Communication lock/unlock commands (LOCKWR, LOCKRO)

### `settings.py` (External Import)
Contains:
- FULL_SWEEP array (54-point voltage sweep)
- Register write/read/init functions
- I2C device address and parameters
- ADC reading function (readadc())

---

## Calibration Curve Data

### Catechol Calibration
```
Substance: Catechol
Molecular Weight: 110.1 g/mol
Calibration: Linear (I vs C)
Slope (m): 0.1499 µA/µM
Intercept (b): -0.4881 µA

Equation: Concentration = (Max_Current - (-0.4881)) / 0.1499
```

### Ascorbic Acid / Progesterone
```
Substance: Ascorbic Acid or Progesterone
Molecular Weight: 176.12 g/mol
Calibration: Logarithmic (log I vs log C)
Slope (m): 0.9033
Intercept (b): 4.1644
Volume: 1 mL

Equation: log₁₀(M) = (log₁₀(I) - 4.1644) / 0.9033
Result: Mass (mg) = (V × W × M) / 1000
```

---

## Modern UI Application (`modern app interface.py`)

### Page Structure

#### WelcomePage
- Introduction screen
- Project title and description
- EPA compliance note for catechol exposure limits

#### SamplePage
- Verification of sample insertion
- User acknowledgment before proceeding

#### BufferPage
- pH buffer requirement (ABS+PBS)
- pH validation (must equal 6.5)
- Prevents measurement with incorrect pH

#### CalibrationPage
- Live calibration curve display (calibration.png)
- Real-time current reading every 2 seconds
- Safety classification display:
  - **Green**: Concentration < 10 µM (SAFE)
  - **Orange**: 10 µM < Concentration < 181 µM (HEALTH RISK)
  - **Red**: Concentration > 181 µM (UNSAFE TOXIC)

### Safety Thresholds
```python
ACUTE_LIMIT = 10.0 µM     # Short-term exposure limit
CHRONIC_LIMIT = 181.0 µM  # Long-term exposure limit
```

### Auto-Read Loop [Lines 250-278]
- Reads current.txt every 2000 ms (2 seconds)
- Non-blocking UI updates via Tkinter's .after() method
- Handles file not found and invalid data errors gracefully

---

## Key Mathematical Formulas

### 1. Voltage to Current (Transimpedance)
```
I (µA) = Baseline_Offset + ((V - Vref/2) / R_TIA) × 10⁶

Where:
- Baseline_Offset = 571.59 µA (dark current)
- V = voltage from ADC (1.25 to 5.0 V)
- Vref = 2.5 V (reference voltage)
- R_TIA = TIA resistance (2.75 kΩ to 350 kΩ)
```

### 2. FFT-based Denoising
```
Denoised_Signal = IFFT(FFT(Windowed_Signal) × LowPassFilter)

Where:
- Windowed_Signal = Original_Signal × Hanning_Window
- LowPassFilter = 1 if |f| < f_cutoff, else 0
- f_cutoff = Automatic (5% threshold) or Fallback (30% Nyquist)
```

### 3. Peak-to-RMS Ratio
```
Peak_to_RMS = max(|I|) / sqrt(mean(I²))

Quality Assessment:
- > 5: Excellent (noise < 20% of peak)
- 3-5: Good (noise 20-33% of peak)
- < 3: Poor (noise > 33% of peak)
```

### 4. Frequency Degradation Fit
```
Peak_to_RMS(f) = a + b × ln(f)

Parameters:
- a: Intercept (peak sharpness at reference frequency)
- b: Slope (decay rate, typically negative)
- R²: Goodness of fit (0 to 1)
```

### 5. Concentration from Current
```
For Catechol (Linear):
C (µM) = (I_max - b) / m = (I_max + 0.4881) / 0.1499

For Ascorbic Acid (Log):
log₁₀(M) = (log₁₀(I) - 4.1644) / 0.9033
C (M) = 10^[log₁₀(I) - 4.1644] / 0.9033
```

---

## Troubleshooting Guide

### Common Issues

#### 1. Voltage Out of Bounds (< 1.25 V or > 5.0 V)
**Cause**: ADC read error or sensor disconnection
**Solution**: 
- Verify I2C connection
- Check ADC firmware
- Confirm reference voltage circuit

#### 2. Negative Current Values
**Cause**: Dark current offset miscalibration
**Solution**:
- Recalibrate offset value (571.59)
- Measure zero-bias current with no analyte
- Update offset accordingly

#### 3. FFT Denoising Not Removing Noise
**Cause**: Noise frequency within signal band
**Solution**:
- Increase sampling frequency (if hardware capable)
- Adjust threshold from 5% to 10%
- Reduce scan rate for smoother signal

#### 4. Peak-to-RMS Ratio Always Low
**Cause**: Sensor under-damped or TIA gain too low
**Solution**:
- Increase TIA gain (try 14 kΩ or higher)
- Reduce measurement temperature
- Check sensor surface for contamination

#### 5. pH Validation Fails
**Cause**: Buffer not yet equilibrated
**Solution**:
- Wait longer after buffer addition
- Stir solution thoroughly
- Use calibrated pH meter

---

## References

- **LMP91000**: Electrochemical Sensor AFE Datasheet(https://www.alldatasheet.com/datasheet-pdf/pdf/2195217/TI2/LMP91000.html)
- **FFT Denoising**: Oppenheim & Schafer "Discrete-Time Signal Processing"
- **Cyclic Voltammetry**: Bard & Faulkner "Electrochemical Methods"
- **Chronoamperometry**: Cottrell Equation for transient current decay
- **Catechol EPA Limits**: Environmental Protection Agency Industrial Guide

---

## Modified Code from 

**Project**: Design and development of a portable, low-cost and customizable sensor platform based on a potentiostat mainly integrated by commercial off-the-shelf (COTS) electronic components.
**Author**: Juan Poveda
**Institution**: Technical University of Cartagena
**Status**: Complete

For questions or improvements, refer to the GitHub repository issues and discussions.
