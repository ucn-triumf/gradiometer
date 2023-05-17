from guizero import App, TextBox
import tkinter as tk
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


def print_value():

    print(text_box.value)

    # Example of altering the plot based on what you typed
    a.plot([1, 2, 3, 4], [1*text_box.value, 2, 3, 4])
    canvas.draw()


# guizero stuff
app = App()
text_box = TextBox(app, command=print_value)

   
# Matplotlib stuff (example)
f = Figure(figsize=(5,5), dpi=100)
a = f.add_subplot(111)
x = [1, 2, 3, 4]
y = [1, 2, 3, 4]
a.plot(x, y)

# Make a special tkinter canvas that works with matplotlib,
# and add it to app.tk (i.e. the tk widget hidden inside the guizero App)
canvas = FigureCanvasTkAgg(f, app.tk)
canvas.draw()
canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

# Enter the infinite display loop (this has to come after creating the plot)
app.display()
