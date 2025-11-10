from flask import Flask, jsonify
from flask_cors import CORS
from multiprocessing import Process, Value, freeze_support, Manager
from pip_window import start_pip_window
from muse_streaming import start_muse_inference
import threading

app = Flask(__name__)
CORS(app)

pip_process = None
should_stop = Value('b', False)

# Shared state (only used within main process + muse thread)
manager = Manager()
latest_focus_data = manager.dict({
    "class_label": None,
    "probabilities": {},
    "reg_output": [0.4, 0.3, 0.2, 0.1],
    "timestamp": None
})

@app.route("/focus_data", methods=["GET"])
def get_focus_data():
    """Frontend polls this endpoint to get latest focus level"""
    return jsonify(dict(latest_focus_data))


def run_pip_window():
    """Launch floating PiP window (polls HTTP for live data)"""
    start_pip_window(
        window_title="Focus Graph",
        update_interval=1000,
        max_points=20,
        stop_flag=should_stop,
        api_url="http://127.0.0.1:5001/focus_data"
    )


@app.route("/start_pip", methods=["POST"])
def start_pip():
    """Start the PIP visualization"""
    global pip_process, should_stop
    if pip_process and pip_process.is_alive():
        return {"status": "already running"}

    should_stop.value = False
    pip_process = Process(target=run_pip_window)
    pip_process.start()
    return {"status": "started"}


@app.route("/stop_pip", methods=["POST"])
def stop_pip():
    """Stop the PIP window cleanly"""
    global pip_process, should_stop
    if pip_process and pip_process.is_alive():
        should_stop.value = True
        pip_process.join(timeout=5)
        if pip_process.is_alive():
            pip_process.terminate()
            pip_process.join()
        pip_process = None
        return {"status": "stopped"}
    return {"status": "no window running"}


if __name__ == "__main__":
    freeze_support()

    # Start Muse inference thread
    inference_thread = threading.Thread(
        target=start_muse_inference,
        args=(latest_focus_data,),
        daemon=True
    )
    inference_thread.start()

    print("✅ Flask API running at http://127.0.0.1:5001")
    app.run(port=5001, debug=True, use_reloader=False)
