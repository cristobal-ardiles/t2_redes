import time
import jsockets
import sys

MAX_DIGITS = 4
N_TRIES = 10
N_ARGS = 7

def exit_no_ack(sec_number):
    """Imprime un error y aborta el protocolo al no recibir confimación de recepción"""
    print(f"Fatal: no se recibió confimación del paquete {sec_number}")
    sys.exit(1)

def exit_timeout():
    print("Fatal: no se recibió un paquete a tiempo")
    sys.exit(1)

def exit_wrong_package(expected, received):
    print(f"Fatal, received wrong package. Expected {expected}, received {received}")
    sys.exit(1)

def send_msg(socket,header,msg,timeout):
    """Envía un mensaje a través del socket, esperando timeout segundos 
    por el ACK de confimación"""
    global sec_number
    
    tries = 0 
    while tries < N_TRIES:
        # Construimos el mensaje 
        full_msg = bytearray()
        full_msg += header.encode()
        full_msg += str(sec_number).encode()
        full_msg += msg
        # Enviamos el mensaje a través del socket
        sent = socket.send(full_msg)
        socket.settimeout(timeout)
        while True:
            try:
                ack = socket.recv(4096).decode()
                if ack[0] == 'A' and ack[1] == str(sec_number):
                    break
            except:
                ack = None
                break
        if ack:
            break
        else:
            tries += 1

    sec_number = (sec_number+1)%10
    socket.settimeout(None)
    #Chequeamos haber recibido la confirmación
    if not ack:
        exit_no_ack(sec_number)
    
    return sent, ack

## Intenta recibir un mensaje en un socket. 
def try_to_receive(sock, timeout, max_size, tries=1):
    """
    Intenta recibir un mensaje del socket, enviando la confirmación de recepción
    Si no recibe un mensaje a tiempo, error
    """
    sock.settimeout(timeout)
    package = None
    tries = 0
    while tries < N_TRIES:
        try:
            package = sock.recv(max_size)
            # Recibimos un paquete, enviamos la respuesta
            # Almacenamos solamente el header y el número de secuencia
            sock.settimeout(None)
            container = bytearray(2)
            container[0] = ord('A')
            container[1] = package[1]
            sock.send(container)
            return package
        except:
            tries+=1  

if len(sys.argv) != N_ARGS:
    print("Use: "+sys.argv[0]+"timeout packsize filein fileout host port")
    sys.exit(1)

timeout, packsize, filein, fileout, host, port = sys.argv[1:]

## Conexión al servidor
sv_socket = jsockets.socket_udp_connect(host, int(port))

##Inicializamos el número de paquete
sec_number = 0

#### Iniciamos el protocolo

## Enviamos el paquete al servidor y esperamos la respuesta
t0 = time.time()
msg = packsize.zfill(MAX_DIGITS)+timeout.zfill(MAX_DIGITS)
bytes_sent, response = send_msg(sv_socket,"C",msg.encode(),int(timeout))
package_size, timeout = int(response[2:6]), int(response[6:])
timeout = timeout / 1000 
print("Tamaño de paquete acordado: ", package_size)
print("Timeout acordado ", timeout, " [s]")

total_bytes_sent = 0

## Aquí ya tenemos el tamaño del paquete acordado 
with open(filein,"rb") as input:
    chunk = input.read(package_size)
    while chunk:
        # Creamos el mensaje como un bytearray
        #Enviamos el mensaje
        bytes_sent, _ = send_msg(sv_socket,"D",chunk,timeout)
        total_bytes_sent += bytes_sent
        #Volvemos a leer un pedazo de texto
        chunk = input.read(package_size)
# Cuando se acaba el mensaje, enviamos una E
# Este mensaje incluye solo el header, es decir, el contenido es vacío
send_msg(sv_socket,"E",bytearray(),timeout)

print("Archivo enviado, esperando respuesta")

#Escribimos la respuesta 
total_bytes_recvd = 0
with open(fileout,"wb") as output:
    response = try_to_receive(sv_socket,timeout,package_size+2)
    # Obtenemos el primer byte para asegurarnos de recibir el paquete correcto
    # Recimos paquetes hasta que no sea más contenido
    while response[0] == ord("D"):
        output.write(response[2:])
        total_bytes_recvd += len(response)
        response = try_to_receive(sv_socket,timeout,package_size+2)
        
    # Si recibo una letra distinta a 'D', entonces chequeo que sea una 'E'
    if response[0] != ord("E"):
        exit_wrong_package("E",response[0])

tf = time.time()

print("Archivo recibido, desplegando resultados")

bandwidth = (total_bytes_sent+total_bytes_recvd)/(tf-t0)
print(f"""Bytes: {total_bytes_sent+total_bytes_recvd},t ime={tf-t0},bw={bandwidth/(1024*1024)} MB/s
""")
sv_socket.close()

