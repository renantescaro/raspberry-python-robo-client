import cv2
from config import Config

# parametro 0 para webcam integrada / usb
camera = cv2.VideoCapture(Config.get('STREAMING_URL'))
classificador = cv2.CascadeClassifier('xmls/haar_xml_07_19.xml')

while (True):
    conectado, imagem = camera.read()
    imagem_cinza = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)
    faces_detectadas = classificador.detectMultiScale(imagem_cinza, scaleFactor=1.5, minSize=(100, 100))

    # retangulos em faces detectadas
    for (x, y, l, a) in faces_detectadas:
        cv2.rectangle(imagem, (x, y), (x+l, y+a), (0, 0, 255), 2)

    cv2.imshow('teste', imagem)
    cv2.waitKey(1)

camera.release()
cv2.destroyAllWindows()
