import numpy as np

# Constants used in the program
SAMPLE_FREQ = 25  # The sampling frequency of the sensor in Hz (samples per second)
MA_SIZE = 4       # The size of the moving average window
SECS_DATA = 2     # Number of seconds of data to collect
BUFFER_SIZE = SAMPLE_FREQ * SECS_DATA  # The total buffer size for collected data

# Function to calculate HR, IPM, HRSTD, and RMSSD
def calc_hr_and_ipm(ir_data):
    """
    By detecting peaks of the PPG cycle, calculate:
      - Heart Rate (HR)
      - Impulse Per Minute (IPM)
      - Heart Rate Standard Deviation (HRSTD)
      - Root Mean Square of Successive Differences (RMSSD)
    """
    # Compute the mean of the IR data to find the DC component
    ir_mean = int(np.mean(ir_data))

    # Remove DC mean and invert the signal to detect valleys as peaks
    x = -1 * (np.array(ir_data) - ir_mean)

    # Apply a 4-point moving average to smooth the signal
    for i in range(x.shape[0] - MA_SIZE):
        x[i] = np.sum(x[i:i+MA_SIZE]) / MA_SIZE

    # Calculate the threshold for peak detection
    n_th = int(np.mean(x))
    n_th = 30 if n_th < 30 else n_th  # Minimum threshold allowed
    n_th = 60 if n_th > 60 else n_th  # Maximum threshold allowed

    # Detect peaks in the signal
    ir_valley_locs, n_peaks = find_peaks(x, BUFFER_SIZE, n_th, 4, 15)

    # Calculate Heart Rate (HR) and R-R intervals
    peak_intervals = []
    hr = -999
    hr_valid = False
    if n_peaks >= 2:
        for i in range(1, n_peaks):
            interval = (ir_valley_locs[i] - ir_valley_locs[i-1]) / SAMPLE_FREQ  # Convert to seconds
            peak_intervals.append(interval)
        
        # Average interval to calculate HR
        avg_interval = np.mean(peak_intervals)
        hr = int(60 / avg_interval)  # Convert interval to beats per minute
        hr_valid = True

    # Calculate Impulse Per Minute (IPM)
    ipm = (n_peaks / SECS_DATA) * 60  # Convert impulses per `SECS_DATA` to per minute

    # Calculate HRSTD (Heart Rate Standard Deviation)
    hrstd = np.std(peak_intervals) * 60 if len(peak_intervals) > 1 else -999  # in bpm

    # Calculate RMSSD (Root Mean Square of Successive Differences)
    if len(peak_intervals) > 1:
        diff_intervals = np.diff(peak_intervals)  # Successive differences
        rmssd = np.sqrt(np.mean(diff_intervals ** 2)) * 60  # in bpm
    else:
        rmssd = -999

    return hr, hr_valid, ipm, hrstd, rmssd


# # Function to calculate heart rate (HR) from infrared (IR) sensor data
# def calc_hr(ir_data):
#     """
#     Calculate heart rate using PPG (Photoplethysmogram) data from the infrared sensor.
    
#     This function detects peaks in the IR data to calculate the intervals between peaks,
#     which represent the heartbeats, and then estimates the heart rate.
    
#     Parameters:
#         ir_data (np.array): Array of infrared data from the MAX30102 sensor.
    
#     Returns:
#         hr (int): Estimated heart rate in beats per minute.
#         hr_valid (bool): Indicator of whether the heart rate calculation is valid.
#     """
    
#     # Step 1: Calculate the mean value (DC component) of the IR data
#     ir_mean = int(np.mean(ir_data))
    
#     # Step 2: Remove the DC component and invert the signal to make valleys become peaks
#     x = -1 * (np.array(ir_data) - ir_mean)

#     # Step 3: Apply a 4-point moving average filter to smooth the data
#     # This reduces noise and helps in peak detection
#     for i in range(x.shape[0] - MA_SIZE):
#         x[i] = np.sum(x[i:i+MA_SIZE]) / MA_SIZE

#     # Step 4: Calculate the threshold for peak detection
#     # Threshold is used to distinguish between peaks and non-peaks
#     n_th = int(np.mean(x))
#     n_th = 30 if n_th < 30 else n_th  # Minimum threshold value is 30
#     n_th = 60 if n_th > 60 else n_th  # Maximum threshold value is 60

#     # Step 5: Detect peaks in the filtered data
#     # Peaks represent the valleys in the original signal (heartbeats)
#     ir_valley_locs, n_peaks = find_peaks(x, BUFFER_SIZE, n_th, 4, 15)

