import time
import hashlib
import socket
import threading
import pandas as pd
import signal
import sys
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

Utenti = {}
connections = []
lock = threading.Lock()

# Porta dinamica per Render
port = int(os.environ.get("PORT", 12345))

# Percorso CSV – Render lo mette nella stessa cartella
path = "./utenti.csv"

server_running = True

###############################################
# Classe User
class User:
    def __init__(self, name, c):
        self.name = name
        self.c = c

    def print_data(self):
        print("Username:", self.name)
        print("client:", self.c)

###############################################
def hash_password(password):
    hasher = hashlib.sha256()
    hasher.update(password.encode('utf-8'))
    return hasher.hexdigest()

###############################################
def broadcast(message, exclude_socket=None):
    with lock:
        for client in connections:
            if client != exclude_socket:
                try:
                    client.send(message.encode())
                except:
                    client.close()
                    remove_user(client)

###############################################
def online(connection):
    connection.send("______________________________".encode())
    for nome in Utenti.values():
        time.sleep(0.1)
        connection.send(("           >" + nome).encode())
    connection.send("______________________________".encode())

###############################################
def remove_user(connection):
    with lock:
        if connection in Utenti:
            del Utenti[connection]
        if connection in connections:
            connections.remove(connection)

###############################################
def gestione_client(connection, address):
    print('Connecting from', address)
    nome = login(connection)
    if nome == "nope":
        return

    utente = User(nome, connection)

    with lock:
        Utenti[connection] = nome
        connections.append(connection)

    utente.print_data()
    broadcast(f"{utente.name} è entrato in chat", connection)

    try:
        while True:
            message = connection.recv(1024).decode()
            if not message:
                break
            elif message == "/online":
                online(connection)
            elif message == "/close":
                break
            else:
                broadcast(f"{utente.name}: {message}", connection)
    except:
        pass
    finally:
        remove_user(connection)
        connection.close()
        broadcast(f"{utente.name} si è disconnesso", connection)

###############################################
def login(connection):
    df = pd.read_csv(path)
    connection.send("start login".encode())
    time.sleep(0.3)
    connection.send("inserire nome".encode())
    time.sleep(0.3)
    connection.send("stop".encode())

    name = connection.recv(1024).decode()

    # Utente già online
    for u in Utenti.values():
        if u == name:
            connection.send("utente già online".encode())
            time.sleep(0.2)
            connection.send("non fare il furbetto".encode())
            time.sleep(0.2)
            connection.send("nope".encode())
            return "nope"

    # Login normale
    if name in df["Nome"].values:
        index = df[df["Nome"] == name].index[0]
        valoue = df.iloc[index, 1]

        connection.send("inserire password".encode())
        time.sleep(0.3)

        tentativi = 0
        while tentativi < 3:
            connection.send("stop".encode())
            password = connection.recv(1024).decode()
            pas = hash_password(password)

            if pas == valoue:
                connection.send("Welcome back to".encode())
                break
            else:
                connection.send("password sbagliata".encode())
                connection.send(f"tentativi rimasti:{2 - tentativi}".encode())
                tentativi += 1

        if tentativi == 3:
            connection.send("tentativi finiti".encode())
            connection.send("nope".encode())
            return "nope"

    else:
        # Nuovo utente
        connection.send("creazione utente si prega di inserire una password con lettere e numeri".encode())
        time.sleep(0.3)
        connection.send("stop".encode())
        password = connection.recv(1024).decode()

        pas = hash_password(password)
        df.loc[len(df)] = [name, pas]
        df.to_csv(path, index=False)
        connection.send("Welcome to ".encode())

    connection.send("#END".encode())
    return name

###############################################
# Server socket
def start_socket_server():
    global server_running

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Render richiede 0.0.0.0
    s.bind(("0.0.0.0", port))
    s.listen(25)

    print(f"Socket Server attivo sulla porta {port}")

    while server_running:
        try:
            c, addr = s.accept()
            threading.Thread(target=gestione_client, args=[c, addr]).start()
        except OSError:
            break

###############################################
# Mini web server per "wake-up"
class WakeHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Server Attivo")

def start_http_server():
    http_port = 8080   # porta libera su Render
    server = HTTPServer(("0.0.0.0", http_port), WakeHandler)
    print("HTTP Wake server su porta 8080")
    server.serve_forever()

###############################################
if __name__ == "__main__":
    # Avviamo entrambi i server
    threading.Thread(target=start_http_server, daemon=True).start()
    start_socket_server()
