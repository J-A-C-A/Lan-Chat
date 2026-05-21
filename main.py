import tkinter as tk
from queue import Queue
from gui import ChatGUI
from client import Client

def main():
    q = Queue()
    root = tk.Tk()
    client = Client(q)
    client.connect_gui()
    app = ChatGUI(root,client,q)
    root.mainloop()

if __name__ == "__main__":
    main()