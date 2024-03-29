import tkinter as tk
import threading
from classes.joystick import Joystick
from classes.config import Config

class ConfigJoystick(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.joystick = Joystick()
        self.master = master
        self.grid()
        self.acelerador = tk.StringVar() 
        self.re = tk.StringVar()
        self.esquerda = tk.StringVar()
        self.direita = tk.StringVar()
        self.cam_v = tk.StringVar()
        self.cam_h = tk.StringVar()
        self._criar_componentes()
        self.txt_acelerador.focus_set()
        self.atual = self.acelerador

    def _criar_componentes(self):
        # acelerador
        self.lbl_acelerador = tk.Label(self, text='Acelerador')
        self.lbl_acelerador.grid(row=1, column=1)
        self.txt_acelerador = tk.Entry(self, width=15, textvariable=self.acelerador)
        self.txt_acelerador.grid(row=1, column=2)

        # ré
        self.lbl_re = tk.Label(self, text='Ré')
        self.lbl_re.grid(row=2, column=1)
        self.txt_re = tk.Entry(self, width=15, textvariable=self.re)
        self.txt_re.grid(row=2, column=2)

        # esquerda
        self.lbl_esquerda = tk.Label(self, text='Esquerda')
        self.lbl_esquerda.grid(row=3, column=1)
        self.txt_esquerda = tk.Entry(self, width=15, textvariable=self.esquerda)
        self.txt_esquerda.grid(row=3, column=2)

        # direita
        self.lbl_direita = tk.Label(self, text='Direita')
        self.lbl_direita.grid(row=4, column=1)
        self.txt_direita = tk.Entry(self, width=15, textvariable=self.direita)
        self.txt_direita.grid(row=4, column=2)

        # eixo vertical camera
        self.lbl_eixo_vertical_camera = tk.Label(self, text='Eixo Vertical Camera')
        self.lbl_eixo_vertical_camera.grid(row=1, column=3)
        self.txt_eixo_vertical_camera = tk.Entry(self, width=15, textvariable=self.cam_v)
        self.txt_eixo_vertical_camera.grid(row=1, column=4)

        # eixo horizontal camera
        self.lbl_eixo_horizontal_camera = tk.Label(self, text='Eixo Horizontal Camera')
        self.lbl_eixo_horizontal_camera.grid(row=2, column=3)
        self.txt_eixo_horizontal_camera = tk.Entry(self, width=15, textvariable=self.cam_h)
        self.txt_eixo_horizontal_camera.grid(row=2, column=4)

        # botao salvar
        self.btn_salvar = tk.Button(self, text='salvar', command=self._salvar)
        self.btn_salvar.grid(row=7, column=1)

    def _salvar(self):
        Config.limpar()
        Config.set('joystick_acelerador', self.acelerador.get())
        Config.set('joystick_re', self.re.get())
        Config.set('joystick_esquerda', self.esquerda.get())
        Config.set('joystick_direita', self.direita.get())
        Config.set('joystick_cam_v', self.cam_v.get())
        Config.set('joystick_cam_h', self.cam_h.get())

    def _verificar(self):
        while True:
            num, tipo = self.joystick.pegar_comando()
            if num != -1:
                conteudo_entry = self.master.focus_get().get()
                if conteudo_entry == '':
                    self.master.focus_get().insert(0, f'{tipo}-{str(num)}')
                    # root.focus_get().insert(0, str(num))

def iniciar():
    root = tk.Tk()
    root.geometry('500x300')
    root.title('Configurar Joystick')
    app = ConfigJoystick(master=root)

    thread = threading.Thread(target=app._verificar)
    thread.daemon = True 
    thread.start()

    app.mainloop()
