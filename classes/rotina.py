from classes.joystick import Joystick
from classes.dados import Dados
from classes.socket_class import Socket
from threading import Thread


class Rotina:
    def __init__(self, **kwargs):
        self._joystick = Joystick()
        self._socket = Socket()
        self._dados = Dados()

    def run(self):
        while True:
            self._joystick.verificar_comandos()
            enviar = False

            # acelerador
            if self._joystick.acelerador_tipo == 'analogico':
                if (self._joystick.analogico[ int(self._joystick.acelerador_porta) ] < self._joystick.sensib_neg):
                    self._dados.motor_frente = True
                    enviar = True
            elif self._dados.motor_frente != self._joystick.botao[ int(self._joystick.acelerador_porta) ]:
                self._dados.motor_frente = self._joystick.botao[ int(self._joystick.acelerador_porta) ]
                enviar = True

            # re
            if self._joystick.re_tipo == 'analogico':
                if (self._joystick.analogico[ int(self._joystick.re_porta) ] < self._joystick.sensib_neg):
                    self._dados.motor_tras = True
                    enviar = True
            elif self._dados.motor_tras != self._joystick.botao[ int(self._joystick.re_porta) ]:
                self._dados.motor_tras = self._joystick.botao[ int(self._joystick.re_porta) ]
                enviar = True

            # direção esquerda
            if self._joystick.direcao_e_tipo == 'analogico':
                if (self._joystick.analogico[ int(self._joystick.direcao_e_porta) ] < self._joystick.sensib_neg):
                    self._dados.motor_esquerda = True
                    enviar = True
            elif self._dados.motor_esquerda != self._joystick.botao[ int(self._joystick.direcao_e_porta) ]:
                self._dados.motor_esquerda = self._joystick.botao[ int(self._joystick.direcao_e_porta) ]
                enviar = True

            # direção direita
            if self._joystick.direcao_d_tipo == 'analogico':
                if self._joystick.analogico[ int(self._joystick.direcao_d_porta)] > self._joystick.sensib_pos:
                    self._dados.motor_direita = True
                    enviar = True
            elif self._dados.motor_direita != self._joystick.botao[ int(self._joystick.direcao_d_porta) ]:
                self._dados.motor_direita = self._joystick.botao[ int(self._joystick.direcao_d_porta) ]
                enviar = True

            # camera vertical
            if self._joystick.cam_v_tipo == 'analogico' and (
                self._joystick.analogico[int(self._joystick.cam_v_porta)] > self._joystick.sensib_pos
                or self._joystick.analogico[int(self._joystick.cam_v_porta)] < self._joystick.sensib_neg
            ):
                self._dados.camera_vertical = self._joystick.analogico[ int(self._joystick.cam_v_porta) ]
                enviar = True

            # camera horizontal
            if self._joystick.cam_h_tipo == 'analogico' and (
                self._joystick.analogico[int(self._joystick.cam_h_porta)] > self._joystick.sensib_pos
                or self._joystick.analogico[int(self._joystick.cam_h_porta)] < self._joystick.sensib_neg
            ):
                self._dados.camera_horizontal = self._joystick.analogico[ int(self._joystick.cam_h_porta) ]
                enviar = True

            # envia comandos via socket
            if enviar:
                dados_bytes = str.encode( self._dados.get() )
                self._socket.enviar(dados_bytes)
                self._dados.camera_vertical = 0
                self._dados.camera_horizontal = 0
                self._dados.motor_esquerda = False
                self._dados.motor_direita = False
            enviar = False
