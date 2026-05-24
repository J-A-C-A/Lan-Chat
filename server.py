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
        self.rooms = {}
        self.buffers = {}
        self.message_counters = {}
        self.send_locks = {}
        self.message_times_of_reset = {}
        self.RATE_LIMIT = 5
        self.RATE_LIMIT_BAN = 10
        self.MAX_BUFFER_SIZE = 4096
        self.clients_lock = thr.Lock()
        self.rooms_lock = thr.Lock()
        self.buffers_lock = thr.Lock()
        self.rate_limit_lock = thr.Lock()
        self.send_lock = thr.Lock()


    def start(self):
        self.server_socket.setsockopt(soc.SOL_SOCKET, soc.SO_REUSEADDR, 1)
        self.server_socket.bind((self.ip_address, self.server_port))
        self.server_socket.listen(5)
        self.accept_connections()

    def accept_connections(self):
        while True:
            conn, address = self.server_socket.accept()
            self.send_locks[conn] = thr.Lock()
            thread = thr.Thread(target=self.handle_client, args=(conn,address))
            thread.start()


    def handle_client(self,conn,address):
        nick = self.login_loop(conn)

        if nick is None:
            return

        self.chat_loop(conn,nick)

    def login_loop(self,conn):
        while True:
            err_nick_used = False
            nick = self.receive_message(conn)

            if nick is None:
                print("Client disconnected")
                return None
            elif nick == "":
                self.send_message(conn,"ERROR|Nick is empty")
                continue

            pattern = r'^[a-zA-Z0-9_\-\.ąęłćńóśźżĄĘŁĆŃÓŚŹŻ]+( [a-zA-Z0-9_\-\.ąęłćńóśźżĄĘŁĆŃÓŚŹŻ]+)*$'
            result = re.match(pattern, nick)
            if  result is None:
                self.send_message(conn,"ERROR|You have entered an invalid characters")
                continue



            with self.clients_lock:
                if nick in self.clients.keys():
                    err_nick_used = True
                else:
                    self.clients[nick] = conn

            if err_nick_used:
                self.send_message(conn,"ERROR|Nick is already used")
                continue
            else:
                self.send_message(conn,"LOGIN|OK")
                with self.clients_lock:
                    users = list(self.clients.keys())

                if self.clients:
                    answer_users = "USERS" + "|" + ",".join(users)
                else:
                    answer_users = "USERS" + "|" + ""
                with self.clients_lock:
                    for c in self.clients.values():
                        self.send_message(c,answer_users)



                with self.rooms_lock:
                    rooms_with_users = list(self.rooms.items())

                if rooms_with_users:
                    parts = []
                    for room, users in rooms_with_users:
                        users_str = ",".join(users)
                        parts.append(f"{room}:{users_str}")

                    answer_rooms = "ROOMS" + "|" + ";".join(parts)
                else:
                    answer_rooms = "ROOMS" + "|" + ""
                with self.clients_lock:
                    for c in self.clients.values():
                        self.send_message(c, answer_rooms)

                return nick

    def chat_loop(self,conn,nick):
        while True:
            try:
                message = self.receive_message(conn)
            except ConnectionResetError:
                self.clean_up(conn,nick)
                return
            except OverflowError:
                self.send_message(conn,"ERROR|Buffer overflow, disconnecting")
                self.clean_up(conn,nick)
                return
            if message is None:
                print("Client disconnected")
                self.clean_up(conn,nick)
                return
            elif message == "":
                self.send_message(conn, "ERROR|Message is empty")
                continue
            else:
                result = self.check_rate_limit(nick)
                if result == "BAN":
                    self.send_message(conn,"LOG|You have been banned for sending too many messages")
                    self.clean_up(conn,nick)
                    return
                elif result == "WARN":
                    self.send_message(conn,"LOG|You have been warned for sending too many messages")


            print("DEBUG RAW:", repr(message))

            if message.startswith("/"):
                result = self.command_handler(nick,conn,message)
                if result == "QUIT":
                    return
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
            rooms_with_users = list(self.rooms.items())

        if rooms_with_users:
            parts = []
            for room, users in rooms_with_users:
                users_str = ",".join(users)
                parts.append(f"{room}:{users_str}")
            answer_rooms = "ROOMS" + "|" + ";".join(parts)
        else:
            answer_rooms = "ROOMS" + "|" + ""

        with self.clients_lock:
            self.clients.pop(nick,None)
            self.buffers.pop(conn, None)
            self.send_locks.pop(conn,None)
            users = list(self.clients.keys())

        if self.clients:
            answer_users = "USERS" + "|" + ",".join(users)
        else:
            answer_users = "USERS" + "|" + ""

        with self.clients_lock:
            for c in self.clients.values():
                self.send_message(c, answer_users)
            for c in self.clients.values():
                self.send_message(c, answer_rooms)

        with self.rate_limit_lock:
            self.message_times_of_reset.pop(nick,None)
            self.message_counters.pop(nick,None)

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
        now = dt.datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M")

        if cmd == "PM":
            message = cmd + "|" + sender_nick + "|" + target + "|" + msg + "|" + timestamp
        elif cmd == "ROOM":
            message = cmd + "|" + target + "|" + sender_nick + "|" + msg + "|" + timestamp
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
                    try:
                        self.send_message(target_conn,complex_message)
                    except (BrokenPipeError,ConnectionResetError):
                        self.send_message(sender_conn,"ERROR|Target is unavailable")

                else:
                    print("ERROR|Invalid message format")
                    self.send_message(sender_conn,"ERROR|Invalid message format")
                    return
        else:
            self.send_message(sender_conn,"ERROR|Target does not exist")
            return


    def send_room(self,sender_nick,sender_conn,cmd,target,msg):
        complex_message = self.message_formatting(sender_nick,cmd,target,msg)

        if complex_message is None:
            print("ERROR|Invalid message format")
            self.send_message(sender_conn,"ERROR|Invalid message format")
            return

        with self.rooms_lock:
                result = self.rooms.get(target,None)
                if result is not None:
                    users_in_room = list(result)
                else:
                    users_in_room = None


        if users_in_room is not None:
                for user in users_in_room:
                    if user == sender_nick:
                        continue
                    with self.clients_lock:
                        target_conn = self.clients.get(user,None)

                    if target_conn is  None:
                        continue

                    try:
                        self.send_message(target_conn,complex_message)
                    except (BrokenPipeError,ConnectionResetError):
                        print(f"ERROR|User: {user} is unavailable")
                        continue
        else:
            self.send_message(sender_conn,"ERROR|Target does not exist")
            return

    def join_room(self,nick,conn,name):
        err_user_already_in_room = False
        with self.rooms_lock:
            room = self.rooms.get(name,None)
            if room is None:
                self.rooms[name] = [nick]
            elif nick in room:
                err_user_already_in_room = True
            else:
                self.rooms[name].append(nick)

        with self.rooms_lock:
            rooms_with_users = list(self.rooms.items())

        if rooms_with_users:
            parts = []
            for room, users in rooms_with_users:
                users_str = ",".join(users)
                parts.append(f"{room}:{users_str}")

            answer_rooms = "ROOMS" + "|" + ";".join(parts)
        else:
            answer_rooms = "ROOMS" + "|" + ""
        with self.clients_lock:
            for c in self.clients.values():
                self.send_message(c, answer_rooms)


        if err_user_already_in_room:
            err_user_already_in_room = False
            self.send_message(conn, "ERROR|User is already in the room")
        else:
            self.send_message(conn, f"LOG|You are now in room: {name}")

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

        with self.rooms_lock:
            rooms_with_users = list(self.rooms.items())

        if rooms_with_users:
            parts = []
            for room, users in rooms_with_users:
                users_str = ",".join(users)
                parts.append(f"{room}:{users_str}")

            answer_rooms = "ROOMS" + "|" + ";".join(parts)
        else:
            answer_rooms = "ROOMS" + "|" + ""
        with self.clients_lock:
            for c in self.clients.values():
                self.send_message(c, answer_rooms)

        if status == "Left_room":
            self.send_message(conn,f"LOG|You left room: {name}")
        elif status ==  "Not_in_room":
            self.send_message(conn,"ERROR|User is not in the room")
        elif status == "Room_not_found":
            self.send_message(conn,"ERROR|Room does not exist")



    def command_handler(self,nick,conn,msg):
        command = msg.split("|",maxsplit=1)
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
            self.send_message(conn,answer)
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
            self.send_message(conn,answer)

        elif command[0] == "/quit":
            self.clean_up(conn,nick)
            return "QUIT"
        else:
            self.send_message(conn,"ERROR|Invalid command")


    def send_message(self,conn,message):
        message += "\n"
        msg_to_send = message.encode("utf-8")
        with self.send_locks[conn]:
            conn.send(msg_to_send)

    def receive_message(self,conn):
        while True:
            chunk = conn.recv(1024)
            if not chunk:
                return None

            message_to_return = None
            with self.buffers_lock:
                if conn not in self.buffers:
                    self.buffers[conn] = b""

                self.buffers[conn] += chunk

                self.check_buffer_overflow(conn)
                parts = self.buffers[conn].split(b"\n")
                if len(parts) >= 2:
                    message = parts[0]
                    self.buffers[conn] = b"\n".join(parts[1:])
                    message_to_return = message.decode("utf-8")

            if message_to_return is not None:
                return message_to_return


    def check_rate_limit(self,nick):
        now = dt.datetime.now()
        with self.rate_limit_lock:
            if nick not in self.message_counters:
                self.message_counters[nick] = 0
                self.message_times_of_reset[nick] = now

            elapsed = (now - self.message_times_of_reset.get(nick,now) ).total_seconds()

            if elapsed >= 1.0:
                self.message_counters[nick] = 0
                self.message_times_of_reset[nick] = dt.datetime.now()

            self.message_counters[nick] += 1
            count = self.message_counters[nick]

        if count >= self.RATE_LIMIT_BAN:
            return "BAN"
        elif count  >= self.RATE_LIMIT:
            return "WARN"
        else:
            return "OK"

    def check_buffer_overflow(self,conn):
            if len(self.buffers[conn]) > self.MAX_BUFFER_SIZE:
                raise OverflowError("Buffer overflow")


if __name__ == "__main__":
    server = Server()
    server.start()
