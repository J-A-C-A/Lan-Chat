import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from tkinter import messagebox

class ChatGUI():
    def __init__(self,root,client,queue):
        self.root = root
        self.root.title("Lan Chat App")
        self.client = client
        self.q = queue
        self.nick = ""

        self.current_chat = {"type":"PM","name":"self"}
        self.chats = {}
        self.rooms_data = {}
        self.root.withdraw()
        self.show_login_popup()
        self.build_layout()
        self.build_left_panel()
        self.build_center_panel()
        self.build_right_panel()

        self.start_queue_loop()


    def build_layout(self):
        self.left_frame = tk.Frame(self.root, width=200)
        self.center_frame = tk.Frame(self.root, width=500)
        self.right_frame = tk.Frame(self.root, width=200)

        self.status_bar = tk.Label(self.root,text="",anchor="w",relief="sunken")
        self.status_bar.pack(side="bottom",fill="x")

        self.left_frame.pack(side="left", fill="y")
        self.center_frame.pack(side="left", fill="both",expand=True)
        self.right_frame.pack(side="right", fill="y")

    def build_left_panel(self):
        self.left_pm_frame = tk.Frame(self.left_frame)
        self.left_room_frame = tk.Frame(self.left_frame)

        self.left_pm_frame.pack(fill="both", expand=True)
        self.left_room_frame.pack(fill="both", expand=True)

        self.pm_label = tk.Label(self.left_pm_frame,text="Private messages")
        self.pm_label.pack()

        self.room_label = tk.Label(self.left_room_frame,text="Your Rooms")
        self.room_label.pack()

        self.leave_room_button = tk.Button(self.left_room_frame,text="Leave Room", command= self.handle_leave_room)

        self.pm_list = tk.Listbox(self.left_pm_frame)
        self.room_list = tk.Listbox(self.left_room_frame)

        self.pm_list.pack(fill="both", expand=True)
        self.room_list.pack(fill="both", expand=True)
        self.leave_room_button.pack()

        self.pm_list.bind("<<ListboxSelect>>", self.on_pm_select)
        self.room_list.bind("<<ListboxSelect>>", self.on_room_select)

    def build_center_panel(self):
        self.chat_box_upper_label = tk.Label(self.center_frame)
        self.chat_box_upper_label.pack()

        self.chat_box_label = tk.Label(self.center_frame,text="No chat selected")
        self.chat_box_label.pack()


        self.chat_box = ScrolledText(self.center_frame)
        self.chat_box.pack(fill="both", expand=True)
        self.chat_box.config(state="disabled")

        self.input_frame = tk.Frame(self.center_frame)
        self.input_frame.pack(fill="x")

        self.input_entry = tk.Entry(self.input_frame)
        self.input_entry.pack(side="left",fill="x",expand=True)
        self.input_entry.bind("<Return>", lambda event: self.send_message())

        self.send_button = tk.Button(self.input_frame,
                                     text="Send",
                                     command=self.send_message)
        self.send_button.pack(side="right")
        
    def build_right_panel(self):
        self.right_users_frame = tk.Frame(self.right_frame)
        self.right_rooms_frame = tk.Frame(self.right_frame)

        self.users_label = tk.Label(self.right_users_frame,text="Active Users")
        self.users_label.pack()

        self.rooms_label = tk.Label(self.right_rooms_frame,text="Available Rooms")
        self.rooms_label.pack()

        self.create_button = tk.Button(self.right_rooms_frame,text="Create Room",command= self.show_create_room_popup)

        self.right_users_frame.pack(fill="both", expand=True)
        self.right_rooms_frame.pack(fill="both", expand=True)

        self.users_list = tk.Listbox(self.right_users_frame)
        self.rooms_list_right = tk.Listbox(self.right_rooms_frame)

        self.users_list.pack(fill="both", expand=True)
        self.rooms_list_right.pack(fill="both", expand=True)
        self.create_button.pack()

        self.users_list.bind("<<ListboxSelect>>", self.on_user_select)
        self.rooms_list_right.bind("<<ListboxSelect>>", self.on_room_right_select)

    def show_login_popup(self):
        self.login_popup = tk.Toplevel(self.root)
        self.login_popup.title("Login")
        self.login_label = tk.Label(self.login_popup,text="Enter your username")
        self.login_entry = tk.Entry(self.login_popup)
        self.login_button = tk.Button(self.login_popup,text="Log in", command=self.handle_login)
        self.login_label.pack()
        self.login_entry.pack()
        self.login_button.pack()
        self.login_entry.bind("<Return>", self.handle_login)

    def show_create_room_popup(self):
        self.room_popup = tk.Toplevel(self.root)
        self.room_popup.title("Create Room")
        self.room_popup_label = tk.Label(self.room_popup,text="Enter room name")
        self.room_entry = tk.Entry(self.room_popup)
        self.room_button = tk.Button(self.room_popup,text="Create", command=self.handle_creat_room)

        self.room_popup_label.pack()
        self.room_entry.pack()
        self.room_button.pack()
        self.room_entry.bind("<Return>", self.handle_creat_room)

    def handle_creat_room(self,event=None):
        name = self.room_entry.get()
        if not name:
            return
        self.client.send_message(f"/join|{name}")
        self.rooms_list_right.insert("end",name)
        self.room_list.insert("end",name)
        self.switch_chat("ROOM",name)
        self.room_popup.destroy()

    def handle_leave_room(self,event=None):
        if not self.room_list.curselection():
            return

        index = self.room_list.curselection()[0]
        room = self.room_list.get(index)
        self.client.send_message(f"/leave|{room}")
        self.room_list.delete(index)
        self.current_chat = {"type": "PM", "name": "self"}
        self.chat_box_label.config(text="No chat selected")
        self.chat_box.config(state="normal")
        self.chat_box.delete("1.0", "end")
        self.chat_box.config(state="disabled")

    def handle_login(self,event=None):
        nick = self.login_entry.get()

        if not self.client.connected:
            tk.messagebox.showerror("Connection Error","Connection with server Failed")
            return

        result = self.client.login_gui(nick)
        if result == "LOGIN|OK":
            self.nick = nick
            self.login_popup.destroy()
            self.root.deiconify()
            self.chat_box_upper_label.config(text=f"User: {self.nick}")
        elif result == "ERROR|Nick is empty":
            tk.messagebox.showerror("Error","Nick is empty")
        elif result == "ERROR|Nick is already used":
            tk.messagebox.showerror("Error","Nick is already used")
        else:
            tk.messagebox.showerror("Error","Unexpected answer from server")




    def send_message(self):
        msg = self.input_entry.get()
        if self.current_chat.get("type",None) == "PM":
            message_to_send = "PM" + "|" + self.current_chat.get("name","Unknown") + "|" + msg
            self.client.send_message(message_to_send)
            gui_msg = self.nick + ":" + " " + msg
            key = f"{self.current_chat['type']}|{self.current_chat['name']}"
            self.append_message(key,gui_msg)
            self.input_entry.delete(0, "end")
        elif self.current_chat.get("type",None) == "ROOM":
            message_to_send = "ROOM" + "|"+ self.current_chat.get("name","Unknown") + "|" +  msg
            self.client.send_message(message_to_send)
            gui_msg = self.nick + ":" + " " + msg
            key = f"{self.current_chat['type']}|{self.current_chat['name']}"
            self.append_message(key, gui_msg)
            self.input_entry.delete(0, "end")

    def append_message(self,key,msg):
        self.ensure_chat_exists(key)
        self.chats[key].append(msg)
        current_key = self.create_key(self.current_chat["type"],self.current_chat["name"])
        if key == current_key:
            self.refresh_chat()
        else:
            parts = key.split("|",maxsplit=1)
            name = parts[1]
            existing_users = self.pm_list.get(0, "end")
            if name not in existing_users:
                self.pm_list.insert("end", name)



    def on_pm_select(self,event=None):
        selection = self.pm_list.curselection()
        if not selection:
            return

        index = selection[0]
        name = self.pm_list.get(index)
        self.switch_chat(chat_type="PM",name=name)

    def on_room_select(self,event):
        selection = self.room_list.curselection()
        if not selection:
            return
        index = selection[0]
        name = self.room_list.get(index)
        self.switch_chat(chat_type="ROOM",name=name)

    def on_user_select(self,event=None):
        selection = self.users_list.curselection()
        if not selection:
            return
        index = selection[0]
        name = self.users_list.get(index)
        existing_users = self.pm_list.get(0,"end")
        if  name not in existing_users:
            self.pm_list.insert("end",name)

        self.switch_chat(chat_type="PM",name=name)

    def on_room_right_select(self,event=None):
        selection = self.rooms_list_right.curselection()
        if not selection:
            return
        index = selection[0]
        name = self.rooms_list_right.get(index)
        existing_rooms = self.room_list.get(0,"end")
        if name not in existing_rooms:
            self.room_list.insert("end",name)

        self.client.send_message(f"/join|{name}")
        self.switch_chat(chat_type="ROOM",name=name)



    def switch_chat(self,chat_type,name):
        key = self.create_key(chat_type,name)
        self.ensure_chat_exists(key)
        self.current_chat = {"type":chat_type,"name":name}
        self.refresh_chat()

    def refresh_chat(self):
        chat_type = self.current_chat["type"]
        name = self.current_chat["name"]
        if chat_type == "ROOM":
            users = self.rooms_data.get(name,[])
            users_str = ",".join(users)
            self.chat_box_label.config(text=f"ROOM|{name}: {users_str}")
        else:
            self.chat_box_label.config(text=f"{chat_type}|{name}")
        self.chat_box.config(state="normal")
        self.chat_box.delete("1.0","end")
        key = self.create_key(self.current_chat['type'],self.current_chat["name"])
        for msg in self.chats.get(key,[]):
            self.chat_box.insert("end", msg + "\n")

        self.chat_box.config(state="disabled")

    def ensure_chat_exists(self,key):
        if key not in self.chats:
            self.chats[key] = []

    def create_key(self,chat_type,name):
        key= f"{chat_type}|{name}"
        return key

    def process_queue(self):
        while not self.q.empty():
            #"PM", sender_nick, content, timestamp
            #"ROOM", room_name, sender_nick, content, timestamp
            message = self.q.get()
            chat_type = message[0]
            if chat_type=="PM":
                name = message[1]
                content = message[2]
                timestamp = message[3]
                key = self.create_key(chat_type,name)
                formatted_message = f"{timestamp}|{name}: {content}"
                self.append_message(key,formatted_message)
            elif chat_type=="ROOM":
                room_name = message[1]
                sender_nick = message[2]
                content = message[3]
                timestamp = message[4]
                key = self.create_key(chat_type,room_name)
                formatted_message = f"{timestamp}|{room_name}|{sender_nick}: {content}"
                self.append_message(key,formatted_message)
            elif chat_type=="USERS_UPDATE":
                users= message[1]
                self.users_list.delete(0, "end")
                for u in users:
                    self.users_list.insert("end", u)
            elif chat_type=="ROOMS_UPDATE":
                rooms = message[1]
                self.rooms_list_right.delete(0, "end")
                self.rooms_data = {}
                for r in rooms:
                    parts = r.split(":")
                    room_name = parts[0]
                    if len(parts)> 1:
                        users = parts[1].split(",")
                    else:
                        users = []

                    self.rooms_data[room_name] = users
                    self.rooms_list_right.insert("end", room_name)
                    if self.current_chat["type"]=="ROOM":
                        self.refresh_chat()
            elif chat_type == "LOG":
                self.set_status(f"Info: {message[1]}")
            elif chat_type == "ERROR":
                self.set_status(f"Error: {message[1]}")



    def start_queue_loop(self):
        self.process_queue()
        self.root.after(100, self.start_queue_loop)

    def set_status(self,message):
        self.status_bar.config(text=message)
        self.root.after(3000, lambda: self.status_bar.config(text=""))





