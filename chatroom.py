import socket
import threading 
import select


class ServerTCP:
    def __init__(self, server_port):
        # get local machines IP address
        self.server_port = server_port
        addr = socket.gethostbyname(socket.gethostname())

        # create and bind socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((addr,server_port))

        # listen for incoming connections
        self.server_socket.listen(10)
        print(f"Listening on server address {addr} and port {server_port}")

        self.server_socket.setblocking(False) 

        # initialize empty dict to store clients address and name
        self.clients = {}
        self.sockets = [self.server_socket]

        # events to handle server and message state
        self.run_event = threading.Event()
        self.handle_event = threading.Event()


    def accept_client(self):
        #import pdb; pdb.set_trace()
        try:
            # accept client connection
            client_socket, clientAddr = self.server_socket.accept()
            print(f"Received connection from {clientAddr}")

            client_socket.setblocking(False)  # Non-blocking mode
            self.sockets.append(client_socket)  # Add to monitored sockets

            readable, _, _ = select.select([client_socket], [], [], 1)
            if readable:
                # stores name into variable
                clientName = client_socket.recv(1024).decode()

                # checks if the client name is in dict
                if clientName in self.clients.values():
                    client_socket.sendall("Name already taken".encode())
                    
                    #client_socket.close()
                    return False
                else:
                #if not, then add client name to dict nd broadcast join
                    client_socket.sendall(f"Welcome {clientName}.".encode())
                    self.clients[client_socket] = clientName
                    self.broadcast(client_socket, 'join')

                    clientThread = threading.Thread(target=self.handle_client, args=(client_socket,))
                    clientThread.daemon = True  
                    clientThread.start()

                    return True

        except Exception as e:
            print(f"Error accepting client connection: {e}")
            return False

    def close_client(self, client_socket):
        try:
            # check if the given client socket is in the dict, if it is delete from dict and close socket
            if client_socket in self.clients:
                clientName = self.clients.get(client_socket)
                self.sockets.remove(client_socket)
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
            self.run_event.set()
            self.handle_event.set()

            self.server_socket.close()
            print("server socket closed")
        
        except Exception as e:
            print(f"Error during shutdown {e}")
        
    def get_clients_number(self):
        return len(self.clients)
    
        
    def handle_client(self, client_socket):
        try:
            while self.handle_event.is_set() == False:
                readable, _, _ = select.select([client_socket], [], [], 1)
                if readable:
                    message = client_socket.recv(1028).decode()

                    if not message or message == 'exit':
                        self.broadcast(client_socket, 'exit')
                        self.close_client(client_socket)  
                        break  
                    else:
                        self.broadcast(client_socket, message)

        except Exception as e:
            print(f"Error handling client {client_socket}: {e}")

    def run(self):
        print("Server started.")
        try:
            while self.run_event.is_set() == False:
                readable, _, _ = select.select(self.sockets, [], [], 1)
                for socket in readable:
                    if socket == self.server_socket:
                        self.accept_client()
        
        except KeyboardInterrupt:
            print("Keyboard interrupt, server shutting down")
        except Exception as e:
            print(f"Error running: {e}")
        
        finally:
            self.shutdown()

class ClientTCP:
    def __init__(self, client_name, server_port):
        # initialize instance variables
        self.client_name = client_name
        self.server_port = server_port

        # get server address and initalize client socket
        self.server_addr = socket.gethostbyname(socket.gethostname())
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # make variables to handle threading events
        self.exit_run = threading.Event()
        self.exit_receive = threading.Event()

    def connect_server(self):
        try:
            # connect the client sokcet to the given addr and port
            self.client_socket.connect((self.server_addr, self.server_port))

            # send the client name to the server and get a response
            self.client_socket.sendall(self.client_name.encode())

            readable, _, _ = select.select([self.client_socket], [], [], 1)
            if readable:
                response = self.client_socket.recv(1028).decode()

                if 'Welcome' in response:
                    print(f"{response}")
                    return True
                elif 'taken' in response:
                    print(f"{response}")
                    self.client_socket.close() 
                    self.exit_run.set()  
                    self.exit_receive.set()
                    return False
                else:
                    return False
            
        except Exception as e:
            print(f"Error connecting to the server: {e}")
            return False

    def send(self, text):
        self.client_socket.sendall(text.encode())

    def receive(self):
        # receive messages until message is server shutdown in which events will be set to true
        while self.exit_receive.is_set() == False:
            try:
                # Check if the socket is still valid
                if self.client_socket.fileno() == -1:
                    print("Socket is closed. Exiting receive loop.")
                    break

                readable, _, _ = select.select([self.client_socket], [], [], 1)
                if readable:
                        message = self.client_socket.recv(1028).decode()
                        if not message:
                            print("Server disconnected.")
                            self.exit_receive.set()
                            break  
                        elif message == 'server-shutdown':
                            self.exit_receive.set()
                            self.exit_run.set()
                            break
                        else:
                            print(message)
            except OSError as e:
                print(f"Error receiving message: {e}")
                self.exit_receive.set()
                break  # Exit the loop on error

    def run(self):
        
        if not self.connect_server():
            return

        receiveThread = threading.Thread(target=self.receive)
        receiveThread.start()
        try:
            while self.exit_run.is_set() == False:
                userInput = input("Enter message (type 'exit' to leave): \n")
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
            if self.client_socket.fileno() != -1:
                self.client_socket.close()
            receiveThread.join()
            print("Client has exited.")


