import tkinter as tk
from tkinter.scrolledtext import ScrolledText

class ChatGUI():
    def __init__(self,root,client):
        self.root = root
        self.root.title("Chat")
        self.client = client

        self.current_chat = {"type":"PM","name":"self"}
        self.chats = {}
        self.root.withdraw()
        self.show_login_popup()
        self.build_layout()
        self.build_left_panel()
        self.build_center_panel()
        self.build_right_panel()

    def build_layout(self):
        self.left_frame = tk.Frame(self.root, width=200)
        self.center_frame = tk.Frame(self.root, width=500)
        self.right_frame = tk.Frame(self.root, width=200)

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

        self.pm_list = tk.Listbox(self.left_pm_frame)
        self.room_list = tk.Listbox(self.left_room_frame)

        self.pm_list.pack(fill="both", expand=True)
        self.room_list.pack(fill="both", expand=True)

        self.pm_list.bind("<<ListboxSelect>>", self.on_pm_select)
        self.room_list.bind("<<ListboxSelect>>", self.on_room_select)

    def build_center_panel(self):
        self.chat_box = ScrolledText(self.center_frame)
        self.chat_box.pack(fill="both", expand=True)
        self.chat_box.config(state="disabled")

        self.input_frame = tk.Frame(self.center_frame)
        self.input_frame.pack(fill="x")

        self.input_entry = tk.Entry(self.input_frame)
        self.input_entry.pack(side="left",fill="x",expand=True)

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

        self.right_users_frame.pack(fill="both", expand=True)
        self.right_rooms_frame.pack(fill="both", expand=True)

        self.users_list = tk.Listbox(self.right_users_frame)
        self.rooms_list_right = tk.Listbox(self.right_rooms_frame)

        self.users_list.pack(fill="both", expand=True)
        self.rooms_list_right.pack(fill="both", expand=True)

    def show_login_popup(self):
        self.login_popup = tk.Toplevel(self.root)
        self.login_popup.title("Login")
        self.login_label = tk.Label(self.login_popup,text="Enter your username")
        self.login_entry = tk.Entry(self.login_popup)
        self.login_button = tk.Button(self.login_popup,text="Log in", command=self.handle_login)
        self.login_label.pack()
        self.login_entry.pack()
        self.login_button.pack()

    def handle_login(self):
        self.nick = self.login_entry.get()
        self.login_popup.destroy()
        self.root.deiconify()


    def send_message(self):
        msg = self.input_entry.get()
        if self.current_chat.get("type",None) == "PM":
            message_to_send = "PM" + "|" + self.current_chat.get("name","Unknown") + "|" + msg
            #self.client.send_message(message_to_send)
            gui_msg = self.nick + ":" + " " + msg
            self.append_message(gui_msg)
            self.input_entry.delete(0, "end")
        elif self.current_chat.get("type",None) == "ROOM":
            message_to_send = "ROOM" + "|"+ self.current_chat.get("name","Unknown") + "|" +  msg
            #self.client.send_message(message_to_send)
            gui_msg = self.nick + ":" + " " + msg
            self.append_message(gui_msg)
            self.input_entry.delete(0, "end")

    def append_message(self,msg):
        chat_type = self.current_chat["type"]
        name = self.current_chat["name"]
        self.ensure_chat_exists(chat_type,name)
        key = f"{chat_type}|{name}"
        self.chats[key].append(msg)
        self.refresh_chat()

    def on_pm_select(self,event):
        selection = self.pm_list.curselection()
        if not selection:
            return

        index = selection[0]
        name = self.pm_list.get(index)
        self.current_chat = {"type":"PM","name":name}
        self.refresh_chat()

    def on_room_select(self,event):
        selection = self.room_list.curselection()
        if not selection:
            return
        index = selection[0]
        name = self.room_list.get(index)
        self.current_chat = {"type":"ROOM","name":name}
        self.refresh_chat()

    def switch_chat(self,chat_type,name):
        self.ensure_chat_exists(chat_type,name)
        self.current_chat = {"type":chat_type,"name":name}
        self.refresh_chat()


    def refresh_chat(self):
        self.chat_box.config(state="normal")
        self.chat_box.delete("1.0","end")

        key= f"{self.current_chat['type']}|{self.current_chat['name']}"
        for msg in self.chats.get(key,[]):
            self.chat_box.insert("end", msg + "\n")

        self.chat_box.config(state="disabled")

    def ensure_chat_exists(self,chat_type,name):
        key= f"{chat_type}|{name}"
        if key not in self.chats:
            self.chats[key] = []



