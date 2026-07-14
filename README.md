Industrial Catechol Detection System - Comprehensive Documentation
Project Overview
This is an Industrial Treated Wastewater Quality Monitoring System for catechol detection using electrochemical sensors. The system is designed to run on a Raspberry Pi 3B+ microprocessor and uses LMP91000 Current Sensor transimpedance amplifiers (TIA) with cyclic voltammetry and chronoamperometry methods and integrated piecewise linear calibration function(optional) for accurate detection.
---
Table of Contents
How to Use?
System Architecture
Hardware Configuration
File Structure
Main Application Files
Calibration Methodology
Function Documentation
Voltage Calculation & Bounds Explanation
Measurement Methods
Data Processing Pipeline
Chronoamperometry Planner (Section 6.2)
---
How to Use
Modern Interface: Double-click the app icon on the home screen to launch the modern CustomTkinter-based interface.
For Development:
Open Documents Folder and launch Python3
Code for the Prototype Development Interface and App is located within this directory
Do not move files out of directory
Make modifications without changing file names
System Architecture
Workflow Steps:
Welcome page with system information
Sample insertion verification
pH buffer configuration (ABS+PBS, target pH 6.5)
Real-time calibration monitoring with safety assessment
Automated concentration calculation and risk classification
Overview
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
Key Features
Real-time electrochemical measurements via LMP91000 sensor interface
Dual measurement methods: Cyclic Voltammetry (CV) and Chronoamperometry (CA)
Advanced signal processing: FFT-based denoising with frequency domain filtering
Peak-to-RMS analysis: Frequency degradation analysis
Piecewise linear calibration: Multi-segment calibration for improved accuracy across concentration ranges
Safety monitoring: Real-time toxic concentration alerts
Modern GUI: CustomTkinter-based interface with calibration curves
---
Hardware Configuration
Raspberry Pi 3B+ GPIO Setup
```python
GPIO.setmode(GPIO.BOARD)  # Use physical pin numbering
GPIO.setup(11, GPIO.OUT)  # Pin 11 = Red LED (Status indicator)
GPIO.setup(13, GPIO.OUT)  # Pin 13 = Green LED (Ready indicator)
```
ADC Configuration
Resolution: 16-bit (values: 0 to 65,535)
Reference Voltage (Vref): 2.5 V
Maximum Voltage (Vmax): 5 V
Sampling Frequency: 250 kHz (default)
Sensor Specifications (LMP91000)
TIA Gain Options: 2.75 kΩ, 3.5 kΩ, 7 kΩ, 14 kΩ, 35 kΩ, 120 kΩ, 350 kΩ
Operating Modes: Deep Sleep, 2-Lead GRGC, Standby, 3-Lead AC, Temperature MT-OFF, Temperature MT-ON
Bias Potentials: -0.6 V to +0.6 V (27 voltage points in 0.05 V increments)
---
File Structure
1. `test\\\\\\\_INTEGRATEDFULL.py` (Main Application - ~1135 lines)
The primary interface application handling:
Electrochemical measurements
User interface management
Data visualization
Signal processing and denoising
Concentration calculations using a linear calibration function with optional piecewise linear calibration
2. `modern app interface.py` (~300 lines)
Modern CustomTkinter-based GUI featuring:
Welcome page
Sample insertion verification
pH buffer configuration
Real-time calibration and safety monitoring
Live current reading display
Concentration calculations using a linear calibration function with optional piecewise linear calibration
3. `var.py` and `settings.py` (External Dependencies)
Configuration files containing:
Register definitions for LMP91000 sensor
TIA configuration constants
Operating mode constants
I2C communication parameters
Piecewise linear calibration segment definitions
---
Calibration Methodology
The system converts a measured current into a catechol concentration using one shared
function, `get\\\\\\\_concentration\\\\\\\_from\\\\\\\_current()`, defined in `test\\\\\\\_INTEGRATEDFULL.py` and imported
by `modern app interface.py`. Both interfaces therefore always agree; there is no duplicated
calibration arithmetic anywhere in the codebase.
Two modes are supported:
Mode	When to use	Selected by
Piecewise linear (default)	Wide dynamic range, sensor response bends away from a single straight line	`use\\\\\\\_piecewise=True`; "Piecewise Linear" on the touchscreen, "Piecewise calibration" checkbox on the dev interface
Linear (classic)	Narrow range, single validated straight line, or when you want the legacy behaviour	`use\\\\\\\_piecewise=False`; "Linear" on the touchscreen, checkbox unticked on the dev interface
---
1. Segment definition (concentration domain)
Segments are stored the way they are fitted: you prepare standards of known concentration and
regress i = mC + b within each band.
```python
CALIBRATION\\\\\\\_SEGMENTS = {
    'Catechol': \\\\\\\[
        {'conc\\\\\\\_range': (0.0,   100.0),  'slope': 0.1499, 'intercept': -0.4881},   # low  band
        {'conc\\\\\\\_range': (100.0, 500.0),  'slope': 0.1245, 'intercept':  2.1543},   # mid  band
        {'conc\\\\\\\_range': (500.0, 2000.0), 'slope': 0.0987, 'intercept':  8.7654}    # high band
    ]
}
```
Add as many segments as you like; keep them in ascending concentration order. `LINEAR\\\\\\\_COEFFS`
holds the single-line fallback and its validated working range:
```python
LINEAR\\\\\\\_COEFFS = {
    'Catechol': {'slope': 0.1499, 'intercept': -0.4881, 'conc\\\\\\\_range': (0.0, 500.0)}
}
```
---
2. Segment selection is done in the CURRENT domain
At run time the instrument gives us a current, not a concentration. Selecting a segment by
"invert every line and see which answer lands inside its own band" is ambiguous: independently
fitted lines are not continuous, so near a join two segments can both claim a reading
(overlap) or neither can (gap). For the coefficients above:
Segment	Concentration band	Current at band edges (i = mC + b)
1	0 – 100 µM	−0.4881 → 14.5019 µA
2	100 – 500 µM	14.6043 → 64.4043 µA
3	500 – 2000 µM	58.1154 → 206.1654 µA
There is a gap of ~0.10 µA between segments 1 and 2, and a 6.3 µA overlap between
segments 2 and 3.
`build\\\\\\\_current\\\\\\\_breakpoints()` resolves this once, at import time:
For every segment, compute the current at its two concentration endpoints.
Sort segments by current.
Where two neighbours meet, place the breakpoint at the midpoint of the two boundary
currents. Gaps close, overlaps disappear, and every current maps to exactly one segment.
Resulting current intervals for catechol:
```
Segment 1:  -0.4881  ->  14.5531 µA
Segment 2:  14.5531  ->  61.2599 µA
Segment 3:  61.2599  -> 206.1654 µA

Calibrated window: -0.4881 to 206.1654 µA
```
`calibration\\\\\\\_current\\\\\\\_window(substance, use\\\\\\\_piecewise)` returns this window, and the touchscreen
app prints it whenever a reading falls outside it.
---
3. Concentration calculation
```
C\\\\\\\_measured (µM) = (I\\\\\\\_measured - intercept\\\\\\\_segment) / slope\\\\\\\_segment

C\\\\\\\_true (µM)     = C\\\\\\\_measured x dilution\\\\\\\_factor
```
The dilution factor defaults to 1 (neat sample).
---
4. Out-of-range handling and the dilution workflow
If the measured current is outside the calibrated window, the system does not extrapolate and
does not return a number. Extrapolating a fitted line beyond the standards it was fitted
against is exactly where the largest errors live, and a wrong catechol number is a safety
problem, not just an accuracy problem. Instead:
```
OUT OF RANGE, PERFORM SUCCESSIVE DILUTIONS UNTIL YOU ACHIEVE A CURRENT READING THAT
IS IN RANGE. MULTIPLY THE CORRESPONDING CONCENTRATION BY THE DILUTION FACTOR TO
OBTAIN THE TRUE CONCENTRATION.
```
`classify\\\\\\\_safety(None)` returns status `OUT OF RANGE` in a neutral blue-grey (`#455a64`) - never
a green/orange/red safety colour, so an out-of-range reading can never be mistaken for a verdict.
Operator workflow
A reading comes back OUT OF RANGE (result box turns blue-grey).
Dilute the sample by a known factor. A 1-in-10 dilution (1 mL sample + 9 mL buffer) is a
dilution factor of 10. Repeat / stack dilutions if needed; the factors multiply
(10 then 5 = 50).
Re-measure. When the current lands inside the calibrated window, type the dilution factor into
the Dilution factor box and press Apply.
The app reports `C\\\\\\\_measured x DF` as the true concentration, and the safety classification is
applied to that true value.
The dilution box is always visible (default 1), so an in-range reading on a deliberately diluted
sample is also handled correctly.
---
5. Function contract
```python
get\\\\\\\_concentration\\\\\\\_from\\\\\\\_current(current,
                               substance='Catechol',
                               use\\\\\\\_piecewise=True,
                               dilution\\\\\\\_factor=1.0,
                               segments=None) -> dict
```
Returns:
Key	Type	Meaning
`concentration`	float or `None`	True concentration in µM (`raw x dilution\\\\\\\_factor`); `None` when out of range
`raw\\\\\\\_concentration`	float or `None`	Concentration of the solution as actually measured
`dilution\\\\\\\_factor`	float	Factor applied
`segment\\\\\\\_index`	int	0-based index of the segment used; `-1` for linear mode or out of range
`in\\\\\\\_range`	bool	`False` when the current falls outside the calibrated window
`method`	str	`'piecewise'` or `'linear'`
`unit`	str	`'uM'`
`message`	str	Human-readable status (dilution instructions when out of range)
---
6. Worked examples
```
I = 5.00 µA, piecewise, DF = 1
  -> Segment 1 (current interval -0.4881 to 14.5531 µA)
  -> C = (5.00 - (-0.4881)) / 0.1499 = 36.61 µM
  -> HEALTH RISK (10 < C < 181)

I = 30.00 µA, piecewise, DF = 1
  -> Segment 2 (current interval 14.5531 to 61.2599 µA)
  -> C = (30.00 - 2.1543) / 0.1245 = 223.66 µM
  -> UNSAFE TOXIC (C > 181)

I = 300.00 µA, piecewise
  -> outside calibrated window \\\\\\\[-0.4881, 206.1654] µA
  -> OUT OF RANGE. Dilute the sample.

I = 5.00 µA, piecewise, DF = 10 (sample was diluted 1-in-10)
  -> C\\\\\\\_measured = 36.61 µM
  -> C\\\\\\\_true     = 36.61 x 10 = 366.12 µM
  -> UNSAFE TOXIC

I = 80.00 µA, LINEAR mode
  -> C = (80.00 + 0.4881) / 0.1499 = 536.95 µM, outside the validated 0-500 µM line
  -> OUT OF RANGE. Dilute, or switch to piecewise.
```
---
Advantages over single-line calibration
Improved accuracy: a bending sensor response is approximated far better by several short
lines than by one long one.
Extended dynamic range: 0 – 2000 µM instead of the 0 – 500 µM single-line window.
Honest limits: readings outside the calibrated window are refused rather than extrapolated.
Segment-specific coefficients can absorb electrode-condition effects that vary with
concentration.
Limitations to be aware of
The three segments are independently fitted, so the calibration is not continuous: near a
breakpoint, a small change in current can produce a small step in reported concentration
(~0.7 µM at the 14.55 µA join, larger at the 61.26 µA join, where the two lines disagree by
several µA). If this matters for your write-up, refit with a continuous piecewise model
(constrain adjacent segments to share a value at the knot) or fit the knot positions directly.
The segment coefficients for the mid and high bands are placeholders from an earlier draft.
They must be re-fitted against real catechol standards before the numbers are quotable.
Future enhancements
Continuous / constrained piecewise fit (shared knots) to remove the step discontinuities
Automatic dilution suggestion: propose a factor from how far outside the window the reading is
Polynomial segments (2nd order) within bands
Temperature compensation and an electrode aging / drift model
Error propagation through the dilution chain, to attach an uncertainty to `C\\\\\\\_true`
---
Function Documentation
Core Signal Processing Functions
1. `smooth(y, box\\\\\\\_pts)` [Lines 128-131]
Purpose: Apply moving average filtering to smooth noisy data
Parameters:
`y` (array): Input signal to be smoothed
`box\\\\\\\_pts` (int): Size of the smoothing window
Mechanism:
Creates a normalized box kernel of size `box\\\\\\\_pts`
Performs convolution with mode='same' to maintain signal length
Returns smoothed signal without changing signal boundaries
Example Usage:
```python
smoothed\\\\\\\_data = smooth(data, 64)  # 64-point moving average
```
Output: Smoothed numpy array preserving original length
---
2. `fft\\\\\\\_denoise(data, sampling\\\\\\\_freq=250000, display\\\\\\\_plots=True)` [Lines 241-408]
Purpose: Remove high-frequency noise from cyclic voltammogram data using FFT-based denoising
Parameters:
`data` (array-like): Current values (µA) from CV measurement
`sampling\\\\\\\_freq` (float): ADC sampling frequency in Hz (default: 250 kHz)
`display\\\\\\\_plots` (bool): If True, displays analysis in embedded Tkinter window
Processing Steps:
Signal Segmentation [Lines 264-268]
Splits data into two segments: forward scan (indices 0-27) and reverse scan (indices 27-54)
Each segment analyzed independently for customized cutoff detection
Windowing [Lines 270-278]
Applies Hanning window to each segment to reduce spectral leakage
Formula: `windowed\\\\\\\_signal = segment × hanning\\\\\\\_window`
Hanning window: `w(n) = 0.5 × \\\\\\\[1 - cos(2π n/(N-1))]` for n = 0 to N-1. w(n) is maximized at n=(N-1)/2 and minimum at n=0 and n=N-1 meaning that the discontinuities at extremas are smoothened out preserving the signal.
FFT Computation [Lines 276-295]
Computes FFT for each segment and combined signal
Calculates magnitude spectrum: `|FFT(x)|`
Extracts positive frequencies for analysis
Automatic Cutoff Detection [Lines 297-327]
Threshold: 5% of maximum magnitude
Identifies first frequency where magnitude falls below threshold
Formula: `threshold = 0.05 × max(magnitude)`
Fallback: Uses 30% of Nyquist frequency if no natural cutoff found
Filtering [Lines 328-347]
Creates brick-wall low-pass filter mask
Formula: `filter\\\\\\\_mask = 1 if |frequency| < cutoff\\\\\\\_freq else 0`
Applies filter in frequency domain: `filtered\\\\\\\_FFT = FFT × filter\\\\\\\_mask`
Inverse FFT [Lines 350-361]
Converts filtered signal back to time domain
Formula: `denoised\\\\\\\_signal = IFFT(filtered\\\\\\\_FFT)`
Extracts real component: `denoised\\\\\\\_signal.real`
Reverses second segment and applies negative sign
Peak Rescaling [Lines 354-370]
Preserves peak magnitude of original signal
Formula: `scaling\\\\\\\_factor = original\\\\\\\_peak / denoised\\\\\\\_peak`
Applied: `denoised\\\\\\\_signal\\\\\\\_scaled = denoised\\\\\\\_signal × scaling\\\\\\\_factor`
Prevents signal attenuation from affecting concentration calculations
Returns [Lines 408]:
`denoised\\\\\\\_signal` (ndarray): Filtered current values
`cutoff\\\\\\\_freq` (float): Automatically determined cutoff frequency
Output Metrics:
SNR improvement in dB
Energy retention percentage
Noise reduction percentage
Original vs denoised peak comparison
---
3. `calculate\\\\\\\_peak\\\\\\\_to\\\\\\\_rms(data, window\\\\\\\_size=None)` [Lines 413-463]
Purpose: Calculate peak-to-RMS current ratio for signal quality assessment
Parameters:
`data` (array-like): Current values (µA) from CV measurement
`window\\\\\\\_size` (int, optional): Size of analysis window around peak
Calculations:
Peak Current [Lines 451]:
`i\\\\\\\_peak = max(|data|)`
Absolute maximum current value
RMS (Root Mean Square) Current [Lines 454]:
`i\\\\\\\_rms = sqrt(mean(data²))`
Represents effective noise/oscillation level
Standard deviation equivalent for AC signals
Peak-to-RMS Ratio [Lines 461]:
`ratio = i\\\\\\\_peak / i\\\\\\\_rms`
High ratio = sharp, clean peak (good signal quality)
Low ratio = broad, noisy peak (poor signal quality)
Returns:
`peak\\\\\\\_to\\\\\\\_rms\\\\\\\_ratio` (float): Signal sharpness metric
`i\\\\\\\_peak` (float): Maximum current (µA)
`i\\\\\\\_rms` (float): RMS current (µA)
Physical Interpretation:
Ratio > 5: Excellent signal quality
Ratio 3-5: Good signal quality
Ratio < 3: Poor signal quality, increased noise
---
4. `analyze\\\\\\\_frequency\\\\\\\_degradation(frequencies, cv\\\\\\\_data\\\\\\\_list, window\\\\\\\_size=None, plot=True)` [Lines 543-664]
Purpose: Analyze peak-to-RMS ratio degradation across multiple measurement frequencies
Parameters:
`frequencies` (array): List of frequencies (Hz) where CV measurements were taken
`cv\\\\\\\_data\\\\\\\_list` (list of arrays): Current data arrays for each frequency
`window\\\\\\\_size` (int, optional): Analysis window size
`plot` (bool): If True, generates degradation plots
Processing Steps:
Ratio Calculation [Lines 571-579]
Iterates through each frequency
Calls `calculate\\\\\\\_peak\\\\\\\_to\\\\\\\_rms()` for each dataset
Stores peak current, RMS current, and ratio
Curve Fitting [Lines 581-614]
Model Function: `y = a + b × ln(x)`
Initial Guess: `p0 = \\\\\\\[max(ratios), -1]`
Uses `scipy.optimize.curve\\\\\\\_fit()` with max 10,000 function evaluations
Calculates R² (coefficient of determination):
```
     R² = 1 - (Σ(y\\\\\\\_actual - y\\\\\\\_fit)²) / (Σ(y\\\\\\\_actual - y\\\\\\\_mean)²)
     ```

   \\\* R² close to 1.0 indicates excellent fit
