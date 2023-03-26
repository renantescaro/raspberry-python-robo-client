import socket
from .config import Config

class Socket:
    def __init__(self):
        self.HOST = Config.get('SOCKET_IP')
        self.PORTA = int(Config.get('SOCKET_PORTA'))
        self.DESTINO = (self.HOST, self.PORTA)

        self.tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp.connect(self.DESTINO)

    def desconectar(self):
        self.tcp.close()

    def enviar(self, dados_bytes):
        self.tcp.send(dados_bytes)
