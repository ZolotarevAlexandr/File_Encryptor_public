import sys
import os
import random

from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog
from PyQt5.QtGui import QIcon
from cryptography.fernet import Fernet, InvalidToken
import cgitb

cgitb.enable(format='text')

KEY_SET = []  # Insert your Fernet keys here


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def get_files_list(directory):
    files_list = []
    for path, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(path, file)
            files_list.append(file_path)
    return files_list


def check_encrypted(filename):
    with open(filename, 'rb') as file:
        content = file.read()
    try:
        key_index = int(content[-2:])
        key = KEY_SET[key_index]
        Fernet(key).decrypt(content[:-2])
        return True
    except (InvalidToken, ValueError):
        return False


def encrypt_file(filename):
    if not check_encrypted(filename):
        with open(filename, 'rb') as file:
            content = file.read()

        key = random.choice(KEY_SET)
        content = Fernet(key).encrypt(content) + str(KEY_SET.index(key)).zfill(2).encode()

        with open(filename, 'wb') as file:
            file.write(content)
    else:
        raise Exception('File already encrypted')


def decrypt_file(filename):
    if check_encrypted(filename):
        with open(filename, 'rb') as file:
            content = file.read()
        key_index = int(content[-2:].decode())
        key = KEY_SET[key_index]
        content = Fernet(key).decrypt(content[:-2])
        with open(filename, 'wb') as file:
            file.write(content)
    else:
        raise Exception('File already decrypted')


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi(resource_path('data/MainWindow.ui'), self)
        self.setWindowTitle('File Encryptor')
        self.setWindowIcon(QIcon(resource_path('data/icon.ico')))
        self.browse_btn.clicked.connect(self.get_dir)
        self.encrypt_btn.clicked.connect(self.encrypt_dir)
        self.decrypt_btn.clicked.connect(self.decrypt_dir)

    def get_dir(self):
        filename = QFileDialog.getExistingDirectory(self, 'Choose Directory')
        self.directory_inp.setText(filename)

    def encrypt_dir(self):
        self.logs.clear()
        directory = self.directory_inp.text()
        files_amount = len(get_files_list(directory))
        for index, file in enumerate(get_files_list(directory)):
            try:
                encrypt_file(file)
                self.logs.appendPlainText(f'File {file} successfully encrypted')
            except Exception as e:
                self.logs.appendPlainText(f'Exception ({e}) occurred on file {file}')
            self.progress_bar.setValue(int(((index + 1) / files_amount) * 100))

    def decrypt_dir(self):
        self.logs.clear()
        directory = self.directory_inp.text()
        files_amount = len(get_files_list(directory))
        for index, file in enumerate(get_files_list(directory)):
            try:
                decrypt_file(file)
                self.logs.appendPlainText(f'File {file} successfully decrypted')
            except Exception as e:
                self.logs.appendPlainText(f'Exception ({e}) occurred on file {file}')
            self.progress_bar.setValue(int(((index + 1) / files_amount) * 100))


class CheckPassword(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi(resource_path('data/CheckPasswordWindow.ui'), self)
        self.setWindowTitle('File Encryptor')
        self.setWindowIcon(QIcon(resource_path('data/icon.ico')))
        self.log_in_btn.clicked.connect(self.check_password)

    def check_password(self):
        try:
            password_attempt = self.password_inp.text()
            with open(f'{os.getenv("SystemDrive")}/ProgramData/password.txt') as file:
                password = file.read()
            key_index = int(password[-2:])
            key = KEY_SET[key_index]
            password = Fernet(key).decrypt(password).decode()
            if password_attempt == password:
                self.close()
                main_window.show()
            else:
                self.error_label.setText('Wrong password!')
        except Exception as e:
            self.error_label.setText(f'Exception ({e}) occurred')


class CreatePassword(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi(resource_path('data/CreatePasswordWindow.ui'), self)
        self.setWindowTitle('File Encryptor')
        self.setWindowIcon(QIcon(resource_path('data/icon.ico')))
        self.save_btn.clicked.connect(self.save_password)

    def save_password(self):
        try:
            password = self.password_inp.text()
            repeated_password = self.password_rep.text()
            if password != repeated_password:
                self.error_label.setText("Passwords don't match")
                return
            if not password:
                self.error_label.setText("Can't create empty password")
                return
            key = random.choice(KEY_SET)
            password_inp = Fernet(key).encrypt(password.encode()) + \
                           str(KEY_SET.index(key)).zfill(2).encode()
            with open(f'{os.getenv("SystemDrive")}/ProgramData/password.txt', 'wb') as file:
                file.write(password_inp)
            self.close()
            main_window.show()
        except Exception as e:
            self.error_label.setText(f'Exception ({e}) occurred')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    if not os.path.exists(f'{os.getenv("SystemDrive")}/ProgramData/password.txt'):
        create_password_window = CreatePassword()
        create_password_window.show()
    else:
        password_check_window = CheckPassword()
        password_check_window.show()
    sys.exit(app.exec())
