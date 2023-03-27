from classes.joystick import Joystick
from classes.dados import Dados
from classes.socket_class import Socket
from threading import Thread


class Rotina:
    def __init__(self, **kwargs):
        self._joystick = Joystick()
        self._socket = Socket()
        self._dados = Dados()

    def _acelerador(self):
        if self._joystick.acelerador_tipo == 'analogico':
            if (self._joystick.analogico[ int(self._joystick.acelerador_porta) ] < self._joystick.sensib_neg):
                self._dados.motor_frente = True
                return True
        elif self._dados.motor_frente != self._joystick.botao[ int(self._joystick.acelerador_porta) ]:
            self._dados.motor_frente = self._joystick.botao[ int(self._joystick.acelerador_porta) ]
            return True
        return False

    def _re(self):
        if self._joystick.re_tipo == 'analogico':
            if (self._joystick.analogico[ int(self._joystick.re_porta) ] < self._joystick.sensib_neg):
                self._dados.motor_tras = True
                return True
        elif self._dados.motor_tras != self._joystick.botao[ int(self._joystick.re_porta) ]:
            self._dados.motor_tras = self._joystick.botao[ int(self._joystick.re_porta) ]
            return True
        return False

    def _esquerda(self):
        if self._joystick.direcao_e_tipo == 'analogico':
            if (self._joystick.analogico[ int(self._joystick.direcao_e_porta) ] < self._joystick.sensib_neg):
                if self._dados.motor_esquerda == False:
                    self._dados.motor_esquerda = True
                    return True
            elif self._dados.motor_esquerda == True:
                self._dados.motor_esquerda = False
                return True

        elif self._dados.motor_esquerda != self._joystick.botao[ int(self._joystick.direcao_e_porta) ]:
            self._dados.motor_esquerda = self._joystick.botao[ int(self._joystick.direcao_e_porta) ]
            return True
        return False

    def _direita(self):
        if self._joystick.direcao_d_tipo == 'analogico':
            if self._joystick.analogico[ int(self._joystick.direcao_d_porta)] > self._joystick.sensib_pos:
                if self._dados.motor_direita == False:
                    self._dados.motor_direita = True
                    return True
            elif self._dados.motor_direita == True:
                self._dados.motor_direita = False
                return True
    
        elif self._dados.motor_direita != self._joystick.botao[ int(self._joystick.direcao_d_porta) ]:
            self._dados.motor_direita = self._joystick.botao[ int(self._joystick.direcao_d_porta) ]
            return True
        return False

    def _camera_vertical(self):
        if self._joystick.cam_v_tipo == 'analogico' and (
            self._joystick.analogico[int(self._joystick.cam_v_porta)] > self._joystick.sensib_pos
            or self._joystick.analogico[int(self._joystick.cam_v_porta)] < self._joystick.sensib_neg
        ):
            self._dados.camera_vertical = self._joystick.analogico[ int(self._joystick.cam_v_porta) ]
            return True
        return False

    def _camera_horizontal(self):
        if self._joystick.cam_h_tipo == 'analogico' and (
            self._joystick.analogico[int(self._joystick.cam_h_porta)] > self._joystick.sensib_pos
            or self._joystick.analogico[int(self._joystick.cam_h_porta)] < self._joystick.sensib_neg
        ):
            self._dados.camera_horizontal = self._joystick.analogico[ int(self._joystick.cam_h_porta) ]
            return True
        return False

    def run(self):
        while True:
            self._joystick.setar_comandos()
            enviar = False

            if self._acelerador():
                enviar = True

            if self._re():
                enviar = True

            if self._esquerda():
                enviar = True

            if self._direita():
                enviar = True

            if self._camera_vertical():
                enviar = True

            if self._camera_horizontal():
                enviar = True

            # envia comandos via socket
            if enviar:
                dados_bytes = str.encode( self._dados.get() )
                self._socket.enviar(dados_bytes)
                self._dados.camera_vertical = 0
                self._dados.camera_horizontal = 0
