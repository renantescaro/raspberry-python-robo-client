import tkinter as tk

class VideoStreaming(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.grid()
        self.criar_componentes()


    def criar_componentes(self):
        self.hi_there = tk.Button(self)
        self.hi_there["text"] = "Hello World\n(click me)"
        self.hi_there.pack(side="top")
        self.quit = tk.Button(self, text="QUIT", fg="red",
                              command=self.master.destroy)
        self.quit.pack(side="bottom")


def iniciar():
    tkinter = tk.Tk()
    tkinter.geometry('500x300')
    app = VideoStreaming(master=tkinter)
    app.mainloop()