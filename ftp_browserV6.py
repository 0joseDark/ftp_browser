import sys
import os
from ftplib import FTP
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, QListWidget, QSplitter, QMessageBox, QFileDialog, QInputDialog, QTabWidget
from PyQt5.QtCore import Qt

class FTPBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FTP Browser")
        self.resize(1000, 600)

        # Configurando o layout principal da aplicação
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # Layout para os campos de conexão
        self.connection_layout = QHBoxLayout()
        
        # Campo para inserir o host
        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("Host")
        self.connection_layout.addWidget(QLabel("Servidor:"))
        self.connection_layout.addWidget(self.host_input)
        
        # Campo para inserir o nome de usuário
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Nome de usuário")
        self.connection_layout.addWidget(QLabel("Nome de utilizador:"))
        self.connection_layout.addWidget(self.user_input)
        
        # Campo para inserir a senha
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Palavra-passe")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.connection_layout.addWidget(QLabel("Palavra-passe:"))
        self.connection_layout.addWidget(self.password_input)
        
        # Campo para inserir a porta
        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("Porta")
        self.port_input.setText("21")
        self.connection_layout.addWidget(QLabel("Porta:"))
        self.connection_layout.addWidget(self.port_input)
        
        # Botão de conexão
        self.connect_button = QPushButton("Ligação rápida")
        self.connect_button.clicked.connect(self.connect_to_ftp)
        self.connection_layout.addWidget(self.connect_button)

        # Adiciona o layout de conexão ao layout principal
        self.main_layout.addLayout(self.connection_layout)

        # Divisor para os exploradores de arquivos local e remoto
        self.splitter = QSplitter(Qt.Horizontal)
        self.main_layout.addWidget(self.splitter)

        # Explorador de arquivos local
        self.local_file_browser = FileBrowser(self, local=True)
        self.splitter.addWidget(self.local_file_browser)

        # Explorador de arquivos remoto (FTP)
        self.remote_file_browser = FileBrowser(self, local=False)
        self.splitter.addWidget(self.remote_file_browser)

        # Armazena o objeto FTP
        self.ftp = None

    def connect_to_ftp(self):
        """Conecta ao servidor FTP com as credenciais fornecidas"""
        host = self.host_input.text()
        user = self.user_input.text()
        password = self.password_input.text()
        port = int(self.port_input.text())

        try:
            # Cria a conexão FTP
            self.ftp = FTP()
            self.ftp.connect(host, port)
            self.ftp.login(user, password)

            # Carrega o diretório raiz do FTP
            self.remote_file_browser.load_directory(self.ftp.pwd(), ftp=self.ftp)
        except Exception as e:
            QMessageBox.critical(self, "Erro de conexão", str(e))

class FileBrowser(QWidget):
    def __init__(self, parent=None, local=True):
        super().__init__(parent)
        self.is_local = local
        self.current_path = ""

        # Configura o layout do explorador
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)

        # Lista de arquivos e diretórios
        self.file_list = QListWidget()
        self.file_list.itemDoubleClicked.connect(self.navigate)
        self.layout.addWidget(self.file_list)

        # Carrega o diretório inicial
        if self.is_local:
            self.load_directory(os.path.expanduser("~"))  # Diretório inicial (home)

    def load_directory(self, path, ftp=None):
        """Carrega o diretório especificado"""
        self.file_list.clear()
        self.current_path = path

        if self.is_local:
            # Navega em um diretório local
            try:
                items = os.listdir(path)
                self.file_list.addItem("..")
                for item in items:
                    self.file_list.addItem(item)
            except Exception as e:
                QMessageBox.critical(self, "Erro", str(e))
        else:
            # Navega em um diretório FTP
            try:
                ftp.cwd(path)
                items = ftp.nlst()
                self.file_list.addItem("..")
                for item in items:
                    self.file_list.addItem(item)
            except Exception as e:
                QMessageBox.critical(self, "Erro", str(e))

    def navigate(self, item):
        """Navega para um novo diretório ou abre um arquivo"""
        selected_item = item.text()

        if self.is_local:
            new_path = os.path.join(self.current_path, selected_item)
            if os.path.isdir(new_path):
                self.load_directory(new_path)
            else:
                QMessageBox.information(self, "Arquivo", f"Você selecionou o arquivo: {selected_item}")
        else:
            if selected_item == "..":
                new_path = "/".join(self.current_path.split("/")[:-1]) or "/"
            else:
                new_path = f"{self.current_path}/{selected_item}"

            try:
                self.load_directory(new_path, ftp=self.parent().ftp)
            except Exception as e:
                QMessageBox.critical(self, "Erro", str(e))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FTPBrowser()
    window.show()
    sys.exit(app.exec_())
