import bluetooth
import subprocess
import atexit

class BluetoothSender:
    def __init__(self, server_address, port=1):
        """
        Initialize the BluetoothSender object.

        Args:
            server_address (str): MAC address of the server.
            port (int): RFCOMM port to connect to. Default is 1.
        """
        self.server_address = server_address
        self.port = port
        self.client_sock = None

    def enable_bluetooth(self):
        """Enable the Bluetooth device."""
        try:
            subprocess.run(["sudo", "hciconfig", "hci0", "up"], check=True)
            print("Bluetooth device hci0 is now up.")
        except subprocess.CalledProcessError:
            print("Failed to turn on Bluetooth device hci0.")

    def disable_bluetooth(self):
        """Disable the Bluetooth device."""
        try:
            subprocess.run(["sudo", "hciconfig", "hci0", "down"], check=True)
            print("Bluetooth device hci0 is now down.")
        except subprocess.CalledProcessError:
            print("Failed to turn off Bluetooth device hci0.")

    def connect(self):
        """Establish a connection to the server."""
        self.enable_bluetooth()
        # Set up a Bluetooth RFCOMM client socket
        self.client_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        try:
            # Connect to the server using the server address and port
            self.client_sock.connect((self.server_address, self.port))
            print(f"Connected to server at {self.server_address} on port {self.port}", flush=True)
        except bluetooth.BluetoothError as e:
            print(f"Failed to connect to the server: {e}")
            self.client_sock = None

    def send_data(self, data):
        """
        Send data to the server.

        Args:
            data (str): Data to send.
        """
        if self.client_sock:
            try:
                self.client_sock.send(data)
                print(f"Sent: {data}", flush=True)
            except Exception as e:
                print(f"An error occurred while sending data: {e}")
        else:
            print("No active connection. Unable to send data.")

    def disconnect(self):
        """Disconnect from the server and clean up."""
        if self.client_sock:
            try:
                self.client_sock.close()
                print("Disconnected from the server", flush=True)
            except Exception as e:
                print(f"Error while closing the socket: {e}")
        self.disable_bluetooth()

# Register the disable_bluetooth function to run at script exit
atexit.register(BluetoothSender.disable_bluetooth, BluetoothSender)

# Example usage
if __name__ == "__main__":
    # Use receiver's Bluetooth MAC address
    SERVER_ADDRESS = "2C:CF:67:04:9D:D7"
    sender = BluetoothSender(SERVER_ADDRESS)

    try:
        sender.connect()

        # Replace the loop with sensor data reading logic
        while True:
            data_to_send = input("Enter data to send (or 'exit' to quit): ")
            if data_to_send.lower() == "exit":
                break
            sender.send_data(data_to_send)

    finally:
        sender.disconnect()