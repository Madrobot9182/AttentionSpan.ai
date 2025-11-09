from brainflow.board_shim import (
    BoardShim,
    BrainFlowInputParams,
    BoardIds,
    BrainFlowPresets,
)
from brainflow.data_filter import DataFilter, FilterTypes, WindowOperations
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

    def get_avg_wave_data(self):
        time.sleep(30)  # x seconds of data
        data = self.board.get_board_data()

        eeg_data = data[self.board.get_eeg_channels(self.boardId)]
        # gyro
        aux_data = self.board.get_board_data(preset=BrainFlowPresets.AUXILIARY_PRESET)

        pprint(self.board.get_board_descr(self.boardId, 2))
        if aux_data.shape[0] >= 6:
            accel_data = aux_data[0:3, :]
            gyro_data = aux_data[3:6, :]
            gyro_mean = np.mean(gyro_data, axis=1)
            accel_mean = np.mean(accel_data, axis=1)
        else:
            gyro_mean = [0, 0, 0]
            accel_mean = [0, 0, 0]
        # gyro_data = aux_data[self.board.get_gyro_channels(self.boardId)]
        # gyro_mean = np.mean(gyro_data, axis=1)  # mean per axis (x, y, z)
        # print(gyro_mean)
        # print(accel_mean)

        # Ensure even-length EEG (weird hack with postprocessing?)
        if (
            eeg_data.shape[1] % 2 == 1
        ):  # The PSD can only be calculated on arrays with even length
            eeg_data = eeg_data[
                :, : eeg_data.shape[1] - 1
            ]  # So if the length is uneven, we just remove the last sample

        sampling_rate = self.board.get_sampling_rate(self.boardId)
        eeg_data = np.ascontiguousarray(
            eeg_data
        )  # This line might be neccesary if you get the error "BrainFlowError: INVALID_ARGUMENTS_ERROR:13 wrong memory layout, should be row major, make sure you didnt transpose array"

        # Get the average and standard deviations of band powers across all channels
        avgs, stds = DataFilter.get_avg_band_powers(
            eeg_data,
            channels=np.arange(eeg_data.shape[0]),
            sampling_rate=sampling_rate,
            apply_filter=False,
        )

        row = {
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

        # Convert to DataFrame (single-row)
        print("Standard Deviations:", stds)
        return pd.DataFrame([row])

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
    with open("data/session_count.txt", "r") as file:
        session_num = file.read().strip()
        print("Starting Session " + session_num)
    with open("data/session_count.txt", "w") as file:
        file.write(str(int(session_num) + 1))

    fname = f"session_{session_num}_muse2_data"
    csv_path = f"data/{fname}.csv"
    parquet_path = f"data/{fname}.parquet"

    # Attempt to connect to use
    com_port_path = "/dev/ttyACM0"  # Or COM7
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

    # --- Save combined dataset ---
    df.to_csv(csv_path, index=False)
    df.to_parquet(parquet_path, index=False)
    print(f"\n✅ All data saved to {csv_path} and {parquet_path}")

    board.board.stop_stream()
    board.disconnect_muse()