#     # Step 6: Calculate the heart rate if there are enough peaks detected
#     peak_interval_sum = 0
#     if n_peaks >= 2:
#         # Compute the average time interval between consecutive peaks
#         for i in range(1, n_peaks):
#             peak_interval_sum += (ir_valley_locs[i] - ir_valley_locs[i-1])
#         peak_interval_sum = int(peak_interval_sum / (n_peaks - 1))
        
#         # Calculate heart rate in beats per minute
#         hr = int(SAMPLE_FREQ * 60 / peak_interval_sum)
#         hr_valid = True  # Heart rate calculation is valid
#     else:
#         hr = -999  # Indicates an invalid heart rate due to insufficient peaks
#         hr_valid = False

#     return hr, hr_valid

# Function to find peaks in the IR data
def find_peaks(x, size, min_height, min_dist, max_num):
    """
    Find peaks in the IR data.
    
    Parameters:
        x (np.array): Array of filtered IR data.
        size (int): Size of the data array.
        min_height (int): Minimum height for a peak to be considered.
        min_dist (int): Minimum distance between consecutive peaks.
        max_num (int): Maximum number of peaks to detect.
    
    Returns:
        ir_valley_locs (list): List of indices where peaks are detected.
        n_peaks (int): Number of peaks detected.
    """
    
    # Step 1: Find all peaks above the minimum height
    ir_valley_locs, n_peaks = find_peaks_above_min_height(x, size, min_height, max_num)
    
    # Step 2: Remove peaks that are too close to each other
    ir_valley_locs, n_peaks = remove_close_peaks(n_peaks, ir_valley_locs, x, min_dist)

    # Ensure the number of detected peaks does not exceed the maximum allowed
    n_peaks = min([n_peaks, max_num])

    return ir_valley_locs, n_peaks

# Function to find peaks that exceed a minimum height
def find_peaks_above_min_height(x, size, min_height, max_num):
    """
    Identify peaks in the data that exceed a specified minimum height.
    
    Parameters:
        x (np.array): Array of filtered IR data.
        size (int): Size of the data array.
        min_height (int): Minimum height for a peak to be considered.
        max_num (int): Maximum number of peaks to detect.
    
    Returns:
        ir_valley_locs (list): List of indices where peaks are detected.
        n_peaks (int): Number of peaks detected.
    """
    
    i = 0
    n_peaks = 0
    ir_valley_locs = []
    
    # Iterate through the data to find peaks
    while i < size - 1:
        if x[i] > min_height and x[i] > x[i-1]:  # Detect the start of a potential peak
            n_width = 1
            
            # Handle flat peaks by checking if the value remains the same
            while i + n_width < size - 1 and x[i] == x[i+n_width]:
                n_width += 1
                
            # Confirm a peak if the value drops after the flat section
            if x[i] > x[i+n_width] and n_peaks < max_num:
                ir_valley_locs.append(i)  # Record the peak location
                n_peaks += 1
                i += n_width + 1
            else:
                i += n_width
        else:
            i += 1

    return ir_valley_locs, n_peaks

# Function to remove peaks that are too close to each other
def remove_close_peaks(n_peaks, ir_valley_locs, x, min_dist):
    """
    Remove peaks that are closer than the specified minimum distance.
    
    Parameters:
        n_peaks (int): Initial number of peaks detected.
        ir_valley_locs (list): List of peak indices.
        x (np.array): Array of filtered IR data.
        min_dist (int): Minimum allowable distance between peaks.
    
    Returns:
        sorted_indices (list): List of filtered peak indices.
        n_peaks (int): Updated number of peaks after filtering.
    """
    
    # Sort peaks by height (from highest to lowest)
    sorted_indices = sorted(ir_valley_locs, key=lambda i: x[i])
    sorted_indices.reverse()

    i = -1
    while i < n_peaks:
        old_n_peaks = n_peaks
        n_peaks = i + 1
        j = i + 1
        
        # Remove peaks that are too close to the current peak
        while j < old_n_peaks:
            n_dist = (sorted_indices[j] - sorted_indices[i]) if i != -1 else (sorted_indices[j] + 1)
            if n_dist > min_dist or n_dist < -1 * min_dist:
                sorted_indices[n_peaks] = sorted_indices[j]
                n_peaks += 1
            j += 1
        i += 1

    # Sort the remaining peaks in ascending order of indices
    sorted_indices[:n_peaks] = sorted(sorted_indices[:n_peaks])

    return sorted_indices, n_peaks
