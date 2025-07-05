import numpy as np
import matplotlib.pyplot as plt
import time
import sys
import select

# Gyroscope sensor model
def gyro_model(t, amplitude=1.0, frequency=0.5, noise_std=0.1):
    """Simulates gyroscope output with sine wave and Gaussian noise."""
    signal = amplitude * np.sin(2 * np.pi * frequency * t)
    noise = np.random.normal(0, noise_std)
    return signal + noise

# Flight computer decision logic
def flight_computer(gyro_reading):
    """Determines command based on gyroscope reading."""
    if abs(gyro_reading) > 0.8:
        return "Activate Dampers"
    elif abs(gyro_reading) > 0.3:
        return "Stabilize Yaw"
    else:
        return "Hold Position"

# Function to check for user input non-blocking
def check_user_input(params, pause_flag):
    """Checks for user input without blocking the simulation."""
    if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
        try:
            user_input = sys.stdin.readline().strip().lower()
            if user_input == 'pause':
                pause_flag[0] = True
                print("Simulation paused.")
            elif user_input == 'resume':
                pause_flag[0] = False
                print("Simulation resumed.")
            elif user_input == 'stop':
                params['stop_simulation'] = True
                pause_flag[0] = False
                print("Stopping simulation...")
            elif user_input.startswith('amp '):
                try:
                    new_amp = float(user_input.split()[1])
                    if new_amp >= 0:
                        params['amplitude'] = new_amp
                        print(f"Amplitude updated to {new_amp}")
                    else:
                        print("Amplitude must be non-negative.")
                except (IndexError, ValueError):
                    print("Invalid amplitude. Use: amp <value>")
            elif user_input.startswith('freq '):
                try:
                    new_freq = float(user_input.split()[1])
                    if new_freq > 0:
                        params['frequency'] = new_freq
                        print(f"Frequency updated to {new_freq}")
                    else:
                        print("Frequency must be positive.")
                except (IndexError, ValueError):
                    print("Invalid frequency. Use: freq <value>")
            elif user_input.startswith('noise '):
                try:
                    new_noise = float(user_input.split()[1])
                    if new_noise >= 0:
                        params['noise_std'] = new_noise
                        print(f"Noise std updated to {new_noise}")
                    else:
                        print("Noise std must be non-negative.")
                except (IndexError, ValueError):
                    print("Invalid noise std. Use: noise <value>")
            else:
                print("Unknown command.")
        except EOFError:
            params['stop_simulation'] = True
            pause_flag[0] = False
            print("EOF received. Stopping simulation...")
    return pause_flag

# Simulation parameters
duration = 10.0  # seconds
dt = 0.1  # time step in seconds
time_steps = np.arange(0, duration, dt)
gyro_data = []
commands = []
timestamps = []

# Shared parameters for interactivity
params = {
    'amplitude': 1.0,
    'frequency': 0.5,
    'noise_std': 0.1,
    'stop_simulation': False
}

# Pause flag as a list to allow modification
pause_flag = [False]

# Print initial instructions
print("Commands: 'pause', 'resume', 'amp <value>', 'freq <value>', 'noise <value>', 'stop'")
print("Enter commands during simulation...")

# Real-time simulation loop
start_time = time.time()
for t in time_steps:
    if params['stop_simulation']:
        break
    
    # Check for user input
    pause_flag = check_user_input(params, pause_flag)
    
    # Check for pause
    while pause_flag[0] and not params['stop_simulation']:
        time.sleep(0.1)
        pause_flag = check_user_input(params, pause_flag)
    
    # Get current gyroscope reading
    gyro_reading = gyro_model(t, params['amplitude'], params['frequency'], params['noise_std'])
    
    # Get flight computer command
    command = flight_computer(gyro_reading)
    
    # Store data
    gyro_data.append(gyro_reading)
    commands.append(command)
    timestamps.append(t)
    
    # Real-time print
    print(f"[t={t:.1f}s] Gyro={gyro_reading:.2f} | Command={command}")
    
    # Simulate real-time by sleeping
    elapsed_time = time.time() - start_time
    sleep_time = max(0, t - elapsed_time)
    time.sleep(sleep_time)

# Convert lists to numpy arrays for plotting
gyro_data = np.array(gyro_data)
timestamps = np.array(timestamps)

# Plotting results
plt.figure(figsize=(10, 6))
plt.plot(timestamps, gyro_data, label='Gyroscope Reading', color='blue')
plt.axhline(y=0.8, color='red', linestyle='--', label='Dampers Threshold (±0.8)')
plt.axhline(y=-0.8, color='red', linestyle='--')
plt.axhline(y=0.3, color='green', linestyle='--', label='Yaw Threshold (±0.3)')
plt.axhline(y=-0.3, color='green', linestyle='--')
plt.title('Gyroscope Data with Decision Thresholds')
plt.xlabel('Time (s)')
plt.ylabel('Angular Velocity (rad/s)')
plt.grid(True)
plt.legend()
plt.savefig('gyro_data_interactive.png')

# Save log file
with open('hil_simulation_log.txt', 'w') as f:
    f.write("Time(s),Gyro Reading,Command\n")
    for t, gyro, cmd in zip(timestamps, gyro_data, commands):
        f.write(f"{t:.1f},{gyro:.2f},{cmd}\n")

print("\nSimulation complete. Log saved to 'hil_simulation_log.txt' and plot saved to 'gyro_data_interactive.png'.")