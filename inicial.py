from classes.config import Config
from classes.rotina import Rotina
# from interface_grafica.video_streaming import VideoStreaming

if Config.arquivo_vazio():
    # interface grafica configuração de joystick
    import interface_grafica.config_joystick as ig_config_joystick
    ig_config_joystick.iniciar()

else:
    # rotina principal de envio de comandos por socket
    Rotina().run()
    #VideoStreaming().executar()
