from brainflow.board_shim import (
    BoardShim,
    BrainFlowInputParams,
    BoardIds,
    BrainFlowPresets,
)
from brainflow.data_filter import (
    DataFilter,
    FilterTypes,
    WindowOperations,
    DetrendOperations,
)
from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
import time
from pprint import pprint
from pathlib import Path


class MuseBoard:
    board: BoardShim
    boardId = 38
    con_port: str

    def __init__(self, con_port):
        self.con_port = con_port

    def connect_muse(self):
        try:
            params = BrainFlowInputParams()
            params.serial_port = self.con_port
            self.board = BoardShim(self.boardId, params)
            self.board.prepare_session()
            return True
        except Exception as e:
            return False

    def get_avg_wave_data(self, window_size_sec=2, overlap=0.5):
        """
        Collects EEG + AUX data from Muse 2 and performs full post-processing.

        Includes:
            - Filtering (bandpass, notch)
            - Artifact rejection (amplitude + motion)
            - Bandpower extraction in overlapping windows

        Args:
            window_size_sec: sliding window size (s) for bandpower calc
            overlap: fraction of overlap between adjacent windows

        Returns:
            pd.DataFrame: multi-row time series of band powers, gyro, accel
        """
        time.sleep(90)  # x seconds of data

        data = self.board.get_board_data()
        eeg_data = data[self.board.get_eeg_channels(self.boardId)]
        aux_data = self.board.get_board_data(preset=BrainFlowPresets.AUXILIARY_PRESET)

        pprint(self.board.get_board_descr(self.boardId, 2))

        # --- ✅ Step 0: Initial Data Validation ---
        if len(eeg_data) == 0 or len(aux_data) == 0:
            print("❌ No data was recorded, returning early")
            return pd.DataFrame()

        if eeg_data.shape[1] < 16:
            print(f"❌ Insufficient data: {eeg_data.shape[1]} samples (need >= {16})")
            return pd.DataFrame()

        if aux_data.shape[0] >= 6:
            accel_data = aux_data[0:3, :]
            gyro_data = aux_data[3:6, :]
            gyro_mean = np.mean(gyro_data, axis=1)
            accel_mean = np.mean(accel_data, axis=1)
        else:
            gyro_mean = [0, 0, 0]
            accel_mean = [0, 0, 0]

        # POST PROCESSING
        # --- 🧹 Step 1: Clean EEG (Filtering) ---
        # Removes drift, muscle noise, and powerline hum
        sampling_rate = self.board.get_sampling_rate(self.boardId)
        eeg_data = np.ascontiguousarray(eeg_data)

        for ch in range(eeg_data.shape[0]):
            DataFilter.detrend(eeg_data[ch], DetrendOperations.CONSTANT.value)
            DataFilter.perform_bandpass(
                eeg_data[ch],
                sampling_rate,
                1.0,
                50.0,
                2,
                FilterTypes.BUTTERWORTH.value,
                0,
            )  # Keep brainwave frequencies only
            DataFilter.perform_bandstop(
                eeg_data[ch],
                sampling_rate,
                58.0,
                62.0,
                2,
                FilterTypes.BUTTERWORTH.value,
                0,
            )  # Remove 60 Hz noise (North America)
            DataFilter.perform_bandstop(
                eeg_data[ch],
                sampling_rate,
                48.0,
                52.0,
                2,
                FilterTypes.BUTTERWORTH.value,
                0,
            )  # Remove 50 Hz noise (Europe)

        # --- ⚠️ Step 2: Artifact Rejection (Eye Blinks / Spikes) ---
        # Eye blinks can cause 100–300 µV spikes; remove extreme samples
        amplitude_mask = np.all(np.abs(eeg_data) < 100.0, axis=0)
        eeg_data = eeg_data[:, amplitude_mask]

        # Optional: remove top 5% variance windows
        std_per_sample = np.std(eeg_data, axis=0)
        mask_std = std_per_sample < np.percentile(std_per_sample, 95)
        eeg_data = eeg_data[:, mask_std]

        # --- 🚫 Step 3: Reject motion-contaminated data ---
        # accel_data shape: (3, n_samples)
        accel_magnitude = np.linalg.norm(
            accel_data, axis=0
        )  # total acceleration each sample
        delta_accel = np.diff(accel_magnitude)  # change in acceleration
        motion_score = np.mean(np.abs(delta_accel))  # average absolute change
        if motion_score > 0.5:  # Adjust threshold if too sensitive
            print("⚠️  High motion detected — skipping this segment.")
            return pd.DataFrame()  # return empty, skip recording

        # --- 🪟 Step 4: Rolling Bandpower Extraction ---
        n_samples = eeg_data.shape[1]
        win_len = int(window_size_sec * sampling_rate)
        step = int(win_len * (1 - overlap))  # step size in samples

        rows = []
        for start in range(0, n_samples - win_len + 1, step):
            end = start + win_len
            window = eeg_data[:, start:end]

            # ⚙️ Ensure contiguous memory and even-length inside each window too
            if window.shape[1] % 2 == 1:
                window = window[:, :-1]
            window = np.ascontiguousarray(window)

            # --- Compute average band powers ---
            # Returns mean bandpower per frequency band across channels
            avgs, stds = DataFilter.get_avg_band_powers(
                window,
                channels=np.arange(window.shape[0]),
                sampling_rate=sampling_rate,
                apply_filter=False,
            )

            rows.append(
                {
                    "timestamp": pd.Timestamp.now(),
                    "Delta": avgs[0],
                    "Theta": avgs[1],
                    "Alpha": avgs[2],
                    "Beta": avgs[3],
                    "Gamma": avgs[4],
                    "GyroX": gyro_mean[0],
                    "GyroY": gyro_mean[1],
                    "GyroZ": gyro_mean[2],
                    "AccelX": accel_mean[0],
                    "AccelY": accel_mean[1],
                    "AccelZ": accel_mean[2],
                }
            )

        # Convert to DataFrame
        df = pd.DataFrame(rows)
        return df

    def start_muse_stream(self):
        self.board.start_stream()

    def disconnect_muse(self):
        self.board.release_session()


