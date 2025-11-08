from flask import Flask
from flask_cors import CORS
from multiprocessing import Process
from pip_window import start_pip_window

app = Flask(__name__)
CORS(app)

pip_process = None

@app.route("/start_pip", methods=["POST"])
def start_pip():
    global pip_process
    if pip_process and pip_process.is_alive():
        return {"status": "already running"}

    pip_process = Process(target=start_pip_window, kwargs={
        "window_title": "Focus Graph",
        "update_interval": 500,
        "max_points": 20
    })
    pip_process.start()

    return {"status": "started"}

@app.route("/stop_pip", methods=["POST"])
def stop_pip():
    global pip_process
    if pip_process and pip_process.is_alive():
        pip_process.terminate()
        pip_process = None
        return {"status": "stopped"}
    return {"status": "no window running"}


if __name__ == "__main__":
    app.run(port=5001, debug=True)