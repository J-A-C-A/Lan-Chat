import tkinter as tk
from gui import ChatGUI
from client import Client

def main():
    root = tk.Tk()
    client = Client()
    app = ChatGUI(root,client)
    root.mainloop()

if __name__ == "__main__":
    main()