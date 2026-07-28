import asyncio
from bleak import BleakScanner
import csv
import math
import sys
sys.stdout.reconfigure(encoding='utf-8')
#  CONFIG 
TARGET_DEVICES = {
    "D4:E9:F4:A4:5C:F6": 0,
    "D4:E9:F4:A4:8D:E6": 1,
    "C0:CD:D6:CF:6C:3E": 2,
    "C0:CD:D6:CF:31:36": 3
}

BEACON_NAMES = {
    0: "ESP32_Anchor_1",
    1: "ESP32_Anchor_2",
    2: "ESP32_Anchor_3",
    3: "ESP32_Anchor_4"
}

FINGERPRINT_FILE = "fingerprint.csv"

ALPHA = 0.3
K = 5

#  LOAD FINGERPRINTS 
fingerprints = []

with open(FINGERPRINT_FILE, 'r') as f:
    reader = csv.reader(f)
    next(reader)

    for row in reader:
        point = int(row[0])

        means = []
        vars_ = []

        for i in range(1, len(row), 2):
            means.append(float(row[i]))
            vars_.append(float(row[i + 1]))

        fingerprints.append((point, means, vars_))

#  GLOBAL STORAGE 
current_rssi = [None]*4
ema = [None]*4

#  DISTANCE (PARTIAL MATCH) 
def weighted_distance_partial(v, mean, var):
    dist = 0
    count = 0

    for x, m, v_i in zip(v, mean, var):

        if x is None or x == -100:
            continue

        if v_i <= 0:
            v_i = 1

        dist += ((x - m) ** 2) / v_i
        count += 1

    if count == 0:
        return float('inf'), 0

    return math.sqrt(dist / count), count


#  KNN 
def knn_predict(vector):

    distances = []

    for point, means, vars_ in fingerprints:
        d, count = weighted_distance_partial(vector, means, vars_)
        distances.append((point, d, count))

    distances.sort(key=lambda x: x[1])
    nearest = distances[:K]

    #  WEIGHTED VOTING 
    weights = {}
    total_weight = 0

    for p, d, c in nearest:
        w = (1 / (d + 1e-6)) 
        weights[p] = weights.get(p, 0) + w
        total_weight += w

    best_point = max(weights, key=weights.get)
    best_weight = weights[best_point]

    #  CONFIDENCE 
    if total_weight == 0:
        confidence = 0
    else:
        confidence = best_weight / total_weight

    return best_point, nearest, confidence


#  STRONGEST BEACON 
def get_strongest_beacon(vector):
    valid = [(i, rssi) for i, rssi in enumerate(vector) if rssi != -100]

    if not valid:
        return None, None

    idx, rssi = max(valid, key=lambda x: x[1])
    return idx, rssi


#  CALLBACK 
def detection_callback(device, advertisement_data):
    addr = device.address.upper()

    if addr in TARGET_DEVICES:
        idx = TARGET_DEVICES[addr]
        rssi = advertisement_data.rssi

        if rssi is None or rssi > 0:
            return

        current_rssi[idx] = rssi


#  MAIN 
async def run_localization():

    scanner = BleakScanner(detection_callback, scanning_mode="active")
    await scanner.start()

    print(" Adaptive Localization Started\n")

    while True:
        await asyncio.sleep(0.5)

        #  EMA 
        for i in range(4):
            rssi = current_rssi[i]

            if rssi is None:
                continue

            if ema[i] is None:
                ema[i] = rssi
            else:
                ema[i] = ALPHA * rssi + (1 - ALPHA) * ema[i]

        #  BUILD VECTOR 
        vector = [
            x if x is not None else -100
            for x in ema
        ]

        #  NO SIGNAL 
        if all(x == -100 for x in vector):
            print("\n No signal detected (out of range)")
            continue

        #  PREDICT 
        point, nearest, confidence = knn_predict(vector)

        available_count = sum(1 for x in vector if x != -100)
        adjusted_conf = confidence 
        print(f"Point: {point}, Confidence: {round(confidence,2)}")
        #  OUTPUT 
        print("\n RSSI:", [round(x, 2) for x in vector])
        print(f" Point: {point}")
        print(f" Confidence: {round(adjusted_conf, 2)}")
        print(f" Beacons used: {available_count}/4")

        #  FALLBACK DISPLAY 
        
        if adjusted_conf < 0.5:
            idx, rssi = get_strongest_beacon(vector)

            if idx is not None:
                print("Approximate Location (Fallback Mode)")
                print(f"Near Beacon: {BEACON_NAMES[idx]} ({rssi} dBm)")
            else:
                print("No beacon available")

        print("Nearest:", [(p, round(d, 2)) for p, d, _ in nearest])


#  RUN 
asyncio.run(run_localization())