3. \\\*\\\*Interpretation\\\*\\\* \\\\\\\[Lines 646-649]

   \\\* Negative `b` coefficient: Expected decay with frequency
   \\\* Reflects capacitive interference and kinetic suppression
   \\\* Higher frequencies = broader peaks (lower ratio)
   \\\* Lower frequencies = sharper peaks (higher ratio)

\\\*\\\*Returns\\\*\\\* (Dictionary):

```python
{
    'frequencies': numpy array of frequencies (Hz),
    'peak\\\\\\\_to\\\\\\\_rms\\\\\\\_ratios': list of ratio values,
    'peak\\\\\\\_currents': list of peak current values (µA),
    'rms\\\\\\\_currents': list of RMS current values (µA),
    'fit\\\\\\\_params': \\\\\\\[a, b] coefficients for inverse log fit,
    'fit\\\\\\\_quality': R² value (0 to 1),
    'fit\\\\\\\_equation': String representation of fit
}
```
---
Calibration Function
`get\\\\\\\_concentration\\\\\\\_from\\\\\\\_current(current, segments=None)` [NEW]
Purpose: Apply piecewise linear calibration to convert measured current to concentration
Parameters:
`current` (float): Measured current in µA
`segments` (list, optional): Custom calibration segments (uses defaults if None)
Returns:
```python
{
    'concentration': float,      # Concentration in µM
    'segment\\\\\\\_index': int,        # Which segment was used
    'confidence': float,         # Confidence score (0-1)
    'unit': str                  # 'µM'
}
```
Implementation:
```python
def get\\\\\\\_concentration\\\\\\\_from\\\\\\\_current(current, segments=None):
    """
    Apply piecewise linear calibration.
    Returns concentration with segment information.
    """
    if segments is None:
        segments = CALIBRATION\\\\\\\_SEGMENTS  # From settings.py
    
    for idx, segment in enumerate(segments):
        conc = (current - segment\\\\\\\['intercept']) / segment\\\\\\\['slope']
        min\\\\\\\_c, max\\\\\\\_c = segment\\\\\\\['range']
        
        if min\\\\\\\_c <= conc <= max\\\\\\\_c:
            confidence = calculate\\\\\\\_confidence(conc, current, segment)
            return {
                'concentration': conc,
                'segment\\\\\\\_index': idx,
                'confidence': confidence,
                'unit': 'µM'
            }
    
    # Out of range - return best estimate
    segment = segments\\\\\\\[-1]  # Use highest segment
    conc = (current - segment\\\\\\\['intercept']) / segment\\\\\\\['slope']
    return {
        'concentration': conc,
        'segment\\\\\\\_index': len(segments) - 1,
        'confidence': 0.5,  # Low confidence
        'unit': 'µM'
    }
```
---
Display and Visualization Functions
5. `display\\\\\\\_fft\\\\\\\_plots\\\\\\\_in\\\\\\\_window(data, denoised\\\\\\\_signal, windowed\\\\\\\_signal, ...)` [Lines 136-235]
Purpose: Create a 6-panel FFT analysis visualization in a non-blocking Tkinter window
Generates Plots:
Panel 1 - Original Current Signal
X-axis: Voltage (V) from -0.6 to +0.6
Y-axis: Current (µA)
Shows raw, unprocessed measurement
Panel 2 - Windowed Signal
Display of Hanning window application
Shows signal before FFT
Panel 3 - FFT Magnitude Spectrum
X-axis: Frequency (kHz)
Y-axis: Magnitude
Stem plot showing frequency components
Vertical line indicates automatic cutoff frequency
Panel 4 - Filtered FFT
Same axes as Panel 3
Shows only frequencies below cutoff
Demonstrates low-pass filtering effect
Panel 5 - Denoised Signal
Inverse FFT result
High-frequency noise removed
Same format as Panel 1
Panel 6 - Comparison
Overlays original and denoised signals
Visualizes noise reduction effectiveness
Parameters: FFT arrays, filter data, frequency information
Returns: Reference to Toplevel window (allows multiple simultaneous plots)
---
6. `display\\\\\\\_degradation\\\\\\\_plots\\\\\\\_in\\\\\\\_window(frequencies, peak\\\\\\\_to\\\\\\\_rms\\\\\\\_ratios, ...)` [Lines 469-537]
Purpose: Create 4-panel frequency degradation analysis visualization
Generates Plots:
Panel 1 - Linear Frequency Scale
Peak-to-RMS ratio vs frequency (linear)
Shows measured data points and fitted curve
Displays R² value
Panel 2 - Logarithmic Frequency Scale
Same data on logarithmic frequency axis
Better visualization of decay behavior
Shows why inverse log function fits well
Panel 3 - Peak Current Degradation
Peak current vs frequency (log scale)
Shows amplitude loss at higher frequencies
Indicates sensor frequency response limitations
Panel 4 - RMS Current vs Frequency
Noise level degradation analysis
Higher frequencies = higher noise floor
Explains loss of SNR at high frequencies
---
Measurement and Data Acquisition Functions
7. `sweep(TIA, OPMODE)` [Lines 724-815]
Purpose: Execute electrochemical measurement sweep (CV or CA depending on method selection)
Parameters:
`TIA`: Transimpedance gain register value (from TIA_dicc)
`OPMODE`: Operating mode register value (from OPMODE_dicc)
Initialization Phase [Lines 728-731]:
```python
init(LOCKWR, TIA, REFCN\\\\\\\_BIAS\\\\\\\_N\\\\\\\[0], OPMODE)
```
Unlocks sensor write access
Sets TIA gain
Sets reference voltage to -0.6 V (initial)
Sets operating mode (3-Lead AC typical)
Warm-up Phase [Line 739]:
20-second stabilization period
Allows sensor to reach thermal and electrical equilibrium
Critical for reproducible measurements
Cyclic Voltammetry Sweep [Lines 741-761]:
```
For each of 54 voltage steps (0-53):
  1. Apply voltage via step(FULL\\\\\\\_SWEEP\\\\\\\[p])
  2. Read and calculate the current from ADC value via printdout(p)
  3. Update progress bar (12% increment per step)
  4. Update graph
  5. Sleep 1 second between measurements
```
Fixed Voltage (Chronoamperometry) Sweep [Lines 763-806]:
```
For 400 time points:
  1. Apply fixed bias (typically -0.6 V at 0%)
  2. Record current transient
  3. Update every 1 second
  4. Remove edge padding (indices 50-350)
```
Shutdown Phase [Lines 811-814]:
```python
init(LOCKRO, TIACN\\\\\\\_TIAG\\\\\\\_350\\\\\\\_\\\\\\\_RLOAD\\\\\\\_010, REFCN\\\\\\\_BIAS\\\\\\\_N\\\\\\\[0], MODECN\\\\\\\_OP\\\\\\\_MODE\\\\\\\_DEEPSLEEP)
```
Locks sensor to read-only
Switches to deep sleep mode
Reduces power consumption
Returns: `DATA` - Array of 54 (CV) or 400 (CA) current measurements
---
8. `printdout(num)` - Voltage and Current Calculation [Lines 712-722]
Purpose: Convert raw ADC reading to calibrated voltage and current
CRITICAL: Voltage Calculation & Bounds Explanation
Raw Calculation [Lines 715-720]:
```python
TIAG = TIA\\\\\\\_values\\\\\\\["{}".format(variable\\\\\\\_TIA.get())]  # TIA gain in Ohms
value = readadc()  # Raw ADC value (0 to 65,535)
vref = 2.5  # Reference voltage in volts
vmax = 5  # Maximum voltage range
N = 16  # ADC resolution (16-bit)
binmax = ((2\\\\\\\*\\\\\\\*N)-1)  # Maximum ADC count = 65,535

# KEY VOLTAGE FORMULA:
volts = (vref/2) + (vmax - (vref/2)) \\\\\\\* (value) / (binmax)
```
Voltage Formula Breakdown:
Standard ADC to Voltage Conversion:
```
V = (value / binmax) × V\\\\\\\_max
```
This Project's Modified Approach:
```
volts = (vref/2) + (vmax - vref/2) × (value/binmax)
```
Which simplifies to:
```
volts = 1.25 + 1.875 × (value / 65535)
```
Why This Formula Ensures 1.25 V to 5 V Bounds:
Lower Bound (value = 0):
```
   volts = (2.5/2) + (5 - 2.5/2) × 0 = 1.25 V
   ```
