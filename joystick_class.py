import pygame

class Joystick:
    def __init__(self):
        self.analogico_esquerdo_x = 0.0
        self.analogico_esquerdo_y = 0.0
        self.analogico_direito_x  = 0.0
        self.analogico_direito_y  = 0.0
        self.botao_1 = False
        self.botao_2 = False
        self.botao_3 = False
        self.botao_4 = False
        self.botao_5 = False
        self.botao_6 = False

        pygame.init()
        self.clock = pygame.time.Clock()
        pygame.joystick.init()

        # número do joystick plugado
        self.joystick = pygame.joystick.Joystick(0)
        self.joystick.init()


    def verificar_comandos(self):
        self._verificar_botoes()
        self._verificar_analogicos()
        

    def _verificar_botoes(self):
        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN:
                if self.joystick.get_button(0):
                    self.botao_1 = True #a
                if self.joystick.get_button(1):
                    self.botao_2 = True #b
                if self.joystick.get_button(2):
                    self.botao_3 = True #x
                if self.joystick.get_button(3):
                    self.botao_4 = True #y
                if self.joystick.get_button(4):
                    self.botao_5 = True #lb
                if self.joystick.get_button(5):
                    self.botao_6 = True #rb

            elif event.type == pygame.JOYBUTTONUP:
                if int(event.button) == 0:
                    self.botao_1 = False #a
                if int(event.button) == 1:
                    self.botao_2 = False #b
                if int(event.button) == 2:
                    self.botao_3 = False #x
                if int(event.button) == 3:
                    self.botao_4 = False #y
                if int(event.button) == 4:
                    self.botao_5 = False #lb
                if int(event.button) == 5:
                    self.botao_6 = False #rb


    def _verificar_analogicos(self):
        # direção esquerda / direita
        self.analogico_esquerdo_x = self.joystick.get_axis(0)
        self.analogico_esquerdo_y = self.joystick.get_axis(1)

        # camera
        self.analogico_direito_x  = self.joystick.get_axis(3)
        self.analogico_direito_y  = self.joystick.get_axis(4)

        self.clock.tick(20)