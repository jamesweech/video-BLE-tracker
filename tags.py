import asyncio
import json
import os
from bleak import BleakScanner
from datetime import datetime

# File to store the tag states between runs
STATE_FILE = "tag_states.json"

# File containing the beacons (MAC address and name)
BEACONS_FILE = "beacons.txt"

# Dictionary to keep track of devices and their current state (True if in range, False if out of range)
device_states = {}

# Dictionary to track how many consecutive cycles a device has been missed
missed_cycles = {}

# To track devices that were in range during the current scan cycle
devices_in_range = {}


def load_beacons():
    """Load the MAC addresses and their names from beacons.txt."""
    known_devices = {}
    if os.path.exists(BEACONS_FILE):
        with open(BEACONS_FILE, "r") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) == 2:
                    mac, name = parts
                    known_devices[mac] = name
    return known_devices


def load_previous_states(known_devices):
    """Load the previous states from a file, if it exists, and synchronize with the current beacons."""
    previous_states = {}

    # Load the previous states from the file, if it exists
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            previous_states = json.load(f)

    # Create a new state dictionary to compare and synchronize the tags
    synchronized_states = {}

    # Synchronize based on known devices from beacons.txt
    for mac, name in known_devices.items():
        # If the MAC exists in the previous state, update its name if necessary
        if mac in previous_states:
            previous_state = previous_states[mac]
            if previous_state['name'] != name:
                print(f"Renaming device {previous_state['name']} to {name}")
                previous_state['name'] = name
            synchronized_states[mac] = previous_state
        else:
            # If the MAC was not in the previous state, add it with default values
            synchronized_states[mac] = {
                'in_range': False,
                'last_status_change': None,
                'name': name
            }

    # Save the synchronized state to the file
    return synchronized_states


def save_current_states():
    """Save the current states to a file."""
    with open(STATE_FILE, "w") as f:
        json.dump(device_states, f, indent=4)  # Added indent=4 for better readability


async def detection_callback(device, advertising_data):
    # Check if the detected device is one of the known devices
    if device.address in known_devices:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # If the device was previously out of range and is now detected
        if not device_states[device.address]['in_range']:
            device_states[device.address] = {
                'in_range': True,
                'last_status_change': now,
                'name': known_devices[device.address]
            }  # Mark the device as in range and update last status change
            missed_cycles[device.address] = 0  # Reset missed cycles count
            print(f"{now} - {known_devices[device.address]} is in range, RSSI: {advertising_data.rssi}")

        # Add to devices in range this scan cycle
        devices_in_range[device.address] = True


async def monitor_devices():
    scanner = BleakScanner(detection_callback)

    while True:
        # Start scanning for devices
        await scanner.start()
        await asyncio.sleep(5)  # Scan for 5 seconds
        await scanner.stop()

        # Check if any known devices are missing from the scan results
        for mac, name in known_devices.items():
            if mac not in devices_in_range:
                # Device was missed this cycle
                missed_cycles[mac] += 1

                # If the device was previously in range and missed for 3 cycles, declare it out of range
                if device_states[mac]['in_range'] and missed_cycles[mac] >= 3:
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    device_states[mac] = {
                        'in_range': False,
                        'last_status_change': now,
                        'name': name
                    }  # Mark the device as out of range and update last status change
                    print(f"{now} - {name} is out of range")
            else:
                # Device was detected, reset missed cycles
                missed_cycles[mac] = 0

        # Clear the in-range devices for the next scan iteration
        devices_in_range.clear()

        # Save the current states to the file
        save_current_states()

        # Optional delay between scans
        await asyncio.sleep(1)  # Wait for 1 second before the next scan cycle


if __name__ == "__main__":
    # Load known devices from the beacons.txt file
    known_devices = load_beacons()

    # Initialize device states and missed cycles for all known devices
    device_states = load_previous_states(known_devices)
    missed_cycles = {mac: 0 for mac in known_devices}

    # Run the monitoring function
    asyncio.run(monitor_devices())
