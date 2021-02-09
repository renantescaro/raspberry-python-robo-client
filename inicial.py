from config import Config
import rotina
import interface_grafica.config_joystick as ig_config_joystick
import interface_grafica.video_streaming as ig_video_streaming

if Config.arquivo_vazio():
    # interface configuração de joystick
    ig_config_joystick.iniciar()
    pass
else:
    # rotina principal de envio de comandos por socket
    rotina.iniciar()
    #ig_video_streaming.iniciar()