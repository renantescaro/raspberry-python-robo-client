import os

class Environ():
    def set_variaveis(self):
        os.environ['API_USER'] = 'username'
        os.environ['API_PASSWORD'] = 'secret'

    def get_variaveis(self):
        pass