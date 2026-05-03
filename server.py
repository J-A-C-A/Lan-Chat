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

            conn.send("LOGIN|OK".encode("utf-8"))
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

            if message.startswith("/"):
                self.command_handler(nick,conn,message)
            else:
                parts = message.split("|", maxsplit=2)
                if len(parts) < 3:
                    print("ERROR|Invalid message format")
                    continue

                cmd = parts[0]
                target = parts[1]
                msg = parts[2]

                if not cmd or not target or not msg:
                    print("ERROR|Invalid message format")
                    continue

                self.route_message(nick, conn, cmd, target, msg)



    def clean_up(self,conn,nick):
        rooms_to_clean = []
        for room in self.rooms.keys():
            if nick in self.rooms[room]:
                rooms_to_clean.append(room)

        for room in rooms_to_clean:
            self.rooms[room].remove(nick)
            if len(self.rooms[room]) == 0:
                self.rooms.pop(room)

        self.clients.pop(nick,None)
        self.sockets.pop(conn,None)
        conn.close()

    def route_message(self,nick,conn,cmd,target,msg):

        if cmd == "PM":
            self.send_private(nick,conn,cmd,target,msg)
        elif cmd == "ROOM":
            self.send_room(nick,conn,cmd,target,msg)
        else:
            print("ERROR|Invalid message format")
            return

    def message_formatting(self,sender_nick,cmd,target,msg):
        if cmd == "PM":
            message = cmd + "|" + sender_nick + "|" + target + "|" + msg
        elif cmd == "ROOM":
            message = cmd + "|" + target + "|" + sender_nick + "|" + msg
        else:
            return None

        return message


    def send_private(self,sender_nick,sender_conn,cmd,target,msg):

        if target in self.clients.keys():
            target_conn = self.clients[target]
            complex_message = self.message_formatting(sender_nick,cmd,target,msg)
            if complex_message is not None:
                target_conn.send(complex_message.encode("utf-8"))
            else:
                print("ERROR|Invalid message format")
                sender_conn.send("ERROR|Invalid message format".encode("utf-8"))
                return

        else:
            sender_conn.send("ERROR|Target does not exist".encode("utf-8"))
            return


    def send_room(self,sender_nick,sender_conn,cmd,target,msg):
        complex_message = self.message_formatting(sender_nick,cmd,target,msg)

        if complex_message is None:
            print("ERROR|Invalid message format")
            sender_conn.send("ERROR|Invalid message format".encode("utf-8"))
            return

        if target in self.rooms.keys():
            for user in self.rooms[target]:
                if user == sender_nick:
                    continue
                if user not in self.clients.keys():
                    continue


                target_conn = self.clients[user]
                target_conn.send(complex_message.encode("utf-8"))

        else:
            sender_conn.send("ERROR|Target does not exist".encode("utf-8"))
            return

    def join_room(self,nick,conn,name):

        if name in self.rooms.keys():
            if nick in self.rooms[name]:
                pass
            else:
                self.rooms[name].append(nick)
        else:
            self.rooms[name] = [nick]

    def leave_room(self,nick,conn,name):
        if name in self.rooms.keys():

            if nick in self.rooms[name]:
                self.rooms[name].remove(nick)
                if len(self.rooms[name]) == 0:
                    self.rooms.pop(name)
            else:
                    conn.send("ERROR|User is not in the room".encode("utf-8"))
        else:
            conn.send("ERROR|Room does not exist".encode("utf-8"))

    def command_handler(self,nick,conn,msg):
        command = msg.split(" ",maxsplit=1)

        if command[0] == "/join" and len(command) > 1:
            self.join_room(conn,nick,command[1])
        elif command[0] == "/leave" and len(command) > 1:
            self.leave_room(conn,nick,command[1])
        elif command[0] == "/users":
            users = list(self.clients.keys())

            if self.clients:
                answer = "USERS" + "|" + ",".join(users)
            else:
                answer = "USERS" + "|" + "NONE"

            conn.send(answer.encode("utf-8"))
        elif command[0] == "/rooms":

            if self.rooms:
                parts = []

                for room, users in self.rooms.items():
                    users_str = ",".join(users)
                    parts.append(f"{room}:{users_str}")

                answer = "ROOMS" + "|" + ";".join(parts)
            else:
                answer = "ROOMS" + "|" + "NONE"

            conn.send(answer.encode("utf-8"))

        elif command[0] == "/quit":
            self.clean_up(conn,nick)
        else:
            conn.send("ERROR|Invalid command".encode("utf-8"))

