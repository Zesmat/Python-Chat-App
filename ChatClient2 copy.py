import sys
import socket
import threading
import logging
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QLabel, QLineEdit, QPushButton, QMessageBox, QStackedLayout, QHBoxLayout, QScrollArea)
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5.QtGui import QIcon, QFont

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class SignalHandler(QObject):
    show_chat_signal = pyqtSignal()
    show_login_signal = pyqtSignal()
    registration_success_signal = pyqtSignal(str)
    registration_failure_signal = pyqtSignal(str)
    login_success_signal = pyqtSignal(str)
    login_failure_signal = pyqtSignal(str)
    new_message_signal = pyqtSignal(str, bool)
    new_message_signal = pyqtSignal(str, bool, str)

    def __init__(self, parent):
        super().__init__(parent)
        self.show_chat_signal.connect(parent.show_chat)
        self.show_login_signal.connect(parent.show_login)
        self.registration_success_signal.connect(parent.show_message_box)
        self.registration_failure_signal.connect(parent.show_message_box)
        self.login_success_signal.connect(parent.show_message_box)
        self.login_failure_signal.connect(parent.show_message_box)
        self.new_message_signal.connect(parent.display_message)

class ChatClient(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chat Application")
        self.setGeometry(300, 300, 400, 600)
        self.setWindowIcon(QIcon("chat_icon.png"))

        self.host = '192.168.1.11'  # Update this to your server's IP address
        self.port = 8000  # Update this to your server's port
        self.client_socket = None
        self.username = None

        self.main_widget = None
        self.main_layout = None

        self.signal_handler = SignalHandler(self)

        self.init_ui()

    def init_ui(self):
        # WhatsApp-like Styles
        self.setStyleSheet("""
            QWidget {
                background-color: #075E54;
                color: white;
            }
            QLineEdit {
                background-color: white;
                color: black;
                border-radius: 10px;
                padding: 10px;
            }
            QPushButton {
                background-color: #25D366;
                color: white;
                border-radius: 10px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #128C7E;
            }
            QLabel {
                font-size: 14px;
            }
            QScrollArea {
                border: none;
            }
        """)

        # Font
        font = QFont()
        font.setPointSize(10)
        self.setFont(font)

        # Create main widget and layout
        self.main_widget = QWidget()
        self.main_layout = QStackedLayout()
        self.main_widget.setLayout(self.main_layout)

        self.create_login_widget()
        self.create_register_widget()
        self.create_chat_widget()

        self.main_layout.addWidget(self.login_widget)
        self.main_layout.addWidget(self.register_widget)
        self.main_layout.addWidget(self.chat_widget)

        self.setCentralWidget(self.main_widget)

        self.main_layout.setCurrentWidget(self.login_widget)

    def create_login_widget(self):
        self.login_widget = QWidget()
        login_layout = QVBoxLayout()
        login_layout.addWidget(QLabel("Username:"))
        self.login_username = QLineEdit()
        login_layout.addWidget(self.login_username)

        login_layout.addWidget(QLabel("Password:"))
        self.login_password = QLineEdit()
        self.login_password.setEchoMode(QLineEdit.Password)
        login_layout.addWidget(self.login_password)

        login_button = QPushButton("Login")
        login_button.clicked.connect(self.start_login_thread)
        login_layout.addWidget(login_button)

        register_button = QPushButton("Register")
        register_button.clicked.connect(self.show_register)
        login_layout.addWidget(register_button)

        self.login_widget.setLayout(login_layout)

    def create_register_widget(self):
        self.register_widget = QWidget()
        register_layout = QVBoxLayout()
        register_layout.addWidget(QLabel("Username:"))
        self.register_username = QLineEdit()
        register_layout.addWidget(self.register_username)

        register_layout.addWidget(QLabel("Password:"))
        self.register_password = QLineEdit()
        self.register_password.setEchoMode(QLineEdit.Password)
        register_layout.addWidget(self.register_password)

        register_button = QPushButton("Register")
        register_button.clicked.connect(self.start_register_thread)
        register_layout.addWidget(register_button)

        back_to_login_button = QPushButton("Back to Login")
        back_to_login_button.clicked.connect(self.show_login)
        register_layout.addWidget(back_to_login_button)

        self.register_widget.setLayout(register_layout)

    def create_chat_widget(self):
        self.chat_widget = QWidget()
        chat_layout = QVBoxLayout()

        # Scroll area for messages
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.message_widget = QWidget()
        self.message_layout = QVBoxLayout()
        self.message_layout.addStretch()
        self.message_widget.setLayout(self.message_layout)

        self.scroll_area.setWidget(self.message_widget)
        chat_layout.addWidget(self.scroll_area)

        # Message input and send button
        message_input_layout = QHBoxLayout()
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type a message...")
        self.message_input.returnPressed.connect(self.send_message)
        message_input_layout.addWidget(self.message_input)

        send_button = QPushButton("Send")
        send_button.clicked.connect(self.send_message)
        message_input_layout.addWidget(send_button)

        chat_layout.addLayout(message_input_layout)
        self.chat_widget.setLayout(chat_layout)

    def show_login(self):
        self.main_layout.setCurrentWidget(self.login_widget)

    def show_register(self):
        self.main_layout.setCurrentWidget(self.register_widget)

    def show_chat(self):
        self.main_layout.setCurrentWidget(self.chat_widget)
        if not self.client_socket or self.client_socket._closed:
            logging.error("Socket not connected. Reconnecting...")
            self.connect_to_server()
        
    def show_message_box(self, message):
        QMessageBox.information(self, "Information", message)

    def start_register_thread(self):
        threading.Thread(target=self.register, daemon=True).start()

    def start_login_thread(self):
        threading.Thread(target=self.login, daemon=True).start()

    def connect_to_server(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.host, self.port))
            logging.debug("Connected to server")
        except Exception as e:
            logging.error(f"Failed to connect to server: {e}")
            self.signal_handler.login_failure_signal.emit("Failed to connect to server. Please try again.")

    def register(self):
        self.username = self.register_username.text()
        password = self.register_password.text()
        if not self.username or not password:
            self.signal_handler.registration_failure_signal.emit("Username and password cannot be empty.")
            return

        logging.debug(f"Registering user {self.username}")

        self.connect_to_server()
        self.client_socket.sendall(f"REGISTER {self.username} {password}".encode())
        response = self.client_socket.recv(1024).decode()

        if response == "REGISTERED":
            self.signal_handler.registration_success_signal.emit("Registration successful. Please log in.")
            self.signal_handler.show_login_signal.emit()
        else:
            self.signal_handler.registration_failure_signal.emit("Registration failed. Please try again.")
        self.client_socket.close()

    def login(self):
        self.username = self.login_username.text()
        password = self.login_password.text()
        if not self.username or not password:
            self.signal_handler.login_failure_signal.emit("Username and password cannot be empty.")
            return

        logging.debug(f"Logging in user {self.username}")

        self.connect_to_server()
        self.client_socket.sendall(f"LOGIN {self.username} {password}".encode())
        response = self.client_socket.recv(1024).decode()

        if response == "LOGGED_IN":
            self.signal_handler.login_success_signal.emit("Login successful.")
            self.signal_handler.show_chat_signal.emit()
            threading.Thread(target=self.receive_messages, daemon=True).start()
        else:
            self.signal_handler.login_failure_signal.emit("Login failed. Please try again.")
            self.client_socket.close()

    def receive_messages(self):
        while True:
            try:
                # Receive the full message
                message = self.client_socket.recv(1024).decode()
                if not message:
                    break
                
                logging.debug(f"Received message: {message}")
                if ':' in message:
                    sender, content = message.split(':', 1)
                    is_own_message = sender.strip() == self.username
                    self.signal_handler.new_message_signal.emit(content.strip(), is_own_message, sender.strip())
                else:
                    # Handle system messages or errors
                    self.signal_handler.new_message_signal.emit(message, False, "System")
            except Exception as e:
                logging.error(f"Receive message error: {e}")
                break
        def send_message(self):
            message = self.message_input.text()
            if message.strip():  # Check if there's any non-whitespace content
                try:
                    # Send the actual message without length prefix
                    self.client_socket.sendall(f"{self.username}: {message}".encode())
                    self.signal_handler.new_message_signal.emit(message, True, self.username)
                    self.message_input.clear()
                except Exception as e:
                    logging.error(f"Failed to send message: {e}")
                    QMessageBox.warning(self, "Error", "Failed to send message. Please try again.")
    def display_message(self, content, is_own_message, sender):
        message_label = QLabel(f"{sender}: {content}" if not is_own_message else content)
        message_label.setWordWrap(True)
        message_label.setMaximumWidth(300)

        if is_own_message:
            message_label.setStyleSheet("""
                background-color: #DCF8C6;
                color: black;
                border-radius: 10px;
                padding: 10px;
                margin: 5px;
            """)
            alignment = Qt.AlignRight
        else:
            message_label.setStyleSheet("""
                background-color: #FFFFFF;
                color: black;
                border-radius: 10px;
                padding: 10px;
                margin: 5px;
            """)
            alignment = Qt.AlignLeft

        message_layout = QHBoxLayout()
        if is_own_message:
            message_layout.addStretch()
            message_layout.addWidget(message_label)
        else:
            message_layout.addWidget(message_label)
            message_layout.addStretch()     
        self.message_layout.insertLayout(self.message_layout.count()-1, message_layout)

        # Ensure the new message is visible
        QApplication.processEvents()
        self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        )

        # Refresh the widget to ensure proper layout
        self.message_widget.adjustSize()
        self.scroll_area.setWidget(self.message_widget)
    def closeEvent(self, event):
        if self.client_socket:
            try:
                self.client_socket.shutdown(socket.SHUT_RDWR)
                self.client_socket.close()
            except Exception as e:
                logging.error(f"Error closing socket: {e}")
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    client = ChatClient()
    client.show()
    sys.exit(app.exec_())