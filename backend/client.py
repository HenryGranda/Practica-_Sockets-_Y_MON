import ssl
import socket
import threading
import tkinter as tk
from tkinter import scrolledtext
import time

# Variables globales
host = '127.0.0.1'
port = 12346
secure_client = None
connected = False
nickname = ""
nickname_confirmed = False  # Variable para controlar la confirmación del apodo

# Crear socket
def create_secure_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    context = ssl.create_default_context(cafile="cert.pem")
    secure_client = context.wrap_socket(client, server_hostname=host)
    return secure_client

# Intentar conectar al servidor con reconexión
def connect_to_server():
    global secure_client, connected, nickname
    while not connected:
        try:
            secure_client = create_secure_client()
            secure_client.connect((host, port))
            connected = True
            secure_client.send(nickname.encode('utf-8'))
            send_button.config(state=tk.NORMAL)  # Habilitar botón de enviar al conectarse
            threading.Thread(target=receive_messages, daemon=True).start()
        except Exception as e:
            if not connected:
                chat_box_insert(f"No se pudo conectar: {e}. Reintentando en 5 segundos...")
                time.sleep(5)


# Insertar mensajes en la caja de texto
def chat_box_insert(message):
    chat_box.config(state=tk.NORMAL)
    chat_box.insert(tk.END, f"{message}\n")
    chat_box.config(state=tk.DISABLED)
    chat_box.yview(tk.END)

def receive_messages():
    """Recibe mensajes del servidor y los muestra en el cuadro de texto."""
    global connected
    while connected:
        try:
            message = secure_client.recv(1024).decode('utf-8')
            if not message:
                raise ConnectionResetError

            # Si el servidor solicita el apodo, responder y continuar
            if message == 'NICK':
                secure_client.send(nickname.encode('utf-8'))
            else:
                # Mostrar cualquier otro mensaje en el cuadro de texto
                chat_box_insert(message)
        except:
            connected = False
            chat_box_insert("Se perdió la conexión. Reconectando...")
            send_button.config(state=tk.DISABLED)  # Deshabilitar hasta reconexión
            connect_to_server()
            break


# Enviar mensajes al servidor
def send_message(event=None):
    global secure_client, connected
    message = message_entry.get().strip()
    if connected and message:
        try:
            secure_client.send(message.encode('utf-8'))
            chat_box_insert(f"Tú: {message}")  # Mostrar el mensaje enviado en la propia caja de texto
            message_entry.delete(0, tk.END)
        except Exception as e:
            chat_box_insert(f"Error al enviar el mensaje: {e}")
    else:
        chat_box_insert("No estás conectado al servidor.")


# Confirmar el apodo
def confirm_name():
    global nickname
    nickname = name_entry.get().strip()
    if nickname:
        name_entry.config(state=tk.DISABLED)
        confirm_button.config(state=tk.DISABLED)
        send_button.config(state=tk.NORMAL)  # Habilitar el botón de enviar
        threading.Thread(target=connect_to_server, daemon=True).start()

# Configurar la interfaz
def setup_gui():
    global nickname, chat_box, message_entry, send_button, name_entry, confirm_button

    # Configurar ventana principal
    root.title("Chat en Tiempo Real")
    root.geometry("500x500")
    root.configure(bg="#282c34")

    # Marco para entrada del nombre
    frame_nombre = tk.Frame(root, bg="#282c34")
    frame_nombre.pack(pady=10)
    tk.Label(frame_nombre, text="Ingresa tu Nombre:", font=("Arial", 14), bg="#282c34", fg="white").pack(side=tk.LEFT, padx=5)
    name_entry = tk.Entry(frame_nombre, font=("Arial", 12), width=20)
    name_entry.pack(side=tk.LEFT, padx=5)
    confirm_button = tk.Button(frame_nombre, text="Confirmar", command=confirm_name, bg="#61afef", fg="white", font=("Arial", 12))
    confirm_button.pack(side=tk.LEFT)

    # Caja de texto para mostrar mensajes
    chat_box = scrolledtext.ScrolledText(root, state='disabled', width=60, height=20, bg="#1e2127", fg="white", font=("Courier", 12))
    chat_box.pack(pady=10, padx=10)

    # Marco para entrada de mensajes
    entry_frame = tk.Frame(root, bg="#282c34")
    entry_frame.pack(pady=10)

    # Entrada de mensajes
    message_entry = tk.Entry(entry_frame, width=40, font=("Arial", 12), bg="#ECF0F1")
    message_entry.pack(side=tk.LEFT, padx=5)
    message_entry.bind("<Return>", send_message)

    # Botón para enviar mensajes
    send_button = tk.Button(entry_frame, text="Enviar", command=send_message, bg="#98c379", fg="white", font=("Arial", 12), state=tk.DISABLED)
    send_button.pack(side=tk.LEFT)

# Iniciar la aplicación
root = tk.Tk()
setup_gui()
root.mainloop()
