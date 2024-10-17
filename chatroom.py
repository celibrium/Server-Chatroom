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
        self.server_port = server_port
        serverAddr = socket.gethostbyname(socket.gethostname())

        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.serverSocket.bind(serverAddr, server_port)

        self.clients = {}
        self.messages = []

    def accept_client(self, client_addr, message):
        clientName = message

        # Check if the client's name is in the dict and return False if it is
        if clientName in self.clients.values():
            self.server_socket.sendto("Name already taken".encode(), client_addr)
            return False

        # Otherwise, send a "Welcome" message to the client
        welcomeMessage = "Welcome to the chat!"
        self.server_socket.sendto(welcomeMessage.encode(), client_addr)

        # Add the client's address and name to the clients dictionary
        self.clients[client_addr] = clientName

        # append the client address and user x joined message to the list
        joinMessage = f"User {clientName} joined"
        self.messages.append((client_addr, joinMessage))

        self.broadcast()
        return True
    
    def close_client(self, client_addr):
        # Check if the client exists in the clients dictionary
        if client_addr not in self.clients:
            return False

        clientName = self.clients[client_addr]
        userLeft = f"User {clientName} left"

        # Append the message to the messages list and remove client from dict
        self.messages.append((client_addr, userLeft))
        del self.clients[client_addr]

        self.broadcast()
        return True
    
    def broadcast(self):
        # if messages is empty, return
        if not self.messages:
            return
        
        # Get the most recent message from the messages list
        clientAddr, message = self.messages[-1]

        # Iterate over the clients dictionary
        for c in self.clients:
            if c == clientAddr:
                continue
            
            # Send the message to all clients except the client who sent the message
            self.server_socket.sendto(message.encode(), c)

    def shutdown(self):
        self.message.append((None, 'server-shutdown'))
        self.broadcast()

        # Broadcast the shutdown message to all connected clients
        for client_addr in list(self.clients.keys()):
            self.close_client(client_addr)

        # Close the server socket
        self.server_socket.close()
        print("Server has been shut down.")

    def get_clients_number(self):
        return len(self.clients)
        
    def run(self):
        try:
            while True:
                # Receive a message and the client's address
                data, client_addr = self.server_socket.recvfrom(1024)  # buffer size of 1024 bytes
                message = data.decode('utf-8').strip()

                # Check if the client is joining
                if message.startswith("join"):
                    if not self.accept_client(client_addr, message):
                        # If the name is already taken, notify the client
                        self.server_socket.sendto("Name already taken".encode('utf-8'), client_addr)
                    continue

                # Check if the client is leaving
                if message == "exit":
                    self.close_client(client_addr)
                    continue

                # Handle regular messages from connected clients
                if client_addr in self.clients:
                    # Append the message to the server's message list
                    client_name = self.clients[client_addr]
                    self.messages.append((client_addr, f"{client_name}: {message}"))
                    # Broadcast the message to other clients
                    self.broadcast()
                else:
                    # If the client is not recognized (hasn't joined), ignore the message
                    self.server_socket.sendto("You need to join first.".encode('utf-8'), client_addr)

        except KeyboardInterrupt:
            print("Server is shutting down due to KeyboardInterrupt.")
            self.shutdown()
        except Exception as e:
            print(f"An error occurred: {e}")
            self.shutdown()

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