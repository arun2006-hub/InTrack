# BLE Indoor Localization System

An end-to-end BLE (Bluetooth Low Energy) indoor positioning and tracking system utilizing ESP32 microcontrollers as fixed anchors and a Python host application running adaptive signal processing and $k$-Nearest Neighbors ($k$-NN) fingerprinting algorithms.

---

## Project Architecture

The system operates in three main stages:
1. **Beacon Anchors (ESP32):** Fixed nodes broadcasting calibrated BLE advertisements at high frequency ($10\text{ Hz}$).
2. **Fingerprint Calibration:** Mapping target indoor locations into statistical RSSI signature vectors ($\text{Mean}, \text{Variance}$).
3. **Live Positioning Engine:** Processing real-time signals with dynamic EMA filtering, partial-match $k$-NN estimation, and proximity fallbacks.
