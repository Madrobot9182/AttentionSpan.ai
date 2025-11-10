import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import random

def start_pip_window(window_title="Live PiP Graph",
                     update_interval=1000,
                     max_points=10,
                     stop_flag=None):
    """
    stop_flag: multiprocessing.Value('b', False)
    """

    # Always create a fresh Tk root
    root = tk.Tk()
    root.title(window_title)
    root.geometry("400x300")
    root.attributes("-topmost", True)

    text_var = tk.StringVar()
    text_var.set("Dynamic Text Here")
    label = tk.Label(root, textvariable=text_var,
                     font=("Helvetica", 14), fg="white", bg="black")
    label.pack(fill=tk.X)

    fig, ax = plt.subplots()
    fig.patch.set_facecolor('black')
    ax.set_facecolor('black')
    ax.tick_params(colors='white')
    for spine in ax.spines.values():
        spine.set_color('white')

    x_data, y_data = [], []
    line, = ax.plot(x_data, y_data, color='lime')

    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def update_graph():
        if stop_flag and stop_flag.value:
            root.destroy()
            return

        x_data.append(len(x_data))
        y_data.append(random.randint(0, 10))

        x_display = x_data[-max_points:]
        y_display = y_data[-max_points:]
        line.set_data(x_display, y_display)

        ax.relim()
        ax.autoscale_view()
        canvas.draw()

        text_var.set(f"Latest Value: {y_data[-1]}")
        root.after(update_interval, update_graph)

    root.after(update_interval, update_graph)
    root.mainloop()