def get_label_from_range():
    """
    Ask user for 1–5 focus and fatigue ratings, compute regression + class labels.

    Label encoding:
        0 = Focused & Not Fatigued   (FO-NF)
        1 = Focused & Fatigued       (FO-FA)
        2 = Unfocused & Not Fatigued (UF-NF)
        3 = Unfocused & Fatigued     (UF-FA)
    """

    # Safe input for focus
    while True:
        try:
            focus_range = int(
                input("On a scale from 1–5, how focused are you? ").strip()
            )
            if 1 <= focus_range <= 5:
                break
            else:
                print("Please enter a number between 1 and 5.")
        except ValueError:
            print("Invalid input. Enter a number between 1 and 5.")

    # Safe input for fatigue
    while True:
        try:
            fatigue_range = int(
                input("On a scale from 1–5, how fatigued are you? ").strip()
            )
            if 1 <= fatigue_range <= 5:
                break
            else:
                print("Please enter a number between 1 and 5.")
        except ValueError:
            print("Invalid input. Enter a number between 1 and 5.")

    # Normalize to [0, 1]
    focus_norm = (focus_range - 1) / 4.0
    fatigue_norm = (fatigue_range - 1) / 4.0

    # Compute regression-style one-hot values
    fo_nf = focus_norm * (1 - fatigue_norm)
    fo_fa = focus_norm * fatigue_norm
    uf_nf = (1 - focus_norm) * (1 - fatigue_norm)
    uf_fa = (1 - focus_norm) * fatigue_norm

    # Determine dominant class
    combos = [fo_nf, fo_fa, uf_nf, uf_fa]
    label_class = int(np.argmax(combos))

    print(
        f"""
    Focus: {focus_range}/5 ({focus_norm:.2f})
    Fatigue: {fatigue_range}/5 ({fatigue_norm:.2f})
    Computed Labels:
        FO-NF={fo_nf:.3f}, FO-FA={fo_fa:.3f}, UF-NF={uf_nf:.3f}, UF-FA={uf_fa:.3f}
        → Label_Class={label_class}
    """
    )

    return fo_nf, fo_fa, uf_nf, uf_fa, label_class


if __name__ == "__main__":
    # Define where to save
    with open("session_count.txt", "r") as file:
        session_num = file.read().strip()
        print("Starting Session " + session_num)

    fname = f"session_{session_num}_muse2_data"
    csv_path = f"{fname}.csv"
    parquet_path = f"{fname}.parquet"

    # Attempt to connect to use
    com_port_path = cfg.muse.com_port   #"/dev/ttyACM0"  # Or COM7
    board = MuseBoard(com_port_path)
    conn_status = False
    while not conn_status:
        try:
            conn_status = board.connect_muse()
        except Exception as e:
            print(e)
        finally:
            print("\n\n CONNECT SUCCESSFUL! BEGINNING BRAIN PROCESSING \n\n")

    columns = [
        "timestamp",
        "Delta",
        "Theta",
        "Alpha",
        "Beta",
        "Gamma",
        "GyroX",
        "GyroY",
        "GyroZ",
        "AccelX",
        "AccelY",
        "AccelZ",
        "FO-NF",
        "FO-FA",
        "UF-NF",
        "UF-FA",
        "Label_Class",
    ]
    df = pd.DataFrame(columns=columns)

    # Sessions we want to test for
    board.start_muse_stream()

    for i in range(100):
        print(f"\n=== Sample {i+1} ===")
        want_to_continue = input("Want to continue sampling? (Y/n)").lower()
        if want_to_continue == "n":
            break

        # Read data and get dataframe
        row_df = board.get_avg_wave_data()
        if row_df.empty:  # Eg too much motion
            print("Skipping this Sample")
            continue

        # Now ask for user input
        fo_nf, fo_fa, uf_nf, uf_fa, label_class = get_label_from_range()

        # Add label columns
        row_df["FO-NF"] = fo_nf
        row_df["FO-FA"] = fo_fa
        row_df["UF-NF"] = uf_nf
        row_df["UF-FA"] = uf_fa
        row_df["Label_Class"] = label_class

        # Append to master DataFrame
        df = pd.concat([df, row_df], ignore_index=True)
        print("✅ Sample recorded.")

    # Update session count (nothing crashed lol)
    with open("session_count.txt", "w") as file:
        file.write(str(int(session_num) + 1))

    # --- Save combined dataset ---
    df.to_csv(csv_path, index=False)
    df.to_parquet(parquet_path, index=False)
    print(f"\n✅ All data saved to {csv_path} and {parquet_path}")

    board.board.stop_stream()
    board.disconnect_muse()
