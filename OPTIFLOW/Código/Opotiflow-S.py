import numpy as np
import time
import cv2
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)

for i in (23, 25, 16, 21):
    GPIO.setup(i, GPIO.OUT)

# Definindo o pipeline do GStreamer para capturar vídeo da câmera
gstreamer_pipeline = "v4l2src ! video/x-raw,format=YUY2,width=640,height=480,framerate=30/1 ! videoconvert ! appsink"

# Passando o pipeline como argumento para o VideoCapture
cam = cv2.VideoCapture(gstreamer_pipeline, cv2.CAP_GSTREAMER)

# Verificando se a câmera foi aberta corretamente
if not cam.isOpened():
    print("Erro ao acessar a câmera.")
    exit()

time.sleep(0.1)

colorLower = np.array([0, 100, 100])  # mid blue
colorUpper = np.array([179, 255, 255])  # light blue

initvert = 0
inithoriz = 0
counter = 0

xur, yur, xul, yul = 0, 0, 0, 0
xdr, ydr, xdl, ydl = 0, 0, 0, 0

t = 0
t1 = time.time()

# Variáveis para temporização
tempo_aberto = 90  # 1 minuto e meio em segundos
semaforo_aberto = False
tempo_iniciado = False
semaforo_vertical_livre = False  # Controla se o semáforo vertical está aberto
semaforo_horizontal_livre = False  # Controla se o semáforo horizontal está aberto

while t < 5 and cam.isOpened():
    ret, frame = cam.read()
    if not ret:
        print("Erro ao capturar frame da câmera.")
        break

    frame = np.array(frame)  # Transformando o frame em array
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    mask = cv2.inRange(hsv, colorLower, colorUpper)   
    mask = cv2.blur(mask, (3, 3))   
    mask = cv2.dilate(mask, None, iterations=10)
    mask = cv2.erode(mask, None, iterations=1)
    mask = cv2.dilate(mask, None, iterations=5)
    
    me, thresh = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)

    cnts = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[-2]
    
    center = None
    
    if len(cnts) > 0:
        for c in cnts:
            (x, y), radius = cv2.minEnclosingCircle(c)
            center = (int(x), int(y))
            radius = int(radius)
            cv2.circle(frame, center, radius, (0, 255, 0), 2)

            x = int(x)
            y = int(y)
            
            if x > 240:  # right
                if y > 240:  # up
                    xur = x
                    yur = y
                
                if y < 240:  # down
                    xdr = x
                    ydr = y
            if x < 240:  # left
                if y > 240:  # up
                    xul = x
                    yul = y
                
                if y < 240:  # down
                    xdl = x
                    ydl = y

    t2 = time.time()
    t = t2 - t1

# Calibração concluída
time.sleep(5)

