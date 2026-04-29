import socket as soc
import threading as thr
import datetime as dt
import re



class Server():
    def __init__(self):
        self.ip_address = "127.0.0.1"
        self.server_port = 8888
        self.server_socket = soc.socket(soc.AF_INET, soc.SOCK_STREAM)
        self.clients = {}
        self.sockets = {}
        self.rooms = {}


    def start(self):
        self.server_socket.bind((self.ip_address, self.server_port))
        self.server_socket.listen(5)
        self.accept_connections()

    def accept_connections(self):
        while True:
            conn, address = self.server_socket.accept()
            thread = thr.Thread(target=self.handle_client, args=(conn,address))
            thread.start()


    def handle_client(self,conn,address):
        while True:
            raw_data = conn.recv(1024)
            text = raw_data.decode("utf-8")

            if text == "":
                raw_error = "ERROR|Nick is empty"
                encoded_error = raw_error.encode("utf-8")
                conn.send(encoded_error)
                continue
            if text in self.clients.keys():
                raw_error = "ERROR|Nick is already used"
                encoded_error = raw_error.encode("utf-8")
                conn.send(encoded_error)
                continue

            self.clients[text] = conn
            self.sockets[conn] = text
            break




    def route_message(self):
        pass
    def send_private(self):
        pass
    def send_room(self):
        pass