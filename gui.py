import tkinter as tk
from tkinter.scrolledtext import ScrolledText

class ChatGUI():
    def __init__(self,root):
        self.root = root
        self.root.title("Chat")

        self.current_chat = None
        self.chats = {}

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

        self.pm_list = tk.Listbox(self.left_pm_frame)
        self.room_list = tk.Listbox(self.left_room_frame)

        self.pm_list.pack(fill="both", expand=True)
        self.room_list.pack(fill="both", expand=True)

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

        self.right_users_frame.pack(fill="both", expand=True)
        self.right_rooms_frame.pack(fill="both", expand=True)

        self.users_list = tk.Listbox(self.right_users_frame)
        self.rooms_list_right = tk.Listbox(self.right_rooms_frame)

        self.users_list.pack(fill="both", expand=True)
        self.rooms_list_right.pack(fill="both", expand=True)

    def send_message(self):
        msg = self.input_entry.get()
        self.chat_box.config(state="normal")
        self.chat_box.insert("end", msg + "\n")
        self.chat_box.config(state="disabled")
        self.input_entry.delete(0, "end")