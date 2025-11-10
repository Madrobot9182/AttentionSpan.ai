import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import requests

def start_pip_window(window_title="Live PiP Graph",
                     update_interval=1000,
                     max_points=10,
                     stop_flag=None,
                     api_url="http://127.0.0.1:5001/focus_data"):

    root = tk.Tk()
    root.title(window_title)
    root.geometry("500x350")
    root.attributes("-topmost", True)

    text_var = tk.StringVar(value="Waiting for data...")
    label = tk.Label(root, textvariable=text_var,
                     font=("Helvetica", 14), fg="white", bg="black")
    label.pack(fill=tk.X)

    fig, ax = plt.subplots()
    fig.patch.set_facecolor('black')
    ax.set_facecolor('black')
    ax.tick_params(colors='white')
    for spine in ax.spines.values():
        spine.set_color('white')

    # 4 regression targets
    reg_labels = ["FO-NF", "FO-FA", "UF-NF", "UF-FA"]
    colors = ["lime", "orange", "cyan", "magenta"]
    x_data = []
    y_data = [[] for _ in range(4)]

    lines = []
    for i in range(4):
        (line,) = ax.plot([], [], color=colors[i], label=reg_labels[i], linewidth=2)
        lines.append(line)

    ax.legend(facecolor="black", edgecolor="white", labelcolor="white")
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def update_graph():
        if stop_flag and stop_flag.value:
            root.destroy()
            return

        try:
            response = requests.get(api_url, timeout=0.5)
            if response.status_code == 200:
                data = response.json()
                reg_output = data.get("reg_output", [])

                if reg_output and len(reg_output) == 4:
                    # Append each reg_output channel
                    x_data.append(len(x_data))
                    for i in range(4):
                        y_data[i].append(float(reg_output[i]))

                    # Keep within rolling window
                    x_disp = x_data[-max_points:]
                    for i in range(4):
                        y_disp = y_data[i][-max_points:]
                        lines[i].set_data(x_disp, y_disp)

                    # Auto scale based on small changes (micro fluctuations)
                    all_vals = [v for ch in y_data for v in ch[-max_points:]]
                    if all_vals:
                        min_val = min(all_vals)
                        max_val = max(all_vals)
                        # Slight padding for readability
                        ax.set_ylim(min_val - 0.01, max_val + 0.01)

                    ax.relim()
                    ax.autoscale_view(True, True, True)
                    canvas.draw()

                    label_text = f"{data.get('class_label', 'Unknown')} | " + \
                                 " ".join([f"{lbl}:{reg_output[i]:.6f}" for i, lbl in enumerate(reg_labels)])
                    text_var.set(label_text)

        except Exception:
            pass  # ignore connection hiccups

        root.after(update_interval, update_graph)

    root.after(update_interval, update_graph)
    root.mainloop()
