import numpy as np
from scipy.signal import butter, filtfilt, find_peaks
from collections import deque
from max30102 import MAX30102
from time import sleep, time

# Bandpass filter function
def bandpass_filter(data, fs, lowcut=0.5, highcut=3.0):
    nyquist = 0.5 * fs
    low = lowcut / nyquist
    high = highcut / nyquist
    b, a = butter(1, [low, high], btype="band")
    return filtfilt(b, a, data)

# Calculate RMSSD
def calculate_rmssd(ibi):
    diff = np.diff(ibi)  # Successive differences of IBIs
    squared_diff = diff ** 2
    rmssd = np.sqrt(np.mean(squared_diff))
    return rmssd

# Function to calculate HR metrics
def calculate_hr_metrics(ir_data, fs):
    ir_filtered = bandpass_filter(ir_data, fs=fs)

    # Detect peaks
    peaks, _ = find_peaks(ir_filtered, distance=fs / 2.5)  # Minimum distance for 150 bpm
    if len(peaks) < 2:
        return None, None, None, None, None

    # Calculate IBI (in ms)
    ibi = np.diff(peaks) / fs * 1000  # Convert from samples to milliseconds
    avg_ibi = np.mean(ibi)  # Average IBI

    # Calculate metrics
    hr = 60 / (avg_ibi / 1000)  # Convert mean IBI to bpm
    hrstd = np.std(60 / (ibi / 1000))  # Standard deviation of HR values
    rmssd = calculate_rmssd(ibi)  # Root Mean Square of Successive Differences

    # Calculate IPM (Impulses Per Minute)
    window_duration_minutes = len(ir_filtered) / (fs * 60)  # Window duration in minutes
    ipm = len(peaks) / window_duration_minutes

    return hr, ipm, hrstd, rmssd, ir_filtered

# Main script for continuous monitoring
if __name__ == "__main__":
    # Initialize the sensor
    sensor = MAX30102()

    # Sampling frequency (Hz)
    fs = 25  # Confirm the sensor's sampling rate
    window_size = 125  # Sliding window size (e.g., 5 seconds at 100 Hz)
    output_interval = 0.04  # Output metrics every 40 ms

    # Sliding window buffer for IR data
    ir_buffer = deque(maxlen=window_size)

    print("Starting continuous heart rate monitoring...")
    last_output_time = time()

    while True:
        # Use read_sequential to read multiple samples
        ir_data = sensor.read_sequential(amount=100)
        ir_buffer.extend(ir_data)

        # Process and output metrics at regular intervals
        if time() - last_output_time >= output_interval:
            if len(ir_buffer) >= window_size:
                # Convert deque to numpy array
                ir_data_window = np.array(ir_buffer)

                # Calculate heart rate metrics
                hr, ipm, hrstd, rmssd, ir_filtered = calculate_hr_metrics(ir_data_window, fs)
                if hr is not None:
                    print(f"Heart Rate (bpm): {hr:.2f}")
                    print(f"Impulses per minute: {ipm:.2f}")
                    print(f"HRSTD: {hrstd:.2f}")
                    print(f"RMSSD: {rmssd:.2f}")
                    print(f"Filtered Data: {ir_filtered} ...")
                else:
                    print("Not enough peaks detected. Adjust filter or check signal.")

            # Update the last output time
            last_output_time = time()

        # Sleep briefly to prevent excessive CPU usage
        sleep(0.01)
