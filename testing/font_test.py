import tkinter as tk
import tkinter.font as tkfont
window = tk.Tk()
bi_times = tkfont.Font(family="Times", size=120, weight="bold", slant="italic")
canvas = tk.Canvas(window, width=400, height=200)
canvas.pack()
canvas.create_text(200, 100, text="Hi!", font=bi_times)
window.mainloop()



import tkinter.font


