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

# Configurar la interfaz gráfica
def setup_gui():
    global nickname, chat_box, message_entry, send_button, name_entry, confirm_button

    # Configurar ventana principal
    root.title("Chat en Tiempo Real")
    root.geometry("600x600")
    root.configure(bg="#2c3e50")

    # Marco superior para el título
    title_frame = tk.Frame(root, bg="#34495e", height=50)
    title_frame.pack(fill=tk.X)
    tk.Label(
        title_frame,
        text="Chat en Tiempo Real",
        font=("Arial", 18, "bold"),
        bg="#34495e",
        fg="white",
        pady=10,
    ).pack()

    # Marco para la entrada del nombre
    frame_nombre = tk.Frame(root, bg="#2c3e50", pady=10)
    frame_nombre.pack()
    tk.Label(
        frame_nombre,
        text="Ingresa tu Nombre:",
        font=("Arial", 12),
        bg="#2c3e50",
        fg="white",
    ).pack(side=tk.LEFT, padx=5)
    name_entry = tk.Entry(frame_nombre, font=("Arial", 12), width=20, bg="#ecf0f1")
    name_entry.pack(side=tk.LEFT, padx=5)
    confirm_button = tk.Button(
        frame_nombre,
        text="Confirmar",
        command=confirm_name,
        bg="#3498db",
        fg="white",
        font=("Arial", 12, "bold"),
        width=10,
    )
    confirm_button.pack(side=tk.LEFT, padx=5)

    # Marco para la caja de texto de mensajes
    chat_frame = tk.Frame(root, bg="#2c3e50", pady=10)
    chat_frame.pack(fill=tk.BOTH, expand=True)
    chat_box = scrolledtext.ScrolledText(
        chat_frame,
        state="disabled",
        bg="#1e272e",
        fg="white",
        font=("Courier", 12),
        wrap=tk.WORD,
        height=20,
    )
    chat_box.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # Marco para entrada de mensajes
    entry_frame = tk.Frame(root, bg="#2c3e50", pady=10)
    entry_frame.pack(fill=tk.X)
    message_entry = tk.Entry(
        entry_frame, width=50, font=("Arial", 12), bg="#f1f2f6"
    )
    message_entry.pack(side=tk.LEFT, padx=10, pady=5, fill=tk.X, expand=True)
    message_entry.bind("<Return>", send_message)

    # Botón para enviar mensajes
    send_button = tk.Button(
        entry_frame,
        text="Enviar",
        command=send_message,
        bg="#2ecc71",
        fg="white",
        font=("Arial", 12, "bold"),
        state=tk.DISABLED,
        width=12,
    )
    send_button.pack(side=tk.LEFT, padx=10)

# Iniciar la aplicación
root = tk.Tk()
setup_gui()
root.mainloop()
