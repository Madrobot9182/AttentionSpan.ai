from flask import Flask, jsonify
from flask_cors import CORS
from multiprocessing import Process, Value, freeze_support
from pip_window import start_pip_window
import time
from inference_thread import run_inference_background
import threading
from muse_streaming import start_muse_inference
from omegaconf import OmegaConf

app = Flask(__name__)
CORS(app)

pip_process = None
should_stop = Value('b', False)  # shared boolean flag

# Shared state
latest_focus_data = {"class_label": None, "probabilities": {}, "timestamp": None}

@app.route("/focus_data", methods=["GET"])
def get_focus_data():
    """Frontend polls this to get latest focus level"""
    return jsonify(latest_focus_data)

def run_pip_window():
    start_pip_window(window_title="Focus Graph",
                     update_interval=500,
                     max_points=20,
                     stop_flag=should_stop)

@app.route("/start_pip", methods=["POST"])
def start_pip():
    global pip_process, should_stop
    if pip_process and pip_process.is_alive():
        return {"status": "already running"}

    should_stop.value = False  # reset the stop flag
    pip_process = Process(target=run_pip_window)
    pip_process.start()
    return {"status": "started"}

@app.route("/stop_pip", methods=["POST"])
def stop_pip():
    global pip_process, should_stop
    if pip_process and pip_process.is_alive():
        should_stop.value = True  # signal Tkinter to exit
        pip_process.join(timeout=5)
        if pip_process.is_alive():
            pip_process.terminate()  # force kill if needed
            pip_process.join()
        pip_process = None
        return {"status": "stopped"}
    return {"status": "no window running"}

if __name__ == "__main__":
    freeze_support()

    # cfg = OmegaConf.load("configs/main_config.yaml")

    inference_thread = threading.Thread(
        target=start_muse_inference,
        args=(latest_focus_data,),
        daemon=True
    )
    inference_thread.start()

    app.run(port=5001, debug=True, use_reloader=False)