while(cam.isOpened()):
    ret, frame = cam.read()
    if not ret:
        print("Erro ao capturar frame da câmera.")
        break
    
    frame = np.array(frame)  # Transformando o frame em array
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    mask = cv2.inRange(hsv, colorLower, colorUpper)   
    maskhsv = cv2.resize(mask, (250, 250))
    
    mask = cv2.blur(mask, (3, 3))   
    mask1 = cv2.resize(mask, (250, 250))
    
    mask = cv2.dilate(mask, None, iterations=10)
    mask2 = cv2.resize(mask, (250, 250))
    
    mask = cv2.erode(mask, None, iterations=1)
    mask3 = cv2.resize(mask, (250, 250))
    
    mask = cv2.dilate(mask, None, iterations=5)
    mask4 = cv2.resize(mask, (250, 250))
    
    imstack = np.hstack((maskhsv, mask1, mask2, mask3, mask4))
    cv2.imshow("masks", imstack)
    
    me, thresh = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)
    cv2.imshow("thresh", thresh)

    cnts = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[-2]
    
    center = None
    vert = 0
    horiz = 0 
    
    if len(cnts) > 0:
        priority = 0
        
        for c in cnts:
            rect = cv2.minAreaRect(c)
            (x, y), (width, height), angle = cv2.minAreaRect(c)
            box = cv2.boxPoints(rect)
            box = np.int0(box)
            Area = width * height
                       
            if Area > 16000:
                priority = 1
                
        for c in cnts:
            rect = cv2.minAreaRect(c)
            (x, y), (width, height), angle = cv2.minAreaRect(c)
            box = cv2.boxPoints(rect)
            box = np.int0(box)
            Area = width * height
            
            x = int(x)
            y = int(y)
            
            if priority == 1 and Area > 16000:
                if xul < x < xur:  # vertical road
                    if y > yur:
                        # Lógica para semáforo vertical
                        GPIO.output(21, GPIO.HIGH)  # Red hor
                        GPIO.output(23, GPIO.HIGH)  # Green vert
                        GPIO.output(25, GPIO.LOW)  # Green hor
                        GPIO.output(16, GPIO.LOW)  # Red vert
                        print("PRIORITY FOR VERTICAL LANE")
                        semaforo_vertical_livre = True  # Semáforo vertical liberado
                        tempo_iniciado = False  # Reinicia o temporizador quando a via tem prioridade
                        
                    elif y < ydr:
                        # Lógica para semáforo vertical
                        GPIO.output(21, GPIO.HIGH)  # Red hor
                        GPIO.output(23, GPIO.HIGH)  # Green vert
                        GPIO.output(25, GPIO.LOW)  # Green hor
                        GPIO.output(16, GPIO.LOW)  # Red vert
                        print("PRIORITY FOR VERTICAL LANE")
                        semaforo_vertical_livre = True  # Semáforo vertical liberado
                        tempo_iniciado = False  # Reinicia o temporizador quando a via tem prioridade
                        
                if ydr < y < yur:  # horizontal road
                    if x > xur:
                        # Lógica para semáforo horizontal
                        GPIO.output(25, GPIO.HIGH)  # Green hor
                        GPIO.output(16, GPIO.HIGH)  # Red vert
                        GPIO.output(21, GPIO.LOW)  # Red hor
                        GPIO.output(23, GPIO.LOW)  # Green vert
                        print("PRIORITY FOR HORIZONTAL LANE")
                        semaforo_horizontal_livre = True  # Semáforo horizontal liberado
                        tempo_iniciado = False  # Reinicia o temporizador quando a via tem prioridade
                    elif x < xul:
                        # Lógica para semáforo horizontal
                        GPIO.output(25, GPIO.HIGH)  # Green hor
                        GPIO.output(16, GPIO.HIGH)  # Red vert
                        GPIO.output(21, GPIO.LOW)  # Red hor
                        GPIO.output(23, GPIO.LOW)  # Green vert
                        print("PRIORITY FOR HORIZONTAL LANE")
                        semaforo_horizontal_livre = True  # Semáforo horizontal liberado
                        tempo_iniciado = False  # Reinicia o temporizador quando a via tem prioridade
            
            # Se nenhum lado tem prioridade, temporiza para abrir o lado fechado após 90 segundos
            if priority == 0:
                if semaforo_vertical_livre or semaforo_horizontal_livre:
                    # Inicia o temporizador se ainda não iniciado
                    if not tempo_iniciado:
                        t1 = time.time()  # Começa a contagem do tempo
                        tempo_iniciado = True

                    # Verifica o tempo
                    tempo_passado = time.time() - t1
                    if tempo_passado >= tempo_aberto:
                        # Após 90 segundos, libera o semáforo do lado fechado
                        if semaforo_vertical_livre:
                            GPIO.output(25, GPIO.LOW)  # Red hor
                            GPIO.output(16, GPIO.LOW)  # Green vert
                            GPIO.output(21, GPIO.HIGH)  # Green hor
                            GPIO.output(23, GPIO.HIGH)  # Red vert
                            print("Lado fechado (horizontal) liberado após 90 segundos.")

                        if semaforo_horizontal_livre:
                            GPIO.output(21, GPIO.LOW)  # Red hor
                            GPIO.output(23, GPIO.LOW)  # Green vert
                            GPIO.output(25, GPIO.HIGH)  # Green hor
                            GPIO.output(16, GPIO.HIGH)  # Red vert
                            print("Lado fechado (vertical) liberado após 90 segundos.")

    hsvim = cv2.resize(hsv, (500, 500))
    frameim = cv2.resize(frame, (500, 500))
    imstack2 = np.hstack((hsvim, frameim))
    cv2.imshow("Frame + hsv", imstack2)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Finaliza o processo
cam.release()
cv2.destroyAllWindows()
