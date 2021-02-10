import tkinter as tk
from PIL import Image, ImageTk
import cv2

class VideoStreaming(tk.Frame):
    def __init__(self):
        self.master = tk.Tk()
        self.master.title('Video Streaming')
        self.master.geometry('800x600')
        super().__init__(self.master)
        self.camera = cv2.VideoCapture('http://192.168.0.200:8080/?action=stream')
        app         = tk.Frame(self.master, bg="white")
        app.grid()
        self.master = tk.Label(app)
        self.master.grid()
        self.video_componente()
        app.mainloop()


    def video_componente(self):
        conectado, imagem_cv2 = self.camera.read()
        resize_img = cv2.resize(imagem_cv2, (800, 600))
        img        = Image.fromarray(resize_img)
        imgtk      = ImageTk.PhotoImage(image=img)
        self.master.imgtk = imgtk
        self.master.configure(image=imgtk)
        self.master.after(1, self.video_componente)