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
        nick = self.login_loop(conn)

        if nick is None:
            return

        self.clients[nick] = conn
        self.sockets[conn] = nick
        self.chat_loop(conn,nick)

    def login_loop(self,conn):
        while True:
            raw_data = conn.recv(1024)

            if not raw_data:
                print("Client disconnected")
                return None

            nick = raw_data.decode("utf-8")

            if not nick:
                conn.send("ERROR|Nick is empty".encode("utf-8"))
                continue

            if nick in self.clients.keys():
                conn.send("ERROR|Nick is already used".encode("utf-8"))
                continue

            return nick

    def chat_loop(self,conn,nick):
        while True:
            try:
                raw_data = conn.recv(1024)
            except ConnectionResetError:
                self.clean_up(conn,nick)
                return


            if not raw_data:
                print("Client disconnected")
                self.clean_up(conn,nick)
                return

            message = raw_data.decode("utf-8")
            parts = message.split("|", maxsplit=2)

            if len(parts) < 3:
                print("Invalid message format")
                continue

            cmd = parts[0]
            target = parts[1]
            msg = parts[2]

            if not cmd or not target or not msg:
                print("Invalid message format")
                continue

            self.route_message(nick,conn,parts)


    def clean_up(self,conn,nick):
        self.clients.pop(nick,None)
        self.sockets.pop(conn,None)
        conn.close()

    def route_message(self,nick,conn,parts):
        pass
    def send_private(self):
        pass
    def send_room(self):
        pass