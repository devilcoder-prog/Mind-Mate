import sqlite3

# Create user table
def create_usertable():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Add a new user
def add_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
    conn.commit()
    conn.close()

# Login check
def login_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
    data = c.fetchone()
    conn.close()
    return data

import sqlite3

conn = sqlite3.connect('users.db', check_same_thread=False)
c = conn.cursor()

def create_usertable():
    c.execute('CREATE TABLE IF NOT EXISTS userstable(username TEXT, password TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS mood_logs(username TEXT, mood TEXT, note TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)')
    c.execute('CREATE TABLE IF NOT EXISTS phq9_results(username TEXT, score INTEGER, level TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)')
    c.execute('CREATE TABLE IF NOT EXISTS chat_history(username TEXT, message TEXT, response TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)')
    conn.commit()

def add_user(username, password):
    c.execute('INSERT INTO userstable(username,password) VALUES (?,?)', (username, password))
    conn.commit()

def login_user(username, password):
    c.execute('SELECT * FROM userstable WHERE username = ? AND password = ?', (username, password))
    return c.fetchone()

def save_mood(username, mood, note):
    c.execute('INSERT INTO mood_logs(username, mood, note) VALUES (?, ?, ?)', (username, mood, note))
    conn.commit()

def save_phq9(username, score, level):
    c.execute('INSERT INTO phq9_results(username, score, level) VALUES (?, ?, ?)', (username, score, level))
    conn.commit()

def save_chat(username, message, response):
    c.execute('INSERT INTO chat_history(username, message, response) VALUES (?, ?, ?)', (username, message, response))
    conn.commit()
