import max30102
import hrdata
import numpy as np
from scipy.signal import butter, filtfilt, find_peaks
from collections import deque
import json
from bluetooth_sender import BluetoothSender
from time import sleep, time

sensor = max30102.MAX30102()

# Sampling frequency (Hz)
fs = 25
window_size = 100  # Sliding window size (e.g., 5 seconds at 100 Hz) 4s
output_interval = 0.5  # Output metrics every 500 ms

# Sliding window buffer for IR data
# ir_buffer = deque(maxlen=window_size)

print("Starting continuous heart rate monitoring...")
last_output_time = time()

# Use receiver's Bluetooth MAC address
SERVER_ADDRESS = "2C:CF:67:03:0B:FE"
sender = BluetoothSender(SERVER_ADDRESS)

try:
    sender.connect()
    
    # 100 samples are read and used for HR calculation in a single loop
    while True:
        ir_data = sensor.read_sequential(amount=window_size)
        # ir_buffer.extend(ir_data)

        # Process and output metrics at regular intervals
        if time() - last_output_time >= output_interval:
            # if len(ir_buffer) >= window_size:
                # Convert deque to numpy array
            ir_data_window = np.array(ir_data)

            # Calculate heart rate metrics
            hr, ipm, hrstd, rmssd, ir_filtered = hrdata.calculate_hr_metrics(ir_data_window, fs)
            if hr is not None:
                print(f"Heart Rate (bpm): {hr:.2f}")
                print(f"Impulses per minute: {ipm:.2f}")
                print(f"HRSTD: {hrstd:.2f}")
                print(f"RMSSD: {rmssd:.2f}")
                print(f"Filtered Data: {ir_filtered[:10]} ...")

                # Round filtered data to reduce precision
                ir_filtered_rounded = np.round(ir_filtered, decimals=2)

                data_to_send = {
                    "raw_value": ir_filtered_rounded.tolist(),
                    "bpm": round(hr, 2),
                    "ipm": round(ipm,2),
                    "hrstd": round(hrstd, 2),
                    "rmssd": round(rmssd, 2)
                }
                print(data_to_send)
                # Send data over bluetooth
                json_data_to_send = json.dumps(data_to_send)
                sender.send_data(json_data_to_send)
            else:
                print("Not enough peaks detected. Adjust filter or check signal.")

            # Update the last output time
            last_output_time = time()

        # Sleep briefly to prevent excessive CPU usage
        sleep(0.01)


finally:
        sender.disconnect()