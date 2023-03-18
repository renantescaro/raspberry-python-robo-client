import pygame

class Joystick:
    def __init__(self):
        self.analogico = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.botao     = [False, False, False, False, False, False]

        pygame.init()
        self.clock = pygame.time.Clock()
        pygame.joystick.init()

        # # número do joystick plugado
        self.joystick = pygame.joystick.Joystick(0)
        self.joystick.init()

    def verificar_comandos(self):
        self._verificar_botoes()
        self._verificar_analogicos()

    def _verificar_botoes(self):
        for event in pygame.event.get():
            # down
            for b in range(len(self.botao)):
                if event.type == pygame.JOYBUTTONDOWN:
                    if self.joystick.get_button(b):
                        self.botao[b] = True
                elif event.type == pygame.JOYBUTTONUP:
                    if int(event.button) == b:
                        self.botao[b] = False

    def _verificar_analogicos(self):
        for b in range(len(self.analogico)):
            self.analogico[b] = self.joystick.get_axis(b)
        self.clock.tick(20)

    def pegar_botao_pressionado(self):
        # botoes
        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN:
                for n in range(15):
                   if self.joystick.get_button(n):
                       return n, 'botao'
        # analogicos
        for a in range(6):
            valor_analogico = self.joystick.get_axis(a)
            if (valor_analogico > 0.4 or valor_analogico < -0.4) and valor_analogico != -1:
                return a, 'analogico'
        return -1, ''