class ServerUDP:
    def __init__(self, server_port):
        self.server_port = server_port
        server_addr = socket.gethostbyname(socket.gethostname())

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.bind((server_addr, self.server_port))

        self.clients = {}
        self.messages = []

    def accept_client(self, client_addr, message):
        clientName = message

        # Check if the client's name is in the dict and return False if it is
        if clientName in self.clients.values():
            self.server_socket.sendto("Name already taken".encode(), client_addr)
            return False

        # Otherwise, send a "Welcome" message to the client
        welcomeMessage = "Welcome!"
        self.server_socket.sendto(welcomeMessage.encode(), client_addr)
        print(f"Sent welcome message to {clientName}")


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
       #self.messages.append((None, 'server-shutdown'))
       #self.broadcast()

        # Broadcast the shutdown message to all connected clients
        for client_addr in list(self.clients.keys()):
            self.server_socket.sendto("server-shutdown".encode(), client_addr)
            self.close_client(client_addr)

        # Close the server socket
        self.server_socket.close()
        print("Server shutting down.")

    def get_clients_number(self):
        return len(self.clients)
        
    def run(self):
        print("Server started.")
        print("Waiting to receive connections...")
        try:
            while True:
                # Receive a message and the client's address
                readable, _, _ = select.select([self.server_socket], [], [], 1)

                if readable:
                    data, client_addr = self.server_socket.recvfrom(1024)  # buffer size of 1024 bytes
                    message = data.decode()

                    parts = message.split(':')
                    if len(parts) == 2:
                        clientName, msgContent = parts
                    else:
                        clientName, msgContent = parts[0], ""

                    if 'join' in msgContent:
                        self.accept_client(client_addr, clientName)
                    elif msgContent == "exit":
                        self.close_client(client_addr)
                    else:
                        if client_addr in self.clients:
                            fullMessage = f"{clientName}: {msgContent}"
                            self.messages.append((client_addr, fullMessage))
                            self.broadcast()

                # Broadcast the message to other clients
                #self.broadcast()

        except KeyboardInterrupt:
            print("Server is shutting down due to KeyboardInterrupt.")
            self.shutdown()
        except Exception as e:
            print(f"An error occurred: {e}")
            self.shutdown()

class ClientUDP:
    def __init__(self, client_name, server_port):
        self.client_name = client_name
        self.server_port = server_port

        self.server_addr = socket.gethostbyname(socket.gethostname())
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.exit_run = threading.Event()
        self.exit_receive = threading.Event()

    def connect_server(self):
        # try to send join message and wait for response
        try:
            #self.send('join')
            join_message = f"{self.client_name}:join"
            self.client_socket.sendto(join_message.encode(), (self.server_addr, self.server_port))

            readable, _, _ = select.select([self.client_socket], [], [], 5)
            if readable:

                data, _ = self.client_socket.recvfrom(1024)
                response = data.decode()

                # if the response is Welcome then return True
                if response == 'Welcome!':
                    print("Connected to chat")
                    return True
                elif response == "Name already taken":
                    print("Name already taken")
                    self.client_socket.close() 
                    self.exit_run.set()  
                    self.exit_receive.set()
                    return False
                else:
                    return False

        except Exception as e:
            print(f"Error connecting to the server: {e}")
            return False

    def send(self, text):
        try:
            message = f"{self.client_name}:{text}"

            self.client_socket.sendto(message.encode(), (self.server_addr, self.server_port))
            print("message sent")

        except Exception as e:
            print(f"message couldn't send: {e}")

    def receive(self):
        try:
            while self.exit_receive.is_set() == False:
                readable, _, _ = select.select([self.client_socket], [], [], 1)

                if readable:
                    data, _ = self.client_socket.recvfrom(1024)
                    message = data.decode()

                    if message == 'server-shutdown':
                        print("Server is shutting down.")
                        self.exit_receive.set()
                        self.exit_run.set()
                        break
                    else:
                        print(message)

        except Exception as e:
            print(f"receive failed: {e}")

    def run(self):
        try:
            self.connect_server()

            receiveThread = threading.Thread(target=self.receive)
            receiveThread.start()

            while self.exit_run.is_set() == False:
                userInput = input("Enter message (type 'exit' to leave): \n")

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
