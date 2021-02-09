import tkinter as tk
import threading
from joystick import Joystick

class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.joystick = Joystick()
        self.master = master
        self.grid()
        self.acelerador = tk.StringVar() 
        self.re         = tk.StringVar()
        self.esquerda   = tk.StringVar()
        self.direita    = tk.StringVar()
        self.cam_v      = tk.StringVar()
        self.cam_h      = tk.StringVar()
        self.criar_componentes()
        self.txt_acelerador.focus_set()
        self.atual = self.acelerador


    def criar_componentes(self):
        # acelerador
        self.lbl_acelerador = tk.Label(
            self, text='Acelerador')
        self.lbl_acelerador.grid(row=1, column=1)
        self.txt_acelerador = tk.Entry(self, width=15, textvariable=self.acelerador)
        self.txt_acelerador.grid(row=1, column=2)

        # ré
        self.lbl_re = tk.Label(
            self, text='Ré')
        self.lbl_re.grid(row=2, column=1)
        self.txt_re = tk.Entry(self, width=15, textvariable=self.re)
        self.txt_re.grid(row=2, column=2)

        # esquerda
        self.lbl_esquerda = tk.Label(
            self, text='Esquerda')
        self.lbl_esquerda.grid(row=3, column=1)
        self.txt_esquerda = tk.Entry(self, width=15, textvariable=self.esquerda)
        self.txt_esquerda.grid(row=3, column=2)

        # direita
        self.lbl_direita = tk.Label(
            self, text='Direita')
        self.lbl_direita.grid(row=4, column=1)
        self.txt_direita = tk.Entry(self, width=15, textvariable=self.direita)
        self.txt_direita.grid(row=4, column=2)

        # eixo vertical camera
        self.lbl_eixo_vertical_camera = tk.Label(
            self, text='Eixo Vertical Camera')
        self.lbl_eixo_vertical_camera.grid(row=1, column=3)
        self.txt_eixo_vertical_camera = tk.Entry(self, width=15, textvariable=self.cam_v)
        self.txt_eixo_vertical_camera.grid(row=1, column=4)

        # eixo horizontal camera
        self.lbl_eixo_horizontal_camera = tk.Label(
            self, text='Eixo Horizontal Camera')
        self.lbl_eixo_horizontal_camera.grid(row=2, column=3)
        self.txt_eixo_horizontal_camera = tk.Entry(self, width=15, textvariable=self.cam_h)
        self.txt_eixo_horizontal_camera.grid(row=2, column=4)

        # botao salvar
        self.btn_salvar = tk.Button(
            self, text='salvar',
            command=self.salvar)
        self.btn_salvar.grid(row=7, column=1)


    def salvar(self):
        print( self.txt_nome.get() )

    def verificar(self):
        while True:
            num, tipo = self.joystick.get_botao_pressionado()
            if num != -1:
                conteudo_entry = root.focus_get().get()
                if conteudo_entry == '':
                    root.focus_get().insert(0, tipo+'-'+str(num))


root = tk.Tk()
root.geometry('500x300')
app = Application(master=root)

thread = threading.Thread( target=app.verificar )
thread.daemon = True 
thread.start()

app.mainloop()