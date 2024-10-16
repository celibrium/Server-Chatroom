import socket
import threading 

class ServerTCP:
    def __init__(self, server_port):
        # get local machines IP address
        self.server_port = server_port
        addr = socket.gethostbyname(socket.gethostname())

        # create and bind socket
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverSocket.bind((addr,server_port))

        # listen for incoming connections
        self.serverSocket.listen(10)
        print(f"Listening on server address {addr} and port {server_port}")

        # initialize empty dict to store clients address and name
        self.clients = {}

        # events to handle server and message state
        self.runEvent = threading.Event()
        self.handleEvent = threading.Event()


    def accept_client(self):
        try:
            # accept client connection
            clientSocket, clientAddr = self.serverSocket.accept()
            print(f"Recieved connection from {clientAddr}")

            # stores name into variable
            clientName = clientSocket.recv(1024).decode()

            # checks if the client name is in dict
            if clientName in self.clients.values():
                clientSocket.sendall("Name already taken".encode())
                clientSocket.close()
                return False
            else:
            #if not, then add client name to dict and broadcast join
                clientSocket.sendall(f"Welcome {clientName}.".encode())
                self.clients[clientSocket] = clientName
                self.broadcast(clientSocket, 'join')
                return True

        except Exception as e:
            print(f"Error accepting client connection: {e}")
            return False

    def close_client(self, client_socket):
        try:
            # check if the given client socket is in the dict, if it is delete from dict and close socket
            if client_socket in self.clients:
                clientName = self.clients.get(client_socket)
                del self.clients[client_socket]

                client_socket.close()
                print(f"Client socket with name {clientName} closed")
                return True
            # if socket not found return false
            else:
                print("client not found")
                return False
            
        # check for any errors in closing socket
        except Exception as e:
            print(f"Error in closing client {e}")
            return False

    def broadcast(self, client_socket_sent, message):
        # takes client name from given socket
        clientName = self.clients[client_socket_sent]

        # assigns appropriate message depending on message
        if message == 'join':
            broadcastMessage = f"User {clientName} joined"
        elif message == 'exit':
            broadcastMessage = f"User {clientName} left"
        else:
            broadcastMessage = f"{clientName}: {message}"

        # sends message to all clients except for given client
        for c in self.clients:
            if c != client_socket_sent:
                c.sendall(broadcastMessage.encode())


    def shutdown(self):
        try:
            # uses the broadcast message to send a server-shutdown message
            self.broadcast(None, 'server-shutdown')

            # uses the close client to close all client sockets
            for c in list(self.clients.keys()):
                self.close_client(c) 

            # sets the events to which will make it True
            self.runEvent.set()
            self.handleEvent.set()

            self.serverSocket.close()
            print("server socket closed")
        
        except Exception as e:
            print(f"Error during shutdown {e}")
        
    def get_clients_number(self):
        return len(self.clients)
        
    def handle_client(self, client_socket):
        try:
            while self.handleEvent.is_set() == False:
                message = client_socket.recv(1028).decode()

                if message == 'exit':
                    self.broadcast(client_socket, 'exit')
                else:
                    self.broadcast(client_socket, message)

        except Exception as e:
            print(f"Error handling client {client_socket}: {e}")

    def run(self):
        print("Server started.")
        try:
            while self.runEvent.is_set() == False:  
                # Accept a new client connection
                clientSocket, clientAddr = self.serverSocket.accept()
                print(f"Accepted connection from {clientAddr}")
                
                # Handle the new client
                if self.accept_client(clientSocket):
                    # If the client is accepted (i.e., has a unique name), start a new thread to handle the client
                    clientThread = threading.Thread(target=self.handle_client, args=(clientSocket))
                    # exits when main program exits
                    clientThread.daemon = True 
                    clientThread.start()
        
        except KeyboardInterrupt:
            print("Keyboard interrupt, server shutting down")
        
        finally:
            self.shutdown()

class ClientTCP:
    def __init__(self, client_name, server_port):
        # initialize instance variables
        self.client_name = client_name
        self.server_port = server_port

        # get server address and initalize client socket
        self.serverAddr = socket.gethostbyname(socket.gethostname())
        self.clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # make variables to handle threading events
        self.exitRun = threading.Event()
        self.exitReceive = threading.Event()

    def connect_server(self):
        try:
            # connect the client sokcet to the given addr and port
            self.clientSocket.connect((self.serverAddr, self.server_port))

            # send thc client name to the server and get a response
            self.clientSocket.sendall(self.client_name.encode())
            response = self.lientSocket.recv(1028).decode()

            if 'Welcome' in response:
                print(f"{response}")
                return True
            else:
                return False
            
        except Exception as e:
            print(f"Error connecting to the server: {e}")
            return False

    def send(self, text):
        self.clientSocket.sendall(text.encode())

    def receive(self):
        # receive messages until message is server shutdown in which events will be set to true
        while self.exitReceive.is_set() == False:
            message = self.clientSocket.recv(1028).decode()

            if message == 'server-shutdown':
                self.exitReceive.set()
                self.exitRun.set()
            else:
                print(message)

    def run(self):
        try:
            self.connect_server()

            receiveThread = threading.Thread(target=self.receive)
            receiveThread.start()

            while self.exit_run.is_set() == False:
                userInput = input("Enter message (type 'exit' to leave): ")
                # if the user input is exit then events will be set
                if userInput == 'exit':
                    self.send('exit')
                    self.exit_run.set() 
                    self.exit_receive.set()  
                    break

                # Otherwise, send the message to the server
                self.send(userInput)

        except KeyboardInterrupt:
            print("KeyboardInterrupt, exiting")
            self.send('exit')
            self.exit_receive.set()
            self.exit_run.set() 
            
        finally:
            receiveThread.join()
            print("Client has exited.")

class ServerUDP:
    def __init__(self, server_port):
        pass
    def accept_client(self, client_addr, message):
        pass
    def close_client(self, client_addr):
        pass
    def broadcast(self):
        pass
    def shutdown(self):
        pass
    def get_clients_number(self):
        pass
    def run(self):
        pass

class ClientUDP:
    def __init__(self, client_name, server_port):
        pass
    def connect_server(self):
        pass
    def send(self, text):
        pass
    def receive(self):
        pass
    def run(self):
        pass