import numpy as np
import matplotlib
matplotlib.use('Agg')  # MUST be before pyplot to prevent macOS GUI thread crash
import matplotlib.pyplot as plt
import time
import csv
import threading
import queue
from typing import List

class InteractiveGyroSim:
    """Thread-safe interactive gyroscope simulation (macOS/Windows/Linux compatible)."""
    
    def __init__(self, duration: float = 10.0, dt: float = 0.1,
                 amplitude: float = 1.0, frequency: float = 0.5, noise_std: float = 0.1):
        self.duration = duration
        self.dt = dt
        self.params = {'amp': amplitude, 'freq': frequency, 'noise': noise_std}
        
        self.timestamps: List[float] = []
        self.gyro_data: List[float] = []
        self.commands: List[str] = []
        
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        self.cmd_queue = queue.Queue()
        self.console_lock = threading.Lock()

    def _safe_print(self, msg: str):
        """Thread-safe console output to prevent garbled text."""
        with self.console_lock:
            print(msg, flush=True)

    def _start_input_listener(self):
        """Background thread: handles console input without blocking simulation."""
        def listener():
            self._safe_print("🎮 Commands: 'pause', 'resume', 'stop', 'amp <v>', 'freq <v>', 'noise <v>'")
            try:
                while not self.stop_event.is_set():
                    line = input().strip().lower()
                    if line:
                        self.cmd_queue.put(line)
            except (EOFError, KeyboardInterrupt):
                self.stop_event.set()
                
        threading.Thread(target=listener, daemon=True).start()

    def _process_pending_commands(self):
        """Drains and executes all commands currently in the queue."""
        while True:
            try:
                cmd = self.cmd_queue.get_nowait()
            except queue.Empty:
                break
                
            if cmd == 'pause':
                self.pause_event.set()
                self._safe_print("⏸️ Simulation paused.")
            elif cmd == 'resume':
                self.pause_event.clear()
                self._safe_print("▶️ Simulation resumed.")
            elif cmd == 'stop':
                self.stop_event.set()
                self._safe_print("🛑 Stopping simulation...")
            elif cmd.startswith('amp '):
                self._update_param('amp', cmd, 0.0)
            elif cmd.startswith('freq '):
                self._update_param('freq', cmd, 1e-6)
            elif cmd.startswith('noise '):
                self._update_param('noise', cmd, 0.0)
            else:
                self._safe_print("❓ Unknown command.")

    def _update_param(self, name: str, cmd: str, min_val: float):
        try:
            val = float(cmd.split()[1])
            if val < min_val:
                self._safe_print(f"⚠️ {name} must be >= {min_val}")
                return
            self.params[name] = val
            self._safe_print(f"✅ {name} updated to {val}")
        except (IndexError, ValueError):
            self._safe_print(f"❌ Invalid format. Use: {name} <value>")

    def run(self):
        self._start_input_listener()
        
        sim_start = time.perf_counter()
        accumulated_pause = 0.0
        steps = int(round(self.duration / self.dt))
        
        for i in range(steps):
            if self.stop_event.is_set():
                break
                
            # Handle pause state
            if self.pause_event.is_set():
                pause_start = time.perf_counter()
                self._safe_print("⏸️ Paused. Type 'resume' to continue.")
                while self.pause_event.is_set() and not self.stop_event.is_set():
                    self._process_pending_commands()
                    time.sleep(0.05)
                if self.stop_event.is_set():
                    break
                accumulated_pause += time.perf_counter() - pause_start
                
            # Process commands that arrived during sleep/pause
            self._process_pending_commands()
            if self.stop_event.is_set():
                break
                
            # Simulation step
            t = i * self.dt
            gyro = self.params['amp'] * np.sin(2 * np.pi * self.params['freq'] * t) + \
                   np.random.normal(0, self.params['noise'])
            abs_gyro = abs(gyro)
            cmd = ("Activate Dampers" if abs_gyro > 0.8 else 
                   "Stabilize Yaw" if abs_gyro > 0.3 else "Hold Position")
            
            self.timestamps.append(t)
            self.gyro_data.append(gyro)
            self.commands.append(cmd)
            self._safe_print(f"⏱️ [t={t:.1f}s] Gyro={gyro:+.3f} | {cmd}")
            
            # Real-time pacing with pause compensation
            target_time = sim_start + t + accumulated_pause
            sleep_time = target_time - time.perf_counter()
            if sleep_time > 0:
                time.sleep(sleep_time)
                
        # Clean exit
        self.stop_event.set()
        self._post_process()
        plt.close('all')

    def _post_process(self):
        if not self.timestamps:
            self._safe_print("⚠️ No data generated.")
            return
            
        ts = np.array(self.timestamps)
        gyro = np.array(self.gyro_data)
        cmds = np.array(self.commands)
        
        plt.figure(figsize=(11, 6))
        plt.plot(ts, gyro, label='Gyroscope Reading', color='#1f77b4', linewidth=1.5, alpha=0.8)
        
        plt.axhline(0.8, color='#ff7f0e', linestyle='--', linewidth=1, label='Dampers Threshold (±0.8)')
        plt.axhline(-0.8, color='#ff7f0e', linestyle='--', linewidth=1)
        plt.axhline(0.3, color='#2ca02c', linestyle='--', linewidth=1, label='Yaw Threshold (±0.3)')
        plt.axhline(-0.3, color='#2ca02c', linestyle='--', linewidth=1)
        
        mask_damp = cmds == "Activate Dampers"
        mask_yaw = cmds == "Stabilize Yaw"
        plt.scatter(ts[mask_damp], gyro[mask_damp], color='#d62728', marker='o', s=60, zorder=5, label='Dampers Active')
        plt.scatter(ts[mask_yaw], gyro[mask_yaw], color='#2ca02c', marker='s', s=60, zorder=5, label='Yaw Stabilization')
        
        plt.title('Gyroscope Data with Flight Computer Decision Thresholds', fontsize=14, fontweight='bold')
        plt.xlabel('Time (s)', fontsize=12)
        plt.ylabel('Angular Velocity (rad/s)', fontsize=12)
        plt.grid(True, linestyle=':', alpha=0.6)
        plt.legend(loc='upper right', fontsize=10)
        plt.tight_layout()
        plt.savefig('gyro_data_interactive.png', dpi=150, bbox_inches='tight')
        
        with open('hil_simulation_log.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Time(s)', 'Gyro Reading', 'Command'])
            for t_val, g_val, c_val in zip(ts, gyro, cmds):
                writer.writerow([f"{t_val:.1f}", f"{g_val:.3f}", c_val])
                
        self._safe_print("\n✅ Simulation complete.")
        self._safe_print("📊 Plot saved to 'gyro_data_interactive.png'")
        self._safe_print("📄 Log saved to 'hil_simulation_log.csv'")

if __name__ == "__main__":
    try:
        sim = InteractiveGyroSim(duration=10.0, dt=0.1, amplitude=1.0, frequency=0.5, noise_std=0.1)
        sim.run()
    except KeyboardInterrupt:
        print("\n🛑 Simulation interrupted.")
