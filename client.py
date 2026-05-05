import socket as soc
import threading as thr

class Client():
    def __init__(self):
        self.server_ip = "127.0.0.1"
        self.server_port = 8888
        self.client_socket = soc.socket(soc.AF_INET, soc.SOCK_STREAM)
        self.nick = ""
        self.connected = False
        self.running = False
        self.logged_in = False

    def connect(self):
        try:
            self.client_socket.connect((self.server_ip, self.server_port))
            self.connected = True
            self.login()

        except ConnectionRefusedError:
            print("ERROR|Connection refused")
            self.connected = False
            return

    def login(self):
        while not self.logged_in:
            try:
                self.nick = input("Enter your nickname: ")
                self.client_socket.send(self.nick.encode("utf-8"))
                server_answer = self.client_socket.recv(1024).decode("utf-8")
                if server_answer == "LOGIN|OK":
                    self.logged_in = True
                elif server_answer == "EROR|Nick is empty":
                    print("ERROR|Nick is empty")
                    continue
                elif server_answer == "ERROR|Nick is already used":
                    print("ERROR|Nick is already used")
                    continue
                else:
                    print("ERROR|Unexpected answer from server")

            except soc.error:
                self.client_socket.close()
                self.connected = False
                self.logged_in = False
                print("ERROR")
                break

    def start(self):
        if self.logged_in:
            self.show_help()
            thread = thr.Thread(target=self.receive_loop)
            thread.daemon = True
            thread.start()
            self.running = True
            self.send_loop()
        else:
            print("ERROR|User is not logged in")

    def send_loop(self):
        while self.running:
            try:
                message = input("Enter your message: ")
                if message == "/quit":
                    self.running = False
                    self.client_socket.send("/quit".encode("utf-8"))
                    self.client_socket.close()
                    break
                elif message == "/help":
                    self.show_help()
                elif not message.strip():
                    continue
                else:
                    self.client_socket.send(message.encode("utf-8"))
            except soc.error:
                print("ERROR|Connection lost")
                self.running = False
                self.client_socket.close()
                break


    def receive_loop(self):
        while self.running:
            try:
                raw_data = self.client_socket.recv(1024)
                if not raw_data:
                    self.client_socket.close()
                    self.running = False
                    break
                else:
                    message = raw_data.decode("utf-8")
                    print(message)
            except soc.error:
                print("ERROR|Connection lost")
                self.client_socket.close()
                self.running = False
                break

    def show_help(self):
        print("====INSTRUCTIONS====")
        print("Messages:\n")
        print("Personal message format:")
        print("PM|receiver_nick|text\n")
        print("Group message format:")
        print("ROOM|room_name|text\n")
        print("Server commands:")
        print("/users")
        print("/rooms")
        print("/join room_name")
        print("/leave room_name")
        print("/help")
        print("/quit")
