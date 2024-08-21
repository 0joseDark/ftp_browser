import sys
import os
from ftplib import FTP
from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import (QApplication, QMainWindow, QToolBar, QAction, QLineEdit, QTabWidget, 
                             QVBoxLayout, QListWidget, QDialog, QPushButton, QFileDialog, 
                             QMessageBox, QLabel, QInputDialog, QHBoxLayout)

# Classe que gerencia a conexão FTP e a exibição do diretório atual
class FTPClient(QDialog):
    def __init__(self, parent=None, ftp_host="", ftp_user="anonymous", ftp_passwd=""):
        super().__init__(parent)
        self.ftp_host = ftp_host  # Host do servidor FTP
        self.ftp_user = ftp_user  # Nome de usuário
        self.ftp_passwd = ftp_passwd  # Senha do usuário
        self.ftp = FTP()  # Cria uma instância da classe FTP
        self.layout = QVBoxLayout()  # Layout vertical para os widgets

        # Lista de arquivos e diretórios
        self.file_list = QListWidget()
        self.file_list.itemDoubleClicked.connect(self.navigate_to_directory)
        self.layout.addWidget(self.file_list)

        # Botão para download do arquivo selecionado
        self.download_button = QPushButton("Download File")
        self.download_button.clicked.connect(self.download_file)
        self.layout.addWidget(self.download_button)

        self.setLayout(self.layout)

    def load_ftp_directory(self):
        # Conecta ao servidor FTP e carrega o diretório
        try:
            self.ftp.connect(self.ftp_host)  # Conecta ao servidor FTP
            self.ftp.login(self.ftp_user, self.ftp_passwd)  # Faz o login no servidor
            self.ftp.cwd("/")  # Navega até o diretório raiz
            self.update_file_list()  # Atualiza a lista de arquivos e diretórios
        except Exception as e:
            QMessageBox.critical(self, "Connection Error", f"Could not connect to FTP server: {e}")

    def update_file_list(self):
        # Atualiza a lista de arquivos e diretórios
        self.file_list.clear()
        files = []
        self.ftp.retrlines('LIST', files.append)  # Recupera a lista de arquivos e diretórios
        for file in files:
            self.file_list.addItem(file)  # Adiciona cada arquivo/diretório à lista

    def navigate_to_directory(self, item):
        # Navega para o diretório selecionado ou tenta baixar o arquivo
        selected_item = item.text()
        if selected_item.startswith('d'):  # Diretório
            parts = selected_item.split()
            directory_name = parts[-1]
            try:
                self.ftp.cwd(directory_name)  # Navega até o diretório
                self.update_file_list()  # Atualiza a lista de arquivos e diretórios
            except Exception as e:
                QMessageBox.critical(self, "Navigation Error", f"Could not navigate to directory: {e}")
        else:  # Arquivo
            QMessageBox.information(self, "File Selected", "Please use the Download button to download files.")

    def download_file(self):
        # Faz o download do arquivo selecionado
        selected_item = self.file_list.currentItem().text()
        if not selected_item.startswith('d'):  # Arquivo
            parts = selected_item.split()
            file_name = parts[-1]
            save_path, _ = QFileDialog.getSaveFileName(self, "Save File", file_name)
            if save_path:
                with open(save_path, 'wb') as f:
                    try:
                        self.ftp.retrbinary(f"RETR {file_name}", f.write)  # Baixa o arquivo
                        QMessageBox.information(self, "Download Complete", f"File {file_name} downloaded successfully.")
                    except Exception as e:
                        QMessageBox.critical(self, "Download Error", f"Could not download file: {e}")
        else:
            QMessageBox.warning(self, "Invalid Selection", "Please select a file to download.")

# Classe principal do navegador FTP
class FTPBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python FTP Browser")
        self.setGeometry(100, 100, 1200, 800)

        # Gerenciamento de abas
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_current_tab)  # Fecha a aba quando solicitado

        self.setCentralWidget(self.tabs)

        # Layout para inputs de conexão
        self.connection_layout = QHBoxLayout()
        
        # Campo de host
        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("FTP Host")
        self.connection_layout.addWidget(self.host_input)

        # Campo de usuário
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Username (default: anonymous)")
        self.connection_layout.addWidget(self.user_input)

        # Campo de senha
        self.passwd_input = QLineEdit()
        self.passwd_input.setPlaceholderText("Password (default: empty)")
        self.passwd_input.setEchoMode(QLineEdit.Password)
        self.connection_layout.addWidget(self.passwd_input)

        # Botão de conectar
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.connect_to_ftp)
        self.connection_layout.addWidget(self.connect_button)

        # Botão para histórico de conexões
        self.history_button = QPushButton("Connection History")
        self.history_button.clicked.connect(self.show_connection_history)
        self.connection_layout.addWidget(self.history_button)

        # Widget central que segura os inputs de conexão
        self.input_widget = QMainWindow()
        self.input_widget.setLayout(self.connection_layout)
        self.setMenuWidget(self.input_widget)

    def add_new_tab(self, ftp_host, ftp_user, ftp_passwd):
        # Adiciona uma nova aba ao navegador FTP
        browser = FTPClient(self, ftp_host, ftp_user, ftp_passwd)
        i = self.tabs.addTab(browser, ftp_host)
        self.tabs.setCurrentIndex(i)
        browser.load_ftp_directory()  # Carrega o diretório FTP

    def close_current_tab(self, i):
        # Fecha a aba atual se houver mais de uma aberta
        if self.tabs.count() > 1:
            self.tabs.removeTab(i)

    def connect_to_ftp(self):
        # Conecta ao servidor FTP usando os dados fornecidos
        ftp_host = self.host_input.text()
        ftp_user = self.user_input.text() or "anonymous"
        ftp_passwd = self.passwd_input.text()

        if ftp_host:
            self.add_new_tab(ftp_host, ftp_user, ftp_passwd)
            self.record_connection_history(ftp_host, ftp_user)

    def record_connection_history(self, ftp_host, ftp_user):
        # Registra a conexão no histórico
        with open('connection_history.txt', 'a') as f:
            f.write(f"{ftp_host},{ftp_user}\n")

    def show_connection_history(self):
        # Exibe o histórico de conexões
        history_manager = ConnectionHistoryManager(self)
        if history_manager.exec_() == QDialog.Accepted:
            selected_host, selected_user = history_manager.get_selected_connection()
            self.host_input.setText(selected_host)
            self.user_input.setText(selected_user)

# Classe para gerenciar o histórico de conexões
class ConnectionHistoryManager(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Connection History")
        self.layout = QVBoxLayout()

        self.history_list = QListWidget()
        self.load_history()
        self.layout.addWidget(self.history_list)

        # Botão para selecionar uma conexão do histórico
        self.select_button = QPushButton("Connect")
        self.select_button.clicked.connect(self.accept)
        self.layout.addWidget(self.select_button)

        self.setLayout(self.layout)

    def load_history(self):
        # Carrega o histórico de conexões do arquivo
        if os.path.exists('connection_history.txt'):
            with open('connection_history.txt', 'r') as f:
                for line in f:
                    self.history_list.addItem(line.strip())

    def get_selected_connection(self):
        # Retorna a conexão selecionada
        selected_item = self.history_list.currentItem().text()
        return selected_item.split(',')

# Executa o aplicativo
app = QApplication(sys.argv)
QApplication.setApplicationName("Python FTP Browser")
window = FTPBrowser()
window.show()
sys.exit(app.exec_())
