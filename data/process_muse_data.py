from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds, BrainFlowPresets
from brainflow.data_filter import DataFilter, FilterTypes, WindowOperations
from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
import time
from pprint import pprint


class MuseBoard:
    board: BoardShim
    boardId = 38
    con_port: str
    
    def __init__(self, con_port ):
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
        time.sleep(5) # 30 seconds of data
        data = self.board.get_board_data()
        
        eeg_data = data[self.board.get_eeg_channels(self.boardId)]
        # gyro
        aux_data = self.board.get_board_data(preset=BrainFlowPresets.AUXILIARY_PRESET)
       
        
        pprint(self.board.get_board_descr(self.boardId,2))
        if aux_data.shape[0] >= 6:
            accel_data = aux_data[0:3, :]
            gyro_data = aux_data[3:6, :]
            gyro_mean = np.mean(gyro_data, axis=1)
            accel_mean = np.mean(accel_data, axis = 1)
        else:
            gyro_mean = [0, 0, 0]
            accel_mean = [0,0,0]
        # gyro_data = aux_data[self.board.get_gyro_channels(self.boardId)]
        # gyro_mean = np.mean(gyro_data, axis=1)  # mean per axis (x, y, z)
        # print(gyro_mean)
        # print(accel_mean)

        
        # Ensure even-length EEG (weird hack with postprocessing?)
        if eeg_data.shape[1] % 2 == 1: #The PSD can only be calculated on arrays with even length
            eeg_data = eeg_data[:, :eeg_data.shape[1]-1] #So if the length is uneven, we just remove the last sample

        

        sampling_rate = self.board.get_sampling_rate(self.boardId)
        eeg_data = np.ascontiguousarray(eeg_data) #This line might be neccesary if you get the error "BrainFlowError: INVALID_ARGUMENTS_ERROR:13 wrong memory layout, should be row major, make sure you didnt transpose array"

        #Get the average and standard deviations of band powers across all channels
        avgs, stds = DataFilter.get_avg_band_powers(eeg_data,
                                                    channels=np.arange(eeg_data.shape[0]),
                                                    sampling_rate=sampling_rate,
                                                    apply_filter=False)
        row = {
            "timestamp": pd.Timestamp.now(),
            "delta": avgs[0],
            "theta": avgs[1],
            "alpha": avgs[2],
            "beta": avgs[3],
            "gamma": avgs[4],
            "gyro_x": gyro_mean[0],
            "gyro_y": gyro_mean[1],
            "gyro_z": gyro_mean[2],
            "accel_x": accel_mean[0],
            "accel_y": accel_mean[1],
            "accel_z": accel_mean[2],
        }

        # Convert to DataFrame (single-row)
        print("Standard Deviations:", stds)
        return pd.DataFrame([row])


    def disconnect_muse(self):
        self.board.release_session()


if __name__ == "__main__":
    com_port_path = "/dev/ttyACM0" # Or COM7
    board = MuseBoard(com_port_path)
    conn_status = False
    while not conn_status:
        try:
            conn_status = board.connect_muse()
            print("\n\n\n BEGINNING BRAIN PROCESSING \n\n\n")
        
        except Exception as e:
            print(e)

    columns = [
        "timestamp", "Delta", "Theta", "Alpha", "Beta", "Gamma",
        "GyroX", "GyroY", "GyroZ",
        "AccelX", "AccelY", "AccelZ",
        "FO-NF", "FO-FA", "UF-NF", "UF-FA", "Label_Class"
    ]
    df = pd.DataFrame(columns=columns)

    # Define where to save
    fname = "session_01/TestFatigue"
    csv_path = f"{fname}.csv"
    parquet_path = f"{fname}.parquet"


    # Sessions we want to test for


    for i in range(4):
        print(f"\n=== Sample {i+1}/4 ===")

        # Read data and get dataframe
        dataframe = board.get_avg_wave_data()

        # Now ask for user input tbh
        user_input = input("Enter label values (comma-separated): ")
        if user_input.strip():
            try:
                fo_nf, fo_fa, uf_nf, uf_fa, label_class = map(float, user_input.split(","))
            except ValueError:
                print("Invalid input. Using zeros.")
                fo_nf = fo_fa = uf_nf = uf_fa = label_class = 0
        else:
            fo_nf = fo_fa = uf_nf = uf_fa = label_class = 0

        # Add label columns
        row_df["FO-NF"] = fo_nf
        row_df["FO-FA"] = fo_fa
        row_df["UF-NF"] = uf_nf
        row_df["UF-FA"] = uf_fa
        row_df["Label_Class"] = label_class
        
        # Append to master DataFrame
        df = pd.concat([df, row_df], ignore_index=True)
        print("✅ Sample recorded.")

        csv_path = f"{fname}.csv"
        parquet_path = f"{fname}.parquet"

    # --- Save combined dataset ---
    df.to_csv(csv_path, index=False)
    df.to_parquet(parquet_path, index=False)
    print(f"\n✅ All data saved to {csv_path} and {parquet_path}")


    board.board.stop_stream()
    board.disconnect_muse()
