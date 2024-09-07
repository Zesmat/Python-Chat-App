import socket
import threading
import sqlite3
import logging
import queue

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize SQLite database
def init_db():
    with sqlite3.connect('chat_server.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                            username TEXT PRIMARY KEY,
                            password TEXT NOT NULL
                        )''')
        conn.commit()

def handle_client(client_socket, addr, message_queue):
    username = None
    try:
        while True:
            message = client_socket.recv(1024).decode().strip()
            if not message:
                break
            logging.debug(f"Received message from {addr}: {message}")
            if message.startswith("REGISTER") or message.startswith("LOGIN"):
                parts = message.split()
                if len(parts) != 3:
                    client_socket.send("INVALID_FORMAT".encode())
                    continue
                command, username, password = parts
                if command == "REGISTER":
                    if register_user(username, password):
                        client_socket.send("REGISTERED".encode())
                    else:
                        client_socket.send("REGISTER_FAILED".encode())
                elif command == "LOGIN":
                    if authenticate_user(username, password):
                        client_socket.send("LOGGED_IN".encode())
                    else:
                        client_socket.send("LOGIN_FAILED".encode())
            else:
                if username is None:
                    client_socket.send("NOT_LOGGED_IN".encode())
                else:
                    # Add message to the queue for broadcasting
                    message_queue.put((message, client_socket))
    except Exception as e:
        logging.error(f"Error handling client {addr}: {e}")
    finally:
        logging.info(f"Client {addr} disconnected")
        if client_socket in clients:
            clients.remove(client_socket)
        client_socket.close()
def register_user(username, password):
    try:
        with sqlite3.connect('chat_server.db') as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def authenticate_user(username, password):
    with sqlite3.connect('chat_server.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()
    return user is not None

def broadcast_messages(message_queue):
    while True:
        message, sender_socket = message_queue.get()
        if message is None:
            break
        for client in clients:
            if client != sender_socket:
                try:
                    # Send the actual message without length prefix
                    client.send(message.encode())
                except Exception as e:
                    logging.error(f"Error sending message to a client: {e}")
                    client.close()
                    clients.remove(client)
def start_server():
    init_db()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', 8000))
    server.listen(5)
    logging.info("Server started, waiting for clients...")

    message_queue = queue.Queue()
    broadcast_thread = threading.Thread(target=broadcast_messages, args=(message_queue,))
    broadcast_thread.start()

    try:
        while True:
            client_socket, addr = server.accept()
            clients.append(client_socket)
            logging.info(f"Client {addr} connected")
            client_thread = threading.Thread(target=handle_client, args=(client_socket, addr, message_queue))
            client_thread.start()
    except KeyboardInterrupt:
        logging.info("Server shutting down...")
    finally:
        message_queue.put((None, None))  # Signal the broadcast thread to exit
        broadcast_thread.join()
        for client in clients:
            client.close()
        server.close()

if __name__ == "__main__":
    clients = []
    start_server()