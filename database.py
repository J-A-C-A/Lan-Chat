import sqlite3 as sql
import threading as thr

class Database():
    def __init__(self):
        self.conn = sql.connect("chat.db",check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.db_lock = thr.Lock()
        self.init_db()

    def init_db(self):
        self.cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT NOT NULL,
        receiver TEXT,
        room TEXT,
        time_stamp TEXT NOT NULL,
        content TEXT NOT NULL
        )
        ''')
        self.conn.commit()

    def save_message(self,sender,time_stamp,content,receiver=None,room=None):
        #PM: receiver=user, room=None
        #ROOM: receiver=None, room=name
        with self.db_lock:
            self.cursor.execute('''INSERT INTO messages (sender,receiver,room,time_stamp,content) VALUES (?,?,?,?,?)''',(sender,receiver,room,time_stamp,content))
            self.conn.commit()
        print("SAVED TO DB")

    def get_pm_history(self,user1,user2):
        self.cursor.execute('''
        SELECT sender,receiver,room,time_stamp,content FROM messages WHERE (sender = ? AND receiver = ?) OR (sender = ? AND receiver = ?) ORDER BY time_stamp ASC
''',(user1,user2,user2,user1))
        return self.cursor.fetchall()

    def get_room_history(self,room):
        self.cursor.execute('''
        SELECT sender,time_stamp,content FROM messages WHERE room = ? ORDER BY time_stamp ASC
''',(room,))
        return self.cursor.fetchall()






