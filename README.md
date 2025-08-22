# Bluetooth Pulse Monitoring (Raspberry Pi)

Two-Raspberry-Pi demo for real-time heart rate monitoring with a MAX30102 PPG sensor. The sender Pi reads IR data, computes metrics (BPM, IPM, HRSTD, RMSSD), and streams JSON over Bluetooth RFCOMM to a receiver Pi that displays a live dashboard.

- Demo video: https://youtu.be/x7xXRoa4eDU
- Repository: https://github.com/lanhp-vn/bluetooth-pulse-monitoring-rpi5

## Project structure
- `source_codes/heartrate_sender-master/`
  - `main.py`: read MAX30102, compute metrics, send JSON via Bluetooth
  - `max30102.py`: MAX30102 I2C driver (uses `smbus` and `gpiod` interrupt)
  - `hrdata.py`: signal processing and metrics
  - `bluetooth_sender_test.py`: manual test client
- `source_codes/heartrate_receiver-main/`
  - `bluetooth_receiver.py`: RFCOMM server to accept data
  - `display.py`: Tkinter + Matplotlib live metrics and waveform

## Requirements
Sender (sensor Pi):
- Raspberry Pi OS, Python 3
- Hardware: MAX30102 via I2C, one GPIO interrupt
- Packages: `smbus`, `gpiod`, `numpy`, `scipy`, `pybluez`

Receiver (display Pi):
- Python 3 with `pybluez`, `tkinter`, `matplotlib`

Enable Bluetooth: `sudo hciconfig hci0 up`.

## Run
1) Receiver (display):
```bash
cd source_codes/heartrate_receiver-main
python display.py
```
Note the printed Server MAC Address.

2) Sender (sensor):
- Edit `source_codes/heartrate_sender-master/main.py` and set `SERVER_ADDRESS` to the receiver MAC.
```bash
cd source_codes/heartrate_sender-master
python main.py
```

You should see BPM, IPM, HRSTD, RMSSD and a live IR plot on the receiver.

## Notes
- Default sampling rate: 25 Hz (adjust in code if needed).
- If connection fails, pair/trust devices and restart Bluetooth (`hciconfig hci0 down & hciconfig hci0 up`).
