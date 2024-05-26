import socket
import threading
import signal
import time
import sys

port = 12345
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

########################################################################################
#legge tutte le line nella ascii art e le stampa 
def art():
    for line in ascii_art:
        print(line)
        time.sleep(0.3)

#######################################################################################
#gestisce un messaggio che arriva dal server
def receive_messages(client_socket): 
    global client_running
    while client_running: 
        try: 
            message = client_socket.recv(1024).decode()             #riceve il messaggio  
            if message:                                             #se c'è il messaggio lo stampa  
                print(message)  
            if message==("close server"):                           #se il mesg che arriva è close server si chiude il socket                  
                client_socket.close()
        except: 
            client_socket.close() 
            break

#########################################################################################
#leggere tutta la fase di login 
def lettura_login(s):
    while True:        
        msg = s.recv(1024).decode()
        if msg=="nope":
            return False
        if msg == "#END":
            return True
        if msg != "stop":
            print(msg)
        if msg == "stop":
            data = input('')
            s.send(data.lower().encode())

############################################################################################
#gestisce tutto 
def main():
    global client_running
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('127.0.0.1', port))                                  #ci connetttiamo al server

    def signal_handler(sig, frame):                                 #gestisce il ctrl+c
        global client_running
        print("\nClient shutting down...")
        client_running = False
        s.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    if lettura_login(s):                                                    #se il login è andata a buon fine va avanti 
        art()                                                               #stampiamo l'ascii art
        threading.Thread(target=receive_messages, args=(s,)).start()        #diamo inizio al thread
        
        print("Ricordati sei già dentro una chat")
        print("Comandi:")
        print("/online per vedere le persone online")
        print("/close per chiudere la chat")
        while client_running:
            message = input("")                                           #qui gestiamo tutti i comandi che inserisce l'utente 
            if message.lower() == "/close":
                s.send(message.encode('utf-8'))
                s.close()
                break
            if message.lower() == "/online":
                s.send(message.encode('utf-8'))
            else:
                s.send(message.encode('utf-8'))
    else:
        return

if __name__ == "__main__":
    main()
