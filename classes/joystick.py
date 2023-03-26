import pygame
from classes.config import Config

class Joystick:
    def __init__(self):
        self.analogico = [0.0, 0.0, 0.0, 0.0] # 0.0, 0.0
        self.botao = [False, False, False, False, False, False]

        self.acelerador_tipo, self.acelerador_porta = Config.get('JOYSTICK_ACELERADOR').split('-')
        self.re_tipo, self.re_porta = Config.get('JOYSTICK_RE').split('-')
        self.direcao_e_tipo, self.direcao_e_porta = Config.get('JOYSTICK_ESQUERDA').split('-')
        self.direcao_d_tipo, self.direcao_d_porta = Config.get('JOYSTICK_DIREITA').split('-')
        self.cam_v_tipo, self.cam_v_porta = Config.get('JOYSTICK_CAM_V').split('-')
        self.cam_h_tipo, self.cam_h_porta  = Config.get('JOYSTICK_CAM_H').split('-')
        self.sensib_pos = float(Config.get('SENSIBILIDADE_ANALOGICOS'))
        self.sensib_neg = -float(Config.get('SENSIBILIDADE_ANALOGICOS'))

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
            for index_btn in range(len(self.botao)):
                # down button
                if event.type == pygame.JOYBUTTONDOWN:
                    if self.joystick.get_button(index_btn):
                        self.botao[index_btn] = True

                # up button
                elif event.type == pygame.JOYBUTTONUP:
                    if int(event.button) == index_btn:
                        self.botao[index_btn] = False

    def _verificar_analogicos(self):
        for b in range(len(self.analogico)):
            self.analogico[b] = self.joystick.get_axis(b)
        self.clock.tick(20)

    def pegar_botao_pressionado(self):
        # botoes
        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN:
                for n in range(len(self.botao)):
                   if self.joystick.get_button(n):
                       return n, 'botao'
        # analogicos
        for a in range(len(self.analogico)):
            valor_analogico = self.joystick.get_axis(a)
            if (valor_analogico > 0.4 or valor_analogico < -0.4) and valor_analogico != -1:
                return a, 'analogico'
        return -1, ''
