import numpy as np
import pandas as pd

def generate_mock_muse_data(duration_s=10, eeg_rate=256, motion_rate=52, ppg_rate=64):
    t_eeg = np.linspace(0, duration_s, duration_s * eeg_rate)
    t_motion = np.linspace(0, duration_s, duration_s * motion_rate)
    t_ppg = np.linspace(0, duration_s, duration_s * ppg_rate)

    # --- EEG: synthetic mixture of brainwave frequencies ---
    def eeg_channel():
        alpha = np.sin(2 * np.pi * 10 * t_eeg)        # 10 Hz alpha
        beta = 0.5 * np.sin(2 * np.pi * 20 * t_eeg)  # 20 Hz beta
        theta = 0.3 * np.sin(2 * np.pi * 6 * t_eeg)  # 6 Hz theta
        noise = 0.2 * np.random.randn(len(t_eeg))
        return alpha + beta + theta + noise

    eeg_data = np.vstack([eeg_channel() for _ in range(4)]).T
    eeg_df = pd.DataFrame(eeg_data, columns=["TP9","AF7","AF8","TP10"])
    eeg_df["timestamp"] = t_eeg

    # --- Derived frequency band powers (mean amplitude) ---
    eeg_df["alpha_power"] = np.abs(np.sin(2*np.pi*0.2*t_eeg)) + np.random.rand(len(t_eeg))*0.1
    eeg_df["beta_power"]  = np.abs(np.sin(2*np.pi*0.1*t_eeg+1)) + np.random.rand(len(t_eeg))*0.1
    eeg_df["gamma_power"] = np.random.rand(len(t_eeg))*0.5

    # --- Accelerometer and gyroscope ---
    acc_df = pd.DataFrame({
        "timestamp": t_motion,
        "acc_x": np.sin(0.5 * t_motion) + np.random.randn(len(t_motion))*0.05,
        "acc_y": np.cos(0.5 * t_motion) + np.random.randn(len(t_motion))*0.05,
        "acc_z": np.random.randn(len(t_motion))*0.02,
        "gyro_x": np.random.randn(len(t_motion))*5,
        "gyro_y": np.random.randn(len(t_motion))*5,
        "gyro_z": np.random.randn(len(t_motion))*5,
    })

    # --- Heart rate / PPG signal ---
    heart_rate_bpm = 70 + 5*np.sin(0.1*t_ppg) + np.random.randn(len(t_ppg))*0.5
    ppg_df = pd.DataFrame({"timestamp": t_ppg, "ppg": np.sin(2*np.pi*1.2*t_ppg) + np.random.randn(len(t_ppg))*0.1, "bpm": heart_rate_bpm})

    return eeg_df, acc_df, ppg_df

if __name__ == "__main__":
    eeg, acc, ppg = generate_mock_muse_data(10)
    eeg.to_csv("data/mock_eeg.csv", index=False)
    eeg.to_parquet("data/egg.parquet")

    acc.to_csv("data/mock_acc.csv", index=False)
    acc.to_parquet("data/acc.parquet", index=False)

    ppg.to_csv("data/mock_ppg.csv", index=False)
    ppg.to_parquet("data/ppg.parquet", index=False)

    # AND METADATA

    print("✅ Mock Muse data saved.")
