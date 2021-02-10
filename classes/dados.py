import json

class Dados:
    def __init__(self):
        self.camera_vertical   = float()
        self.camera_horizontal = float()
        self.motor_frente      = False
        self.motor_tras        = False
        self.motor_esquerda    = False
        self.motor_direita     = False

    def get(self):
        return json.dumps({
            'camera-v'       : self.camera_vertical,
            'camera-h'       : self.camera_horizontal,
            'motor-frente'   : self.motor_frente,
            'motor-tras'     : self.motor_tras,
            'motor-esquerda' : self.motor_esquerda,
            'motor-direita'  : self.motor_direita,
        })