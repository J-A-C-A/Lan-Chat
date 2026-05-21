import socket as soc
import threading as thr
import sys
class Client():
    def __init__(self,queue):
        self.server_ip = "127.0.0.1"
        self.server_port = 5000
        self.client_socket = soc.socket(soc.AF_INET, soc.SOCK_STREAM)
        self.nick = ""
        self.connected = False
        self.running = False
        self.logged_in = False
        self.print_lock = thr.Lock()
        self.buffer = b""
        self.q = queue


    def connect_gui(self):
        try:
            self.client_socket.connect((self.server_ip, self.server_port))
            self.connected = True

        except (ConnectionRefusedError,OSError):
            print("ERROR|Connection refused")
            self.connected = False


    def login_gui(self,nick):
        self.nick = nick
        self.send_message(nick)
        server_answer = self.receive_message()
        if server_answer == "LOGIN|OK":
            self.logged_in = True
            self.running = True
            thread = thr.Thread(target=self.receive_loop_gui)
            thread.daemon = True
            thread.start()
            return "LOGIN|OK"
        elif server_answer == "ERROR|Nick is empty":
            return "ERROR|Nick is empty"
        elif server_answer == "ERROR|Nick is already used":
            return "ERROR|Nick is already used"
        else:
            return "ERROR|Unexpected answer from server"

    def receive_loop_gui(self):
        while self.running:
            try:
                message = self.receive_message()
                if not message:
                    self.running = False
                    break
                else:
                    if message.startswith("PM|"):
                        #PM|nadawca|odbiorca|treść|timestamp
                        parts = message.split("|", maxsplit=4)
                        if len(parts) >= 5:
                            sender_nick = parts[1]
                            content = parts[3]
                            timestamp = parts[4]
                            message_to_return = ("PM", sender_nick, content, timestamp)
                            self.q.put(message_to_return)

                    elif message.startswith("ROOM|"):
                        #ROOM|pokój|nadawca|treść|timestamp
                        parts = message.split("|", maxsplit=4)
                        if len(parts) >= 5:
                            room_name = parts[1]
                            sender_nick = parts[2]
                            content = parts[3]
                            timestamp = parts[4]
                            message_to_return = ("ROOM", room_name, sender_nick, content, timestamp)
                            self.q.put(message_to_return)

                    elif message.startswith("USERS|"):
                        parts = message.split("|", maxsplit=1)
                        if len(parts) > 1 and parts[1]:
                            users = parts[1].split(",")
                        else:
                            users = []
                        message_to_return = ("USERS_UPDATE", users)
                        self.q.put(message_to_return)

                    elif message.startswith("ROOMS|"):
                        parts = message.split("|", maxsplit=1)
                        if len(parts) > 1 and parts[1]:
                            rooms= parts[1].split(";")
                        else:
                            rooms = []
                        message_to_return = ("ROOMS_UPDATE", rooms)
                        self.q.put(message_to_return)

            except OSError:
                return




#=====================CLI VERSION=====================
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
                self.send_message(self.nick)
                server_answer = self.receive_message()
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
                    print(server_answer)
                    continue

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
            self.running = True
            thread.start()
            self.send_loop()
        else:
            print("ERROR|User is not logged in")

    def send_loop(self):
        while self.running:
            try:
                with self.print_lock:
                    print("Enter your message: ", end="",flush=True)

                message = input()
                if message == "/quit":
                    self.running = False
                    self.send_message("/quit")
                    self.client_socket.close()
                    break
                elif message == "/help":
                    self.show_help()
                elif not message.strip():
                    continue
                else:
                    self.send_message(message)
            except soc.error:
                print("ERROR|Connection lost")
                self.running = False
                self.client_socket.close()
                break


    def receive_loop(self):
        print("RECEIVE LOOP STARTED")
        while self.running:
            try:
                message = self.receive_message()
                if not message:
                    self.client_socket.close()
                    self.running = False
                    break
                else:
                    if message.startswith("PM|"):
                        parts = message.split("|", maxsplit=4)
                        if len(parts) >= 5:
                            sender_nick = parts[1]
                            content = parts[3]
                            timestamp = parts[4]
                            formatted_message = f"[{sender_nick} -> you, {timestamp}]: {content}"
                            with self.print_lock:
                                sys.stdout.write("\r" + " " * 120 + "\r")
                                print(formatted_message)
                    elif message.startswith("ROOM|"):
                        parts = message.split("|", maxsplit=4)
                        if len(parts) >= 5:
                            room_name = parts[1]
                            sender_nick = parts[2]
                            content = parts[3]
                            timestamp = parts[4]
                            formatted_message = f"[#{room_name}|{sender_nick}|{timestamp}]: {content}"
                            with self.print_lock:
                                sys.stdout.write("\r" + " " * 120 + "\r")
                                print(formatted_message)
                    else:
                        with self.print_lock:
                            sys.stdout.write("\r" + " " * 120 + "\r")
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

    def receive_message(self):
        while True:
            chunk = self.client_socket.recv(1024)
            self.buffer += chunk

            if not self.buffer:
                return None

            parts = self.buffer.split(b"\n")

            if len(parts) >= 2:
                message = parts[0]
                self.buffer = b"\n".join(parts[1:])
                return message.decode("utf-8")

    def send_message(self,message):
        message += "\n"
        msg_to_send = message.encode("utf-8")
        self.client_socket.send(msg_to_send)

#if __name__ == "__main__":
    #client = Client()
    #client.connect()
    #client.start()
