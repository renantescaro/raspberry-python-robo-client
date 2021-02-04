import socket
import time
from joystick_class import Joystick
from dados_class import Dados
from socket_class import Socket

_joystick = Joystick()
_socket   = Socket()
_dados    = Dados()

while True:
    _joystick.verificar_comandos()
    enviar = False

    #### analogicos ####

    # camera
    if (_joystick.analogico_direito_y > 0.6 or _joystick.analogico_direito_y < -0.6):
        _dados.camera_vertical = _joystick.analogico_direito_y
        enviar = True
    if (_joystick.analogico_direito_x > 0.6 or _joystick.analogico_direito_x < -0.6):
        _dados.camera_horizontal = _joystick.analogico_direito_x
        enviar = True

    # direção esquerda / direita
    if (_joystick.analogico_esquerdo_x > 0.6):
        _dados.motor_esquerda = True
        enviar = True
    elif _joystick.analogico_esquerdo_x < -0.6:
        _dados.motor_direita = True
        enviar = True


    #### botoes ####

    # frente / tras
    if _dados.motor_frente != _joystick.botao_1:
        _dados.motor_frente = _joystick.botao_1
        enviar = True
    if _dados.motor_tras != _joystick.botao_2:
        _dados.motor_tras = _joystick.botao_2
        enviar = True


    if enviar:
        dados_bytes = str.encode( _dados.get() )
        _socket.enviar(dados_bytes)
        _dados.camera_vertical   = 0
        _dados.camera_horizontal = 0
        _dados.motor_esquerda    = False
        _dados.motor_direita     = False

    enviar = False