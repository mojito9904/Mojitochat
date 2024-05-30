import time
import hashlib
import socket
import threading
import pandas as pd
import signal
import sys
#codifica utf-8

Utenti = {}                 # Dizionario client:nome
connections = []            # Lista dei client
lock = threading.Lock()     # Per permettere l'accesso simultaneo a più client
port = 12345                # Porta 
server_running = True       # Variabile per controllare lo stato del server
path="/home/angelo/rocca/capolavoro/datautenti.csv"                      #il percorso del file csv

###########################################################################################
#creiamo una classe user che è composta da un client e un nome dell'utente 
class User:
    def __init__(self, name, c):            #inserisce i dati 
        self.name = name
        self.c = c
    def print_data(self):                   #stampa i dati 
        print("Username:", self.name)
        print("client:", self.c)

##########################################################################################
#permette la criptazione della password dell'utente 
def hash_password(password):               
    hasher = hashlib.sha256()               #crea un hash con algoritmo sha256
    hasher.update(password.encode('utf-8')) #converte la stringa della password in una sequenza di byte usando l'encoding UTF-8,
    hashed_password = hasher.hexdigest()    #viene utilizzato per ottenere la rappresentazione esadecimale dell'hash 
    return hashed_password                  #returna la password 


###########################################################################################
#permette di mandare un messaggio broadcast a tutti i client conessi 
def broadcast(message, exclude_socket=None): 
    with lock:                                              #cicliamo tutta la lista lock 
        for client in connections:                          #per tutti i client in connections
            if client != exclude_socket:      #quando il client è diverso da quello che ha mandato il messggio  si prova a mandare il messaggio a quel client
                try:
                    client.send(message.encode())
                except: 
                    client.close()
                    remove_user(client)

###########################################################################################
#permette di vedere tutti gli utenti online
def online(connection):
    print("Utenti online:")
    time.sleep(0.3)
    connection.send("______________________________".encode())
    for nome in Utenti.values():                          #cicliamo tutti i nomi che troviamo nella lista utenti 
        time.sleep(0.3)
        connection.send(('           >'+nome).encode())            #e li mandiamo al client e solo a quello che l'ha chiesto
        print("Nome:", nome)
        time.sleep(0.3)
    connection.send("______________________________".encode())
    time.sleep(0.3)

############################################################################################
#permette di eliminare il client che si è disconesso dalla lista e dal dizionario 
def remove_user(connection):
    with lock:
        if connection in Utenti:                    #controliamo se il client è nel dizionario e se c'è lo elimina 
            del Utenti[connection]
        if connection in connections:               #se il client è nella lista connections lo eliminiamo 
            connections.remove(connection)

###########################################################################################
#da qui c'è tutta la gestione del client 
def gestione_client(connection, address):
    print('Connecting from', address)
    nome = login(connection)                        #ci prendiamo il nome dalla funzione login 
    if nome!="nope":                                #se il nome è diverso da nope
        utente = User(nome, connection)             #creiamo un oggetto utente con nome e connection
    
        with lock:                                  #inseriamo in Utenti il nome e il client 
            Utenti[connection] = nome       
            connections.append(connection)          #nelle lista connections inseriamo il client 
        
        utente.print_data()                                         #stampiamo i dati dell'utente 
        broadcast(f"{utente.name} è entrato in chat", connection)   #messaggio di broadcast che dice che il nome utente è entrato in chart
        
        try:  
            while True:                                             #ciclo while infinito
                message = connection.recv(1024).decode()            #riceviamo i messaggi dall'utente 
                if not message:                                     #se non ci sono messaggi 
                    break                                           #interrompiamo il ciclo 
                elif message == "/online":                          #se il messaggio è uguale a /online
                    online(connection)                              #funzione per vedere la lista di utenti online
                elif message == "/close":                           #se il messaggio è uguale a /close
                    break                                           #interrompiamo il ciclo
                else:                                                   
                    broadcast(f"{utente.name}: {message}", connection)  #senno l'utente si è disconesso 
        except:
            pass 
        finally:                                                        #alla fine de ciclo e del try 
            remove_user(connection)                                     #rimuoviamo l'utente dalle varie liste
            connection.close()                                          #chiudiamo la sua conessione 
            broadcast(f"{utente.name} si è disconnesso", connection)    #mandiamo a tutti un messaggio 
    else:
        return 
        
