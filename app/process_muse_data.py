from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds, BrainFlowPresets
from brainflow.data_filter import DataFilter, FilterTypes, WindowOperations
from matplotlib import pyplot as plt
import numpy as np
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
        
    def get_avg_wave_data(self, fname: str):
        time.sleep(5) #wait 5 seconds
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

        

        if eeg_data.shape[1] % 2 == 1: #The PSD can only be calculated on arrays with even length
            eeg_data = eeg_data[:, :eeg_data.shape[1]-1] #So if the length is uneven, we just remove the last sample

        

        sampling_rate = self.board.get_sampling_rate(self.boardId)

        eeg_data = np.ascontiguousarray(eeg_data) #This line might be neccesary if you get the error "BrainFlowError: INVALID_ARGUMENTS_ERROR:13 wrong memory layout, should be row major, make sure you didnt transpose array"

        #Get the average and standard deviations of band powers across all channels
        avgs, stds = DataFilter.get_avg_band_powers(eeg_data,
                                                    channels=np.arange(eeg_data.shape[0]),
                                                    sampling_rate=sampling_rate,
                                                    apply_filter=False)
        
        with open(fname, "a") as f:
            print(f"{avgs[0]},{avgs[1]},{avgs[2]},{avgs[3]},{avgs[4]},{gyro_mean[0]},{gyro_mean[1]},{gyro_mean[2]},{accel_mean[0]},{accel_mean[1]},{accel_mean[2]}", file=f) #The averages will be different from the average of the per-channel band powers because of some other operations happening behind the scenes in get_avg_band_powers(...)
        print("Standard Deviations:", stds)


    def disconnect_muse(self):
        self.board.release_session()

# def connect_muse(con_port: str):
#     board = False
#     try:
#         params = BrainFlowInputParams()
#         params.serial_port = con_port
#         board_id = 38
#         board = BoardShim(board_id, params)
#         board.prepare_session()

#         return board
#     except Exception as e:
#         board = False
#         return board


# def get_avg_wave_data(board: BoardShim):
#     board.start_stream()
    
#     time.sleep(5) #wait 5 seconds
#     data = board.get_board_data()
    
#     board_id = 38 # This code snippet does not work for the synthetic board (not sure why)

#     eeg_data = data[board.get_eeg_channels(board_id)]
#     if eeg_data.shape[1] % 2 == 1: #The PSD can only be calculated on arrays with even length
#         eeg_data = eeg_data[:, :eeg_data.shape[1]-1] #So if the length is uneven, we just remove the last sample
#     sampling_rate = board.get_sampling_rate(board_id)

#     for i in range(eeg_data.shape[0]): #Get the band powers for each channel separately
#         print("Channel", i)

#         psd = DataFilter.get_psd_welch(eeg_data[i],
#                                         nfft=2*sampling_rate,
#                                         overlap=sampling_rate,
#                                         sampling_rate=sampling_rate,
#                                         window=WindowOperations.HANNING.value) #Calculate the Power Spectral Density (don't worry about this)

#         # get_psd(eeg_data[i], sampling_rate, 2*sampling_rate)

#         delta = DataFilter.get_band_power(psd, 1, 4)
#         print("\tDelta:", delta)

#         theta = DataFilter.get_band_power(psd, 4, 8)
#         print("\tTheta:", theta)

#         alpha = DataFilter.get_band_power(psd, 8, 13)
#         print("\tAlpha:", alpha)

#         beta = DataFilter.get_band_power(psd, 13, 30)
#         print("\tBeta:", beta)

#         gamma = DataFilter.get_band_power(psd, 30, 50)
#         print("\tGamma:", gamma)

#     eeg_data = np.ascontiguousarray(eeg_data) #This line might be neccesary if you get the error "BrainFlowError: INVALID_ARGUMENTS_ERROR:13 wrong memory layout, should be row major, make sure you didnt transpose array"

#     #Get the average and standard deviations of band powers across all channels
#     avgs, stds = DataFilter.get_avg_band_powers(eeg_data,
#                                                 channels=np.arange(eeg_data.shape[0]),
#                                                 sampling_rate=sampling_rate,
#                                                 apply_filter=False)
#     print("Averages:", avgs) #The averages will be different from the average of the per-channel band powers because of some other operations happening behind the scenes in get_avg_band_powers(...)
#     # print("Standard Deviations:", stds)

#     board.stop_stream()
    


if __name__ == "__main__":

    board = MuseBoard('COM7')
    conn_status = False
    while not conn_status:
        try:
            conn_status = board.connect_muse()
            print("\n\n\n test \n\n\n")
        
        except Exception as e:
            print(e)

    board.board.start_stream()

    fname = "Focus-NotFatigued.csv"
    col_headers = f"Delta,Theta,Alpha,Beta,Gamma,GyroX,GyroY,GyroZ,AccelX,AccelY,AccelZ,"

    # with open(fname, "a") as f:
    #     print(col_headers, file=f)

    while True:
        board.get_avg_wave_data(fname)
    board.board.stop_stream()
    
    board.disconnect_muse()


    # while board == False:
    #     print("="*50)
    #     print("Trying to connect...")
    #     board = connect_muse('COM4')
    

    # for i in range(10):
    #     get_avg_wave_data(board)
    # 

