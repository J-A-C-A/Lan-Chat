import socket as soc
import threading as thr
import datetime as dt
import re



class Server():
    def __init__(self):
        self.ip_address = "127.0.0.1"
        self.server_port = 5000
        self.server_socket = soc.socket(soc.AF_INET, soc.SOCK_STREAM)
        self.clients = {}
        self.sockets = {}
        self.rooms = {}
        self.clients_lock = thr.Lock()
        self.sockets_lock = thr.Lock()
        self.rooms_lock = thr.Lock()


    def start(self):
        self.server_socket.setsockopt(soc.SOL_SOCKET, soc.SO_REUSEADDR, 1)
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

        with self.clients_lock:
            self.clients[nick] = conn
        with self.sockets_lock:
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

            with self.clients_lock:
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
            print("DEBUG RAW:", repr(message))

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
        with self.rooms_lock:
            rooms_with_users = list(self.rooms.items())
            for room, users in rooms_with_users:
                if nick in users:
                    rooms_to_clean.append(room)
            for room in rooms_to_clean:
                self.rooms[room].remove(nick)
                if len(self.rooms[room]) == 0:
                    self.rooms.pop(room)

        with self.clients_lock:
            self.clients.pop(nick,None)
        with self.sockets_lock:
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
        print("TARGET:", target)
        with self.clients_lock:
            print("Clients:", self.clients.keys())
            target_conn = self.clients.get(target,None)


        if target_conn is not None:
                print("SENDING TO: ", target_conn)
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

        with self.rooms_lock:
                users_in_room = self.rooms.get(target,None)

        if users_in_room is not None:
                for user in users_in_room:
                    if user == sender_nick:
                        continue
                    with self.clients_lock:
                        target_conn = self.clients.get(user,None)

                    if target_conn is  None:
                        continue
                    target_conn.send(complex_message.encode("utf-8"))
        else:
            sender_conn.send("ERROR|Target does not exist".encode("utf-8"))
            return

    def join_room(self,nick,conn,name):
        with self.rooms_lock:
            if name in self.rooms.keys():
                if nick in self.rooms[name]:
                    conn.send("ERROR|User is already in the room".encode("utf-8"))

                else:
                    self.rooms[name].append(nick)
                    conn.send(f"LOG|You are now in room: {name}".encode("utf-8"))
            else:
                self.rooms[name] = [nick]
                conn.send(f"LOG|You are now in room: {name}".encode("utf-8"))

    def leave_room(self,nick,conn,name):
        status = ""
        with self.rooms_lock:
            if name in self.rooms.keys():
                if nick in self.rooms[name]:

                        self.rooms[name].remove(nick)
                        status = "Left_room"
                        if len(self.rooms[name]) == 0:
                            self.rooms.pop(name)
                else:
                        status = "Not_in_room"

            else:
                status = "Room_not_found"

        if status == "Left_room":
            conn.send(f"LOG|You left room: {name}".encode("utf-8"))
        elif status ==  "Not_in_room":
            conn.send("ERROR|User is not in the room".encode("utf-8"))
        elif status == "Room_not_found":
            conn.send("ERROR|Room does not exists".encode("utf-8"))


    def command_handler(self,nick,conn,msg):
        command = msg.split(" ",maxsplit=1)

        if command[0] == "/join" and len(command) > 1:
            self.join_room(nick=nick,conn=conn,name=command[1])
        elif command[0] == "/leave" and len(command) > 1:
            self.leave_room(nick=nick,conn=conn,name=command[1])
        elif command[0] == "/users":
            with self.clients_lock:
                users = list(self.clients.keys())

            if self.clients:
                answer = "USERS" + "|" + ",".join(users)
            else:
                answer = "USERS" + "|" + "NONE"

            conn.send(answer.encode("utf-8"))
        elif command[0] == "/rooms":
            with self.rooms_lock:
                rooms_with_users = list(self.rooms.items())

            if rooms_with_users:
                parts = []
                for room, users in rooms_with_users:
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

if __name__ == "__main__":
    server = Server()
    server.start()