################################################################################################à
#fase che gestisce tutto il login 
def login(connection):
    df = pd.read_csv(path)        #creiamo un dataframe con i dati del csv
    print(df.columns)                                                       #stampiamo le colonne 
    connection.send("start login".encode())
    time.sleep(0.4)
    connection.send("inserire nome".encode())
    time.sleep(0.4)
    connection.send("stop".encode())
    name = connection.recv(1024).decode()                                   #decodificiamo il nome dell'utente 
    for user in Utenti.values():                                            #ciclo per prendere tutti i nomi negli utenti online 
        if user == name:                                                    #se il nome è gia online
            connection.send("utente già online".encode()) 
            time.sleep(0.2)                  
            connection.send("non fare il furbetto".encode())                    
            time.sleep(0.4)
            connection.send("nope".encode())                                #mandiamo un avvisso 
            return "nope"                                                   #returniamo un messaggio che ci servirà
    if name in df["Nome"].values:                                           # se invece il nome è nella colonna del dataframe 
        index = df[df["Nome"] == name].index[0]                             #prendiamo l'indice dove si trova il nome
        print(index)            
        connection.send("inserire password".encode())
        time.sleep(0.4)
        valoue = df.iloc[index, 1]                                          #prendiamo la password cryptata che abbiamo nel dataframe
        tentativi=0
        while tentativi<3:                                                  #qui facciamo un ciclo while per tre tentativi dell'utente per inserire la password
            connection.send("stop".encode())
            password = connection.recv(1024).decode()
            pas = hash_password(password)                                   #qui criptiamo la password che inserisce l'utente 
            if valoue == pas:                                               #se le password sono uguali facciamo entrare l'utente
                print(valoue)
                connection.send("Welcome back to".encode())
                time.sleep(0.4)
                break
            else:                                                           #se sono diverse gli diamo altri tentativi fino a n=3
                connection.send("password sbagliata".encode())
                time.sleep(0.4)
                connection.send(f"tentativi rimasti:{2-tentativi}".encode())
                tentativi += 1
                time.sleep(0.4)
        if tentativi==3:
            connection.send("tentativi finiti".encode()) 
            time.sleep(0.3)
            connection.send("nope".encode())                                #mandiamo un avvisso 
            return "nope"
    else:
        connection.send("creazione utente si prega di inserire una password con lettere e numeri".encode())    #se il nome non c'è
        time.sleep(0.4)         
        connection.send("stop".encode())
        password = connection.recv(1024).decode()
        connection.send("Welcome to ".encode()) 
        pas = hash_password(password)                                                                         #prendiamo la password e la criptiamo 
        new_Utente = [name, pas]
        df.loc[len(df)] = new_Utente
        df.to_csv(path, index=False)                                  #salviamo le informazioni dell'utente nel csv
    time.sleep(0.4)
    connection.send("#END".encode())
    return name                     #returniamo il nome

#############################################################################################################
#startiamo il server prendendo la variabile globare server_running
def start_server():
    global server_running
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('localhost', port))
    s.listen(25)                                                #il server può accettare il massimo di 25 client
    print("Server is listening")

    def signal_handler(sig, frame):                         #funzione che gestisce il ctrl+c nel server 
        global server_running
        print("\nServer shutting down...")
        server_running = False
        for conn in connections:                            #se chiudiamo il server scolleggiamo anche tutti gli utenti 
            conn.send("close server".encode())
        s.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    while server_running:
        try:
            c, addr = s.accept()
            threading.Thread(target=gestione_client, args=[c, addr]).start()        #accettiamo il client e creiamo un thread per il client 
        except OSError:
            break

if __name__ == "__main__":
    start_server()