When ADC reads minimum (0), output = 1.25 V
This is the baseline offset: `vref/2 = 1.25 V`
Upper Bound (value = 65535):
```
   volts = (2.5/2) + (5 - 2.5/2) × (65535/65535)
         = 1.25 + 3.75 × 1
         = 5.0 V
   ```
When ADC reads maximum (65535), output = 5.0 V
Linear Mapping:
Voltage range: 5 V - 1.25 V = 3.75 V
ADC range: 0 to 65,535
Resolution: 3.75 V / 65,535 ≈ 57.22 µV per ADC step
Baseline Offset for Current Calculation [Line 720]:
```python
current = 571.59 + ((volts - (vref/2)) / (TIAG)) \\\\\\\* 1000000
```
Current Calculation Components:
Offset Term: `571.59`
Baseline current in µA
Accounts for dark/background current
Sensor-specific calibration constant
Sensor Response Term: `((volts - vref/2) / TIAG) × 1,000,000`
Subtracts baseline voltage: `volts - 1.25`
Divides by TIA resistance (Ω)
Converts to µA (×1,000,000)
Physics: `I = V / R` (Ohm's Law)
If volts = 1.25 V: I = 0 µA (just offset)
If volts = 3.75 V: I = 571.59 + (2.5 / R) × 10⁶ µA
Example Calculation (TIA = 14 kΩ):
```
   If ADC reads 32,768 (midpoint):
   volts = 1.25 + 1.875 × (32768/65535) = 1.25 + 0.9375 = 2.1875 V
   
   voltage\\\\\\\_above\\\\\\\_baseline = 2.1875 - 1.25 = 0.9375 V
   current = 571.59 + (0.9375 / 14000) × 10⁶
           = 571.59 + 66.96
           = 638.55 µA
   ```
Voltage Bounds Guarantee:
Mathematical Proof:
Let `f(x) = 1.25 + 1.875 × (x/65535)` where `0 ≤ x ≤ 65535`
`f'(x) = 1.875/65535 > 0` (strictly increasing)
`min: f(0) = 1.25 V` ✓
`max: f(65535) = 1.25 + 1.875 = 5.0 V` ✓
Therefore: `1.25 V ≤ volts ≤ 5.0 V` for all valid ADC readings
Practical Implications:
No overflow/underflow risks
Predictable current calculation range
Reference voltage (2.5 V) positioned at 1.25 V mark
Full utilization of 16-bit ADC resolution
Symmetric voltage swings around baseline (-0.6 V to +0.6 V in test potentials)
---
User Interface Event Handlers
9. `startCV()` [Lines 820-963]
Purpose: Execute complete measurement workflow with data processing and concentration calculation
Execution Sequence:
GPIO Indication [Line 821]:
Red LED ON, Green LED OFF (measurement in progress)
Timestamp & Method Selection [Lines 824-831]:
Records measurement time
Prepares title with timestamp
Selects CV or CA method
Sensor Configuration Logging [Lines 833-838]:
Displays selected TIA gain
Displays operating mode
Logs to console and GUI
Data Acquisition [Line 842]:
Calls `sweep(TIA, OPMODE)`
Returns 54 points (CV) or 400 points (CA)
Optional FFT Denoising [Lines 846-848]:
Uncomment to enable noise removal
Cutoff frequency displayed to user
Signal Quality Analysis [Lines 852-855]:
Calculates peak-to-RMS ratio
Displays peak and RMS currents
Provides signal quality assessment
Data Export - Cyclic Voltammetry [Lines 863-884]:
Separates forward and reverse scans
Exports to CSV files with voltage-current pairs
Calculates peak anodic and cathodic currents
Format: Two columns (voltage in V, current in µA)
Data Export - Chronoamperometry [Lines 886-906]:
Exports time vs current data
Removes edge padding (indices 50-350)
Finds maximum steady-state current
Saves to `current.txt` for real-time monitoring
Concentration Calculation [Lines 914-962]:
For Catechol:
Default Linear Calibration:
```
     Concentration (µM) = (Max\\\\\\\_Current - b) / m
     ```

     For example, m = 0.1499 (slope), b = -0.4881 (y-intercept)

   \\\* \\\*\\\*Fallback Piecewise Linear Calibration\\\*\\\*:

```
     Concentration (µM) = apply\_piecewise\_calibration(max\_current)
```

&#x20;    Automatically selects appropriate segment based on current magnitude





10. **GPIO Indication** \[Lines 909-910]:

    * Red LED OFF, Green LED ON (measurement complete)

\---

#### 10\. **`clearCV()`** \[Lines 965-986]

**Purpose**: Reset measurement data and return sensor to safe state

**Operations**:

* Clears graph axes and resets labels
* Initializes empty data arrays (20 points for display)
* Locks sensor to read-only mode
* Enters deep sleep (minimal power consumption)
* Clears title entry field
* Resets global data arrays

\---

#### 11\. **`saveCV()`** \[Lines 988-995]

**Purpose**: Save high-resolution graph image as EPS file

**Format**: EPS (Encapsulated PostScript)

* Resolution: 1000 DPI
* Suitable for publication/documentation
* Landscape orientation
* Saved to `/home/plaksha/Results/LMP91000 Sensor BlindTesting/`

\---

#### 12\. **`analyzeFrequencyDegradation()`** \[Lines 998-1037]

**Purpose**: Execute frequency degradation analysis when multiple CV measurements at different frequencies are available

**Workflow**:

1. Checks minimum of 2 frequency measurements
2. Extracts frequency keys and corresponding data
3. Calls `analyze\\\\\\\_frequency\\\\\\\_degradation()` with window\_size=None
4. Generates embedded FFT analysis plots
5. Saves results to text file with formatted tables and fit equations

\---

### Option Menu Change Handlers

#### 13-16. **Option Callback Functions** \[Lines 1081-1100]

**Functions**:

* `option\\\\\\\_changed\\\\\\\_SUBSTANCE()` - Logs substance selection
* `option\\\\\\\_changed\\\\\\\_TIA()` - Logs TIA gain selection
* `option\\\\\\\_changed\\\\\\\_OPMODE()` - Logs operating mode selection
* `option\\\\\\\_changed\\\\\\\_METHOD()` - Logs measurement method selection

**Mechanism**: Variable tracing with `.trace("w", callback)` triggers callbacks on write

\---

## Measurement Methods

### 1\. Cyclic Voltammetry (CV)

**Principle**: Apply linearly varying voltage, measure resulting current

**Parameters**:

* **Voltage Range**: -0.6 V to +0.6 V (27 forward, 27 reverse)
* **Scan Rate**: 50 mV/s
* **Points**: 54 total (27 forward + 27 reverse)
* **Measurement Interval**: 1 second between points

**Advantages**:

* Identifies redox potential
* Determines electron transfer mechanisms
* Good for catechol with broad oxidation peak

**Output**:

* Forward scan: Oxidation current as voltage increases
* Reverse scan: Reduction current as voltage decreases
* Peak current indicates analyte concentration

### 2\. Chronoamperometry (CA)

**Principle**: Apply fixed voltage, measure current transient over time

**Parameters**:

* **Applied Voltage**: 0 V (fixed bias at -0.6 V)
* **Duration**: 400 seconds
* **Sampling Interval**: 1 second per point
* **Analysis Window**: Points 50-350 (remove edge effects)

**Advantages**:

* Direct steady-state current measurement
* Longer measurement provides stability
* Less sensitive to surface effects
* Better for real-time monitoring

**Output**:

* Steady-state current plateau
* Exponential decay from initial transient
* Maximum current used for concentration calculation

\---

## Data Processing Pipeline

```
Raw ADC Data (0-65535)
↓
\\\[Voltage Calculation]
1.25V ≤ Voltage ≤ 5V
↓
\\\[Current Calculation via Ohm's Law]
I = Offset + (V - Vref/2) / TIA
↓
\\\[Optional: FFT Denoising]
Hanning Window
Frequency Analysis
Low-Pass Filtering
Inverse FFT
Peak Rescaling
↓
\\\[Signal Quality Analysis]
Peak-to-RMS Calculation
Frequency Degradation (if multiple freqs)
Inverse Log Curve Fitting
↓
\\\[CSV Export \\\& Visualization]
Forward/Reverse Scans (CV)
Time Series (CA)
Real-time current.txt update
↓
\\\[Concentration Calculation]
Linear or Logarithmic Calibration
↓
\\\[Safety Classification]
Safe / Health Risk / Toxic
```

\---

## Chronoamperometry Planner

A dedicated planning workflow in the development interface (`test\\\\\\\_INTEGRATEDFULL.py`) that answers the three operational questions of a chronoamperometric standard-addition run. It is opened from the new **"Chronoamperometry Planner"** menu action, which launches a dedicated input panel. All three computations are implemented as standalone, side-effect-free functions; **no existing function was modified** to add them.

### Operator inputs

The panel accepts: the **ascending list of desired concentrations** (comma-separated, µM), the **initial volume** (mL), the **stock concentration** (µM), the **background concentration** (0 for clean buffer), the **mixing time t\_mix** (s; 30 s is a typical bench default for a small, well-stirred cell), and the **safety margin** (default 1.2).

### Q1 — "How much volume do I need to add at each step?"

#### **`compute\\\\\\\_stock\\\\\\\_addition\\\\\\\_schedule(target\\\\\\\_concentrations, initial\\\\\\\_volume, stock\\\\\\\_concentration, initial\\\\\\\_concentration=0.0)`** \[NEW]





The dilution calculator(that uses a derived recursive formula) is exposed to the operator through a dedicated planner in the development interface. The operator types the ascending list of desired concentrations, the initial volume, the stock concentration, and the background concentration(0 for clean buffer). For each step the interface returns the exact stock aliquot to pipette, the running total volume, and the total stock consumed.

The concentration actually reached at each step is re-derived from the pipetted volumes and displayed alongside the target, so any arithmetic or pipetting inconsistency is visible at a glance. The only physical constraint surfaced to the user is Stock concentration > Target concentration: a target cannot be reached by spiking in a stock that is not more concentrated than that target, and the interface refuses the schedule with an explanatory message rather than returning a negative or infinite volume. This is the concentrate-only workflow appropriate to catechol standard addition, where the analyte level is raised step by step.

Worked example (Initial Volume = 10 mL, Stock conc. = 1000 uM, Initial conc = 0)

step 1  ->  add 0.0503 mL   total 10.0503 mL   -> 5 uM

step 2  ->  add 0.0508 mL   total 10.1010 mL   -> 10 uM

step 3  ->  add 0.1031 mL   total 10.2041 mL   -> 20 uM

step 4  ->  add 0.1052 mL   total 10.3093 mL   -> 30 uM

```
For each step it returns the exact stock aliquot to pipette, the running total volume, and the total stock consumed. The concentration actually reached at each step is **re-derived from the pipetted volumes** (mole balance) and displayed alongside the target, so any arithmetic or pipetting inconsistency is visible at a glance.
**Physical constraint surfaced to the user**: `Stock concentration > Target concentration`. A target cannot be reached by spiking in a stock that is not more concentrated than that target; the interface **refuses the schedule with an explanatory message** rather than returning a negative or infinite volume. This is the concentrate-only workflow appropriate to catechol standard addition. Non-ascending target lists and non-positive volumes are likewise refused with explanations.
**Worked example** (Initial Volume = 10 mL, Stock = 1000 µM, Background = 0):
```

step 1 -> add 0.0503 mL   total 10.0503 mL   -> 5 uM
step 2 -> add 0.0508 mL   total 10.1010 mL   -> 10 uM
step 3 -> add 0.1031 mL   total 10.2041 mL   -> 20 uM
step 4 -> add 0.1052 mL   total 10.3093 mL   -> 30 uM

```
Q2 — "How much time do I need to wait before making a measurement?"
**`compute\\\\\\\_stabilization\\\\\\\_time(current, time\\\\\\\_axis=None, tolerance=0.02, sustained\\\\\\\_samples=5, guard\\\\\\\_fraction=0.05, savgol\\\\\\\_window=21, savgol\\\\\\\_polyorder=3)`** \[NEW]
A reading is only meaningful once the faradaic transient has decayed onto its steady-state plateau. The planner decides this **from the current-versus-time record, not a fixed timer**:
```

stable when  d²i/dt² -> 0   AND   di/dt -> 0

```
A naive "second derivative equals zero" test is insufficient on its own — an inflection point on the decaying transient also has zero curvature while the slope is still steep. The function therefore requires **both** the normalised curvature **and** the normalised slope to fall below a small fraction of their own peak magnitudes (tolerance 2%) and to remain there for a sustained window (5 consecutive samples). Both derivatives come from a **Savitzky–Golay filter** (smooth + differentiate in one pass), and an initial **guard region** (first 5% of the record) is skipped so the large opening transient is never mistaken for a plateau. The first sample satisfying the joint criterion is reported as the stabilisation time. If no sustained plateau is found, the planner reports that the transient **has not settled** and recommends a longer measurement or a looser threshold rather than returning a premature value.
If no `time\\\\\\\_axis` is given, a uniform 1 s spacing is assumed — matching the Fixed Voltage sweep (400 samples, 1 s apart).
Q3 — "How long do I wait before adding stock to increase concentration?"
**`compute\\\\\\\_time\\\\\\\_between\\\\\\\_measurements(t\\\\\\\_stabilization, t\\\\\\\_mix=30.0, safety\\\\\\\_margin=1.2)`** \[NEW]
Two independent processes must complete before the next spike: the injected stock must **homogenise** (t\_mix, operator-entered) and the electrode must **re-equilibrate** (exactly the stabilisation time of the resulting transient, from Q2). With a conservative safety margin:
```

Time between measurements = safety\_margin \* (t\_stabilization + t\_mix)

```
This prevents premature spikes (which would corrupt the next reading) and avoids needlessly long waits. Margins below 1.0 are refused.
UI flow
**Menu → Chronoamperometry Planner** opens the input panel.
**Compute Volume Schedule** — available immediately from the typed inputs (Q1 table: add / total / target / achieved, plus total stock consumed).
**Analyze Last CA Transient** — enabled in practice once a **Fixed Voltage** (chronoamperometry) run has filled `DATA\\\\\\\_fv`; it reports the stabilisation time (Q2) and the recommended wait before the next spike (Q3). If no transient exists yet, the panel says so instead of guessing.
\---

Raspberry Pi 3B+ Specific Considerations
GPIO Pinout
* **Pin 11**: RED LED (Status indicator)
* **Pin 13**: GREEN LED (Ready indicator)
* **I2C**: Standard for LMP91000 communication
Performance Notes
* **Processing Speed**: FFT operations on \~60 points @ 250 kHz sampling
* **Memory**: Python/Tkinter footprint minimal for Pi 3B+
* **Power**: GPIO control keeps sensor in sleep when idle
* **Thermal**: Long measurements (400s CA) may generate heat
Interface Libraries
* **RPi.GPIO**: GPIO control (must run as root/sudo)
* **Tkinter**: Native to Raspberry Pi OS
* **CustomTkinter**: Lightweight modern GUI (available via pip)
* **SciPy/NumPy**: Signal processing (pre-installed most distributions)
\---
Configuration Files
`var.py` (External Import)
Contains all sensor register definitions:
* TIA register values (TIACN\_TIAG\_\*\_RLOAD\_010)
* Operating mode registers (MODECN\_OP\_MODE\_\*)
* Reference voltage bias values (REFCN\_BIAS\_N/P\[0-13])
* Communication lock/unlock commands (LOCKWR, LOCKRO)
`settings.py` (External Import)
Contains:
* FULL\_SWEEP array (54-point voltage sweep)
* Register write/read/init functions
* I2C device address and parameters
* ADC reading function (readadc())
\---
Calibration Curve Data
Catechol Calibration
```

Substance: Catechol
Molecular Weight: 110.1 g/mol
Calibration: Linear (default) OR Piecewise Linear (optional, 3 segments)

\--- LINEAR (LINEAR\\\_COEFFS) ---
Slope (m):      0.1499 µA/µM
Intercept (b): -0.4881 µA
Validated range: 0 - 500 µM
Equation: C (µM) = (I - (-0.4881)) / 0.1499

\--- PIECEWISE (CALIBRATION\\\_SEGMENTS) ---
Seg 1:    0 -  100 µM   m = 0.1499   b = -0.4881    current  -0.4881 -> 14.5531 µA
Seg 2:  100 -  500 µM   m = 0.1245   b =  2.1543    current  14.5531 -> 61.2599 µA
Seg 3:  500 - 2000 µM   m = 0.0987   b =  8.7654    current  61.2599 -> 206.1654 µA

Equation: C\\\_measured = (I - b\\\_segment) / m\\\_segment
C\\\_true     = C\\\_measured x dilution\\\_factor

Outside the calibrated current window -> OUT OF RANGE (no value returned; dilute the sample)

```
Ascorbic Acid / Progesterone
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
\---
Modern UI Application (`modern app interface.py`)
Page Structure
WelcomePage
* Introduction screen
* Project title and description
* EPA compliance note for catechol exposure limits
SamplePage
* Verification of sample insertion
* User acknowledgment before proceeding
BufferPage
* pH buffer requirement (ABS+PBS)
* pH validation: accepted within **6.5 ± 0.1** (a tolerance band, not exact float equality -
the previous `ph == 6.5` check could only be satisfied by typing exactly "6.5")
* Prevents measurement with incorrect pH
CalibrationPage
* Live calibration curve display (calibration.png)
* Real-time current reading every 2 seconds
* **Calibration method selector**: `Piecewise Linear` (default) / `Linear`. Switching re-evaluates
the next reading immediately; no restart needed.
* **Dilution factor box + Apply button**: the reported concentration is
`measured concentration x dilution factor`. Default is 1 (neat sample). Invalid or
non-positive entries are rejected with an error dialog.
* Concentration is computed by the shared `get\\\\\\\_concentration\\\\\\\_from\\\\\\\_current()` imported from
`test\\\\\\\_INTEGRATEDFULL.py` - this file contains **no calibration constants of its own**, so the
touchscreen app and the development interface can never drift apart.
* Safety classification display (applied to the **true**, dilution-corrected concentration):
* **Green** `#388e3c`: Concentration < 10 µM (SAFE)
* **Orange** `#f57c00`: 10 µM < Concentration < 181 µM (HEALTH RISK)
* **Red** `#d32f2f`: Concentration > 181 µM (UNSAFE TOXIC)
* **Blue-grey** `#455a64`: OUT OF RANGE - no verdict is given. The panel displays the dilution
instructions and the calibrated current window, and prompts the operator to dilute and enter
the dilution factor.
Safety Thresholds
```python
ACUTE\\\\\\\_LIMIT = 10.0 µM     # Short-term exposure limit
CHRONIC\\\\\\\_LIMIT = 181.0 µM  # Long-term exposure limit
```
Auto-Read Loop [Lines 250-278]
Reads current.txt every 2000 ms (2 seconds)
Non-blocking UI updates via Tkinter's .after() method
Handles file not found and invalid data errors gracefully
---
Key Mathematical Formulas
1. Voltage to Current (Transimpedance)
```
I (µA) = Baseline\\\\\\\_Offset + ((V - Vref/2) / R\\\\\\\_TIA) × 10⁶

Where:
- Baseline\\\\\\\_Offset = 571.59 µA (dark current)
- V = voltage from ADC (1.25 to 5.0 V)
- Vref = 2.5 V (reference voltage)
- R\\\\\\\_TIA = TIA resistance (2.75 kΩ to 350 kΩ)
```
2. FFT-based Denoising
```
Denoised\\\\\\\_Signal = IFFT(FFT(Windowed\\\\\\\_Signal) × LowPassFilter)

Where:
- Windowed\\\\\\\_Signal = Original\\\\\\\_Signal × Hanning\\\\\\\_Window
- LowPassFilter = 1 if |f| < f\\\\\\\_cutoff, else 0
- f\\\\\\\_cutoff = Automatic (5% threshold) or Fallback (30% Nyquist)
```
3. Peak-to-RMS Ratio
```
Peak\\\\\\\_to\\\\\\\_RMS = max(|I|) / sqrt(mean(I²))

Quality Assessment:
- > 5: Excellent (noise < 20% of peak)
- 3-5: Good (noise 20-33% of peak)
- < 3: Poor (noise > 33% of peak)
```
4. Frequency Degradation Fit
```
Peak\\\\\\\_to\\\\\\\_RMS(f) = a + b × ln(f)

Parameters:
- a: Intercept (peak sharpness at reference frequency)
- b: Slope (decay rate, typically negative)
- R²: Goodness of fit (0 to 1)
```
5. Concentration from Current
```
For Catechol (Linear, default coefficients, validated 0-500 µM):
C (µM) = (I - b) / m = (I + 0.4881) / 0.1499

For Catechol (Piecewise Linear):
  1. select the segment k whose CURRENT interval contains I:
         i\\\\\\\_lo(k) <= I <= i\\\\\\\_hi(k)
     where the interval edges come from i = m\\\\\\\*C + b evaluated at the segment's
     concentration bounds, with adjacent segments joined at the MIDPOINT of their
     boundary currents (this removes gaps and overlaps between independently fitted lines)
  2. C\\\\\\\_measured (µM) = (I - b\\\\\\\_k) / m\\\\\\\_k
  3. if no segment contains I  ->  OUT OF RANGE (no value returned)

Dilution correction (both modes):
C\\\\\\\_true (µM) = C\\\\\\\_measured x dilution\\\\\\\_factor

For Ascorbic Acid (Log):
log₁₀(M) = (log₁₀(I) - 4.1644) / 0.9033
C (M) = 10^\\\\\\\[log₁₀(I) - 4.1644] / 0.9033
```
---
Troubleshooting Guide
Common Issues
1. Voltage Out of Bounds (< 1.25 V or > 5.0 V)
Cause: ADC read error or sensor disconnection
Solution:
Verify I2C connection
Check ADC firmware
Confirm reference voltage circuit
2. Negative Current Values
Cause: Dark current offset miscalibration
Solution:
Recalibrate offset value (571.59)
Measure zero-bias current with no analyte
Update offset accordingly
3. FFT Denoising Not Removing Noise
Cause: Noise frequency within signal band
Solution:
Increase sampling frequency (if hardware capable)
Adjust threshold from 5% to 10%
Reduce scan rate for smoother signal
4. Peak-to-RMS Ratio Always Low
Cause: Sensor under-damped or TIA gain too low
Solution:
Increase TIA gain (try 14 kΩ or higher)
Reduce measurement temperature
Check sensor surface for contamination
5. pH Validation Fails
Cause: Buffer not yet equilibrated
Solution:
Wait longer after buffer addition
Stir solution thoroughly
Use calibrated pH meter
Note: the app accepts pH 6.5 +/- 0.1, so a reading of 6.47 or 6.53 will pass
6. Result Panel Shows "OUT OF RANGE" (blue-grey)
Cause: The measured current lies outside the calibrated current window
(-0.4881 to 206.1654 uA for piecewise catechol; 0-500 uM equivalent for linear mode)
Solution:
Dilute the sample by a known factor and re-measure
Enter the dilution factor in the box on the CalibrationPage and press Apply
Repeat until the current lands inside the window; stacked dilution factors multiply
If the current is below the window, the sample may be below the detection limit, or the
TIA gain is too low - raise the gain rather than diluting
If you are in Linear mode and the concentration exceeds 500 uM, switch to Piecewise Linear,
which is calibrated up to 2000 uM
7. Concentration Steps Slightly at a Segment Boundary
Cause: The three segments are independently fitted, so the piecewise curve is not continuous
at the joins. The breakpoint sits at the midpoint of the two boundary currents, so a small step
in reported concentration is expected there.
Solution:
Expected behaviour, not a bug
To remove it, refit with a continuous (knot-constrained) piecewise model
---
References
LMP91000: Electrochemical Sensor AFE Datasheet(https://www.alldatasheet.com/datasheet-pdf/pdf/2195217/TI2/LMP91000.html)
FFT Denoising: Oppenheim & Schafer "Discrete-Time Signal Processing"
Cyclic Voltammetry: Bard & Faulkner "Electrochemical Methods"
Chronoamperometry: Cottrell Equation for transient current decay
Catechol EPA Limits: Environmental Protection Agency Industrial Guide
---
Modified Code from
Project: Design and development of a portable, low-cost and customizable sensor platform based on a potentiostat mainly integrated by commercial off-the-shelf (COTS) electronic components.
Author: Juan Poveda
Institution: Technical University of Cartagena
Status: Complete
For questions or improvements, refer to the GitHub repository issues and discussions.
---
Changelog - Piecewise Calibration Integration
Added
`CALIBRATION\\\\\\\_SEGMENTS` (concentration-domain segments) and `LINEAR\\\\\\\_COEFFS` (single-line fallback
with a validated range) in `test\\\\\\\_INTEGRATEDFULL.py`
`build\\\\\\\_current\\\\\\\_breakpoints()` - converts concentration-domain segments into non-overlapping
current-domain intervals, joining neighbours at the midpoint of their boundary currents
`calibration\\\\\\\_current\\\\\\\_window()` - returns the (i_min, i_max) window a calibration can interpret
`OUT\\\\\\\_OF\\\\\\\_RANGE\\\\\\\_MESSAGE` - the single canonical dilution instruction, shared by both interfaces
Development interface: "Piecewise calibration" checkbox and a Dilution factor entry
(`get\\\\\\\_dilution\\\\\\\_factor()`), wired into `startCV()`
Touchscreen app: calibration method segmented button and a Dilution factor box with an
Apply button, plus a dedicated OUT OF RANGE state


Changelog - Chronoamperometry Planner (Section 6.2)
Added
`compute\\\\\\\_stock\\\\\\\_addition\\\\\\\_schedule()` - recursive stock-aliquot schedule with achieved-concentration
re-derivation and Stock > Target refusal (Section 6.2.1)
`compute\\\\\\\_stabilization\\\\\\\_time()` - Savitzky-Golay joint slope+curvature plateau detector with 2%
tolerance, 5-sample sustained window and 5% guard region (Section 6.2.2)
`compute\\\\\\\_time\\\\\\\_between\\\\\\\_measurements()` - safety_margin x (t_stabilisation + t_mix) spike-timing
rule (Section 6.2.3)
`openChronoPlanner()` + "Chronoamperometry Planner" menu action - dedicated input panel
surfacing all three computations (Section 6.2.4)
Changed / Removed
Nothing. All existing functions, constants and widgets are byte-identical; the additions are
purely new code inserted before the grid configuration block.
