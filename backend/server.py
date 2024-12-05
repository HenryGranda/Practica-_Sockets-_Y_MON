import ssl
import socket
import threading
import time

host = '127.0.0.1'
port = 12346

# Crear y configurar el socket seguro
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen()

context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(certfile="cert.pem", keyfile="key.pem")
secure_server = context.wrap_socket(server, server_side=True)

clients = {}  # Diccionario {client_socket: nickname}
message_queues = {}  # Diccionario {nickname: [(timestamp, mensaje)]}
last_disconnect = {}  # Diccionario {nickname: timestamp}


def broadcast(message, sender_nickname=None, exclude_nickname=None):
    """
    Envía un mensaje a todos los clientes conectados y lo guarda en las colas de mensajes pendientes,
    excepto para el cliente especificado en exclude_nickname.
    """
    timestamp = time.time()  # Captura el momento actual
    for client, nickname in clients.items():
        if nickname != sender_nickname and nickname != exclude_nickname:  # No enviamos al remitente ni al excluido
            try:
                client.send(message.encode('utf-8'))
            except:
                continue
    # Guardar el mensaje en las colas de todos los clientes desconectados, excepto el que se excluye
    for nickname, queue in message_queues.items():
        if nickname != sender_nickname and nickname != exclude_nickname:
            queue.append((timestamp, message))


def send_pending_messages(client, nickname):
    """Envía los mensajes pendientes al cliente cuando se reconecta."""
    if nickname in message_queues and nickname in last_disconnect:
        disconnect_time = last_disconnect[nickname]
        pending_messages = [
            msg for ts, msg in message_queues[nickname] if ts > disconnect_time
        ]
        # Enviar los mensajes en cola al cliente
        for msg in pending_messages:
            try:
                client.send(msg.encode('utf-8'))
            except:
                pass
        # Limpiar mensajes enviados de la cola
        message_queues[nickname] = [
            (ts, msg) for ts, msg in message_queues[nickname] if ts <= disconnect_time
        ]

def handle(client):
    """Maneja los mensajes de cada cliente."""
    nickname = clients[client]
    while True:
        try:
            message = client.recv(1024).decode('utf-8')
            if not message:
                raise ConnectionResetError("Cliente desconectado.")

            # Ignorar mensajes que solo contienen el apodo
            if message == nickname:
                continue

            # Difundir el mensaje a todos los demás
            full_message = f"{nickname}: {message}"
            broadcast(full_message, sender_nickname=nickname)
        except:
            # Manejar desconexión del cliente
            print(f"{nickname} se ha desconectado.")
            clients.pop(client, None)  # Eliminar de la lista de clientes conectados
            last_disconnect[nickname] = time.time()  # Registrar el tiempo de desconexión
            broadcast(f"{nickname} ha salido del chat.", exclude_nickname=nickname)
            client.close()
            break


def receive():
    """Acepta nuevas conexiones y maneja el registro de apodos."""
    while True:
        client, address = secure_server.accept()
        print(f"Conexión aceptada de {address}")

        # Solicitar el apodo del cliente
        client.send('NICK'.encode('utf-8'))
        nickname = client.recv(1024).decode('utf-8')

        # Verificar si el nickname ya existe, desconectar la conexión previa
        for c, n in clients.items():
            if n == nickname:
                c.close()
                clients.pop(c, None)
                broadcast(f"{nickname} ha sido desconectado por una nueva conexión.")

        # Registrar el cliente con su nickname
        clients[client] = nickname
        if nickname not in message_queues:
            message_queues[nickname] = []  # Crear cola para nuevos usuarios
        if nickname not in last_disconnect:
            last_disconnect[nickname] = 0  # Inicializar tiempo de desconexión

        # **1. Notificar al cliente que está conectado primero**
        client.send("Estás conectado al chat.".encode('utf-8'))

        # **2. Enviar los mensajes pendientes al cliente**
        send_pending_messages(client, nickname)

        # **3. Notificar a los demás usuarios que el cliente se ha unido**
        broadcast(f"{nickname} se ha unido al chat.", sender_nickname=None, exclude_nickname=nickname)

        # Iniciar un hilo para manejar mensajes del cliente
        thread = threading.Thread(target=handle, args=(client,))
        thread.start()


print("Servidor seguro escuchando...")
receive()
