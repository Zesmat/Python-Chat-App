import unittest
from PyQt5.QtWidgets import QApplication
from ChatClient2 import ChatClient  # Import your ChatClient class

class TestChatClient(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication([])  # Create a QApplication instance

    def setUp(self):
        self.chat_client = ChatClient()  # Create an instance of ChatClient

    def test_initial_ui_state(self):
        self.assertEqual(self.chat_client.main_layout.currentWidget(), self.chat_client.login_widget)

    def test_show_register(self):
        self.chat_client.show_register()
        self.assertEqual(self.chat_client.main_layout.currentWidget(), self.chat_client.register_widget)

    def test_show_chat(self):
        self.chat_client.show_chat()
        self.assertEqual(self.chat_client.main_layout.currentWidget(), self.chat_client.chat_widget)

    @classmethod
    def tearDownClass(cls):
        cls.app.quit()  # Clean up the QApplication instance

if __name__ == '__main__':
    unittest.main()
