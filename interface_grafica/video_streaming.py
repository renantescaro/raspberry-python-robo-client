from classes.config import Config
import tkinter as tk
from PIL import Image, ImageTk
import cv2

class VideoStreaming(tk.Frame):
    def __init__(self):
        self._largura_tela = 0
        self._altura_tela = 0
        self._pegar_resolucao()
        self.master = tk.Tk()
        self.master.title('Video Streaming')
        self.master.geometry(f'{self._largura_tela}x{self._altura_tela}')
        super().__init__(self.master)

    def executar(self):
        self.camera = cv2.VideoCapture( Config.get('STREAMING_URL') )
        app = tk.Frame(self.master, bg='white')
        app.grid()
        self.master = tk.Label(app)
        self.master.grid()
        self._video_componente()
        app.mainloop()

    def _video_componente(self):
        conectado, imagem_cv2 = self.camera.read()
        resize_img = cv2.resize(imagem_cv2, (int(self._largura_tela), int(self._altura_tela)) )
        rotate_img = cv2.rotate(resize_img, cv2.ROTATE_180)
        img = Image.fromarray(rotate_img)
        imgtk = ImageTk.PhotoImage(image=img)
        self.master.imgtk = imgtk
        self.master.configure(image=imgtk)
        self.master.after(1, self._video_componente)

    def _pegar_resolucao(self):
        resolucao = Config.get('resolucao')
        if len(resolucao) == 0:
            self._largura_tela = 800
            self._altura_tela = 600
        posicao_x = resolucao.find('x')
        self._largura_tela = resolucao[:posicao_x]
        self._altura_tela = resolucao[posicao_x+1:]
