import socket

class Socket:
    def __init__(self):
        self.HOST    = '192.168.0.200'
        self.PORTA   = 5001
        self.DESTINO = (self.HOST, self.PORTA)

        self.tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp.connect(self.DESTINO)

    def desconectar(self):
        self.tcp.close()

    def enviar(self, dados_bytes):
        self.tcp.send(dados_bytes)
