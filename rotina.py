from config import Config
from joystick import Joystick
from dados import Dados
from socket_class import Socket
import threading

class Rotina():
    def __init__(self):
        self._joystick = Joystick()
        self._socket   = Socket()
        self._dados    = Dados()

        # comandos do joystick salvos no arquivo .env
        self.acelerador_tipo, self.acelerador_porta = Config.get('JOYSTICK_ACELERADOR').split('-')
        self.re_tipo, self.re_porta                 = Config.get('JOYSTICK_RE').split('-')
        self.direcao_e_tipo, self.direcao_e_porta   = Config.get('JOYSTICK_ESQUERDA').split('-')
        self.direcao_d_tipo, self.direcao_d_porta   = Config.get('JOYSTICK_DIREITA').split('-')
        self.cam_v_tipo, self.cam_v_porta           = Config.get('JOYSTICK_CAM_V').split('-')
        self.cam_h_tipo, self.cam_h_porta           = Config.get('JOYSTICK_CAM_H').split('-')

    def preparar_envio_socket(self):
        while True:
            self._joystick.verificar_comandos()
            enviar = False

            # acelerador
            if self.acelerador_tipo == 'analogico':
                if (self._joystick.analogico[ int(self.acelerador_porta) ] < -0.6):
                    self._dados.motor_frente = True
                    enviar = True
            else:
                if self._dados.motor_frente != self._joystick.botao[ int(self.acelerador_porta) ]:
                    self._dados.motor_frente = self._joystick.botao[ int(self.acelerador_porta) ]
                    enviar = True
            # re
            if self.re_tipo == 'analogico':
                if (self._joystick.analogico[ int(self.re_porta) ] < -0.6):
                    self._dados.motor_tras = True
                    enviar = True
            else:
                if self._dados.motor_tras != self._joystick.botao[ int(self.re_porta) ]:
                    self._dados.motor_tras = self._joystick.botao[ int(self.re_porta) ]
                    enviar = True

            # direção esquerda
            if self.direcao_e_tipo == 'analogico':
                if (self._joystick.analogico[ int(self.direcao_e_porta) ] < -0.6):
                    self._dados.motor_esquerda = True
                    enviar = True
            else:
                if self._dados.motor_esquerda != self._joystick.botao[ int(self.direcao_e_porta) ]:
                    self._dados.motor_esquerda = self._joystick.botao[ int(self.direcao_e_porta) ]
                    enviar = True
            # direção direita
            if self.direcao_d_tipo == 'analogico':
                if self._joystick.analogico[ int(self.direcao_d_porta)] > 0.6:
                    self._dados.motor_direita = True
                    enviar = True
            else:
                if self._dados.motor_direita != self._joystick.botao[ int(self.direcao_d_porta) ]:
                    self._dados.motor_direita = self._joystick.botao[ int(self.direcao_d_porta) ]
                    enviar = True

            # camera vertical
            if self.cam_v_tipo == 'analogico':
                if (self._joystick.analogico[ int(self.cam_v_porta) ] > 0.6 or self._joystick.analogico[ int(self.cam_v_porta) ] < -0.6):
                    self._dados.camera_vertical = self._joystick.analogico[ int(self.cam_v_porta) ]
                    enviar = True
            else:
                pass
            # camera horizontal
            if self.cam_h_tipo == 'analogico':
                if (self._joystick.analogico[ int(self.cam_h_porta) ] > 0.6 or self._joystick.analogico[ int(self.cam_h_porta) ] < -0.6):
                    self._dados.camera_horizontal = self._joystick.analogico[ int(self.cam_h_porta) ]
                    enviar = True
            else:
                pass


            # envida comandos via socket
            if enviar:
                dados_bytes = str.encode( self._dados.get() )
                self._socket.enviar(dados_bytes)
                self._dados.camera_vertical   = 0
                self._dados.camera_horizontal = 0
                self._dados.motor_esquerda    = False
                self._dados.motor_direita     = False
            enviar = False


def iniciar():
    rotina = Rotina()
    # rotina.preparar_envio_socket()
    # thread = threading.Thread( target=rotina.preparar_envio_socket() )
    # thread.daemon = True 
    # thread.start()