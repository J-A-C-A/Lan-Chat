import socket as soc
import threading as thr

class Client():
    def __init__(self):
        self.server_ip = "127.0.0.1"
        self.server_port = 8888
        self.client_socket = soc.socket(soc.AF_INET, soc.SOCK_STREAM)
        self.nick = ""
        self.connected = False
        self.running = True
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
                elif server_answer == "ERROR|Nick is empty":
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




    def send_loop(self):
        pass

    def receive_loop(self):
        pass
