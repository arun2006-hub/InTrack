import asyncio
from bleak import BleakScanner
import csv
import os
import statistics

#      CONFIG     
TARGET_DEVICES = {
    "D4:E9:F4:A4:5C:F6": 0,
    "D4:E9:F4:A4:8D:E6": 1,
    "C0:CD:D6:CF:6C:3E": 2,
    "C0:CD:D6:CF:31:36": 3
}

NUM_POINTS = 6
SAMPLES_PER_POINT = 100
PAUSE_TIME = 5
STABILIZE_TIME = 2

RAW_FILE = "raw_samples.csv"
FINGERPRINT_FILE = "fingerprint.csv"

#      INIT FILES (overwrite for clean run)     
with open(RAW_FILE, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["Point", "RSSI1", "RSSI2", "RSSI3", "RSSI4"])

with open(FINGERPRINT_FILE, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow([
        "Point",
        "B1_mean", "B1_var",
        "B2_mean", "B2_var",
        "B3_mean", "B3_var",
        "B4_mean", "B4_var"
    ])

#      GLOBAL STORAGE     
current_sample = [None, None, None, None]

#      CALLBACK     
def detection_callback(device, advertisement_data):
    addr = device.address.upper()

    if addr in TARGET_DEVICES:
        idx = TARGET_DEVICES[addr]
        rssi = advertisement_data.rssi

        if rssi is None or rssi > 0:
            return

        current_sample[idx] = rssi


#      MAIN COLLECTION     
async def run_collection():

    global current_sample

    scanner = BleakScanner(detection_callback, scanning_mode="active")
    await scanner.start()

    for point in range(1, NUM_POINTS + 1):

        print(f"\n Move to Point {point}")
        print(" Stabilizing...")
        await asyncio.sleep(STABILIZE_TIME)

        # Reset
        current_sample = [None]*4
        samples = []
        raw_buffer = []

        # Wait for first valid readings
        while all(x is None for x in current_sample):
            await asyncio.sleep(0.1)

        print(" Sampling started...")

        while len(samples) < SAMPLES_PER_POINT:
            await asyncio.sleep(0.2)

            # Only take valid samples
            if any(x is not None for x in current_sample):
                sample = current_sample.copy()
                samples.append(sample)
                raw_buffer.append([point] + sample)

        print(" Sampling done")

        #    WRITE RAW DATA (batch)   
        with open(RAW_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(raw_buffer)

        #    MEDIAN FILL   
        columns = list(zip(*samples))
        processed = []

        for col in columns:
            valid = [x for x in col if x is not None]

            if len(valid) < 10:
                # Too few samples → unreliable
                filled = [-100]*len(col)
            else:
                med = statistics.median(valid)
                filled = [x if x is not None else med for x in col]

            processed.append(filled)

        #    MEAN + VAR   
        row = [point]

        for col in processed:
            mean = sum(col)/len(col)

            if len(col) > 1:
                var = statistics.variance(col)
            else:
                var = 0

            # Prevent zero variance
            var = max(var, 1)

            row.extend([round(mean, 2), round(var, 2)])

        #    SAVE FINGERPRINT   
        with open(FINGERPRINT_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(row)

        print(f" Saved fingerprint: {row[1:]}")
        print(f" Move to next point in {PAUSE_TIME} sec...\n")

        await asyncio.sleep(PAUSE_TIME)

    await scanner.stop()
    print(" Fingerprinting complete!")


#      RUN     
asyncio.run(run_collection())
