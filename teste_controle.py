import pygame

pygame.init()

clock = pygame.time.Clock()
pygame.joystick.init()

joystick = pygame.joystick.Joystick(0)
joystick.init()


while True:
    for event in pygame.event.get():
        if event.type == pygame.JOYBUTTONDOWN:
            for n in range(11):
                if joystick.get_button(n):
                    print(n)

    for b in range(4):
        get_axis = joystick.get_axis(b)
        
        if(get_axis > 0.16 or get_axis < -0.16):
            print(f'{b} -> {get_axis}')

        clock.tick(20)
