# 🚀 Spacecraft_HIL_Simulation

A real-time Hardware-in-the-Loop (HIL) simulation for spacecraft avionics — built in Python.  
This project simulates a gyroscope sensor and a basic flight computer, allowing real-time interaction to modify signal parameters mid-simulation.

---

## 📌 Features

- Simulates gyroscope sensor with sine + Gaussian noise
- Real-time interactive control: `pause`, `resume`, `stop`, and change signal parameters
- Decision logic to simulate basic flight computer actions
- Outputs:
  - Time-series plot of gyroscope data with control thresholds
  - Command log file

---

## 🧠 How It Works

1. **Sensor model** generates a noisy sine-wave signal as gyroscope output.
2. **Flight computer** analyzes the signal and makes decisions like:
   - `Activate Dampers`
   - `Stabilize Yaw`
   - `Hold Position`
3. You can interact with the simulation in real time via terminal input:
   - `pause`, `resume`, `stop`
   - `amp <value>`, `freq <value>`, `noise <value>`

---

## 🖥️ Requirements

- Python 3.x
- `numpy`
- `matplotlib`

Install required libraries:
```bash
pip install numpy matplotlib

## 📈 Sample Output

![Gyroscope Plot](gyro_data_interactive.png)
