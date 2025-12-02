import socket
import threading
import signal
import time
import sys

# dominio Render
HOST = "mojitochat.onrender.com"
PORT = 443   # Render usa la porta HTTPS, viene automaticamente instradata al tuo server

client_running = True

ascii_art = [
        r'    ___  ___      _ _ _        _____ _           _     ',
        r'    |  \/  |     (_|_) |      /  __ \ |         | |    ',
        r'    | .  . | ___  _ _| |_ ___ | /  \/ |__   __ _| |_   ',
        r'    | |\/| |/ _ \| | | __/ _ \| |   |  _ \ / _  | __|  ',
        r'    | |  | | (_) | | | || (_) | \__/\ | | | (_| | |_   ',
        r'    \_|  |_/\___/| |_|\__\___/ \____/_| |_|\__ _|\__|  ',
        r'                _/ |                                   ',
        r'               |__/                                    ',
    ]

def art():
    for line in ascii_art:
        print(line)
        time.sleep(0.3)

def receive_messages(client_socket): 
    global client_running
    while client_running: 
        try: 
            message = client_socket.recv(1024).decode()
            if message:
                print(message)
            if message == "close server":
                client_socket.close()
        except:
            client_socket.close()
            break

def lettura_login(s):
    while True:
        msg = s.recv(1024).decode()
        if msg == "nope":
            return False
        if msg == "#END":
            return True
        if msg != "stop":
            print(msg)
        if msg == "stop":
            data = input("")
            s.send(data.lower().encode())

def main():
    global client_running
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    print(f"Connessione a {HOST} ...")
    s.connect((HOST, PORT))

    def signal_handler(sig, frame):
        global client_running
        print("\nClient shutting down...")
        client_running = False
        s.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    if lettura_login(s):
        art()
        threading.Thread(target=receive_messages, args=(s,)).start()

        print("Ricordati: sei già dentro una chat.")
        print("Comandi:")
        print("/online per vedere le persone online")
        print("/close per chiudere la chat")

        while client_running:
            message = input("")
            s.send(message.encode('utf-8'))
            if message.lower() == "/close":
                s.close()
                break
    else:
        return

if __name__ == "__main__":
    main()
