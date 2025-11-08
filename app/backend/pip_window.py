import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import random

def start_pip_window(window_title="Live PiP Graph", update_interval=1000, max_points=10):
    """
    Opens a Picture-in-Picture window with a live-updating graph and dynamic text.
    
    Parameters:
        window_title (str): Title of the PiP window.
        update_interval (int): Update interval in milliseconds.
        max_points (int): Maximum number of data points to show on the graph.
    """
    root = tk.Tk()
    root.title(window_title)
    root.geometry("400x300")
    root.attributes("-topmost", True)

    # Dynamic text label
    text_var = tk.StringVar()
    text_var.set("Dynamic Text Here")
    label = tk.Label(root, textvariable=text_var, font=("Helvetica", 14), fg="white", bg="black")
    label.pack(fill=tk.X)

    # Create matplotlib figure
    fig, ax = plt.subplots()
    fig.patch.set_facecolor('black')
    ax.set_facecolor('black')
    ax.tick_params(colors='white')
    ax.spines['bottom'].set_color('white')
    ax.spines['top'].set_color('white') 
    ax.spines['right'].set_color('white')
    ax.spines['left'].set_color('white')

    x_data, y_data = [], []
    line, = ax.plot(x_data, y_data, color='lime')

    # Embed matplotlib figure in Tkinter
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def update_graph():
        # Append new data
        x_data.append(len(x_data))
        y_data.append(random.randint(0, 10))

        # Keep only the last 'max_points' points
        x_display = x_data[-max_points:]
        y_display = y_data[-max_points:]
        line.set_data(x_display, y_display)

        ax.relim()
        ax.autoscale_view()
        canvas.draw()

        # Update text dynamically
        text_var.set(f"Latest Value: {y_data[-1]}")

        # Schedule next update
        root.after(update_interval, update_graph)

    update_graph()
    root.mainloop()
