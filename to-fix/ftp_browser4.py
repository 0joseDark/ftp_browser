import sys
import os
from ftplib import FTP
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QListWidget, QDialog, 
                             QPushButton, QFileDialog, QMessageBox, QLineEdit, QTabWidget, 
                             QWidget, QHBoxLayout, QLabel, QInputDialog, QMenu, QAction, 
                             QDockWidget)
from PyQt5.QtCore import Qt

# Classe que gerencia a conexão FTP e a exibição do diretório atual
class FTPClient(QDialog):
    def __init__(self, parent=None, ftp_host="", ftp_user="anonymous", ftp_passwd="", ftp_port=21):
        super().__init__(parent)
        self.ftp_host = ftp_host
        self.ftp_user = ftp_user
        self.ftp_passwd = ftp_passwd
        self.ftp_port = ftp_port
        self.ftp = FTP()
        self.layout = QVBoxLayout()

        # Lista de arquivos e diretórios no servidor FTP
        self.file_list = QListWidget()
        self.file_list.itemDoubleClicked.connect(self.navigate_to_directory)
        self.file_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_list.customContextMenuRequested.connect(self.show_context_menu)
        self.layout.addWidget(self.file_list)

        self.setLayout(self.layout)

    def load_ftp_directory(self):
        # Conecta ao servidor FTP e carrega o diretório
        try:
            self.ftp.connect(self.ftp_host, self.ftp_port)
            self.ftp.login(self.ftp_user, self.ftp_passwd)
            self.ftp.cwd("/")
            self.update_file_list()
        except Exception as e:
            QMessageBox.critical(self, "Connection Error", f"Could not connect to FTP server: {e}")

    def update_file_list(self):
        # Atualiza a lista de arquivos e diretórios
        self.file_list.clear()
        files = []
        self.ftp.retrlines('LIST', files.append)
        for file in files:
            self.file_list.addItem(file)

    def navigate_to_directory(self, item):
        # Navega para o diretório ou inicia a confirmação de download do arquivo
        selected_item = item.text()
        if selected_item.startswith('d'):
            parts = selected_item.split()
            directory_name = parts[-1]
            try:
                self.ftp.cwd(directory_name)
                self.update_file_list()
            except Exception as e:
                QMessageBox.critical(self, "Navigation Error", f"Could not navigate to directory: {e}")
        else:
            file_name = selected_item.split()[-1]
            self.confirm_download(file_name)

    def confirm_download(self, file_name):
        # Aba de confirmação de download
        tab = self.parent().parent().add_confirmation_tab(file_name, self.ftp)
        tab.confirmation_button.clicked.connect(lambda: self.download_file(file_name, tab))

    def download_file(self, file_name, tab):
        # Realiza o download do arquivo após a confirmação
        save_path, _ = QFileDialog.getSaveFileName(self, "Save File", file_name)
        if save_path:
            with open(save_path, 'wb') as f:
                try:
                    self.ftp.retrbinary(f"RETR {file_name}", f.write)
                    QMessageBox.information(self, "Download Complete", f"File {file_name} downloaded successfully.")
                    tab.close_tab()
                except Exception as e:
                    QMessageBox.critical(self, "Download Error", f"Could not download file: {e}")

    def show_context_menu(self, position):
        # Menu contextual para criar, editar, renomear e excluir arquivos/pastas no servidor FTP
        menu = QMenu()

        create_folder_action = QAction("Create Folder", self)
        create_folder_action.triggered.connect(self.create_folder)
        menu.addAction(create_folder_action)

        delete_item_action = QAction("Delete", self)
        delete_item_action.triggered.connect(self.delete_item)
        menu.addAction(delete_item_action)

        rename_item_action = QAction("Rename", self)
        rename_item_action.triggered.connect(self.rename_item)
        menu.addAction(rename_item_action)

        menu.exec_(self.file_list.viewport().mapToGlobal(position))

    def create_folder(self):
        # Cria uma nova pasta no servidor FTP
        folder_name, ok = QInputDialog.getText(self, "Create Folder", "Folder Name:")
        if ok and folder_name:
            try:
                self.ftp.mkd(folder_name)
                self.update_file_list()
            except Exception as e:
                QMessageBox.critical(self, "Create Folder Error", f"Could not create folder: {e}")

    def delete_item(self):
        # Exclui o item selecionado (arquivo ou pasta) no servidor FTP
        selected_item = self.file_list.currentItem().text()
        if selected_item:
            parts = selected_item.split()
            item_name = parts[-1]
            try:
                if selected_item.startswith('d'):
                    self.ftp.rmd(item_name)
                else:
                    self.ftp.delete(item_name)
                self.update_file_list()
            except Exception as e:
                QMessageBox.critical(self, "Delete Error", f"Could not delete item: {e}")

    def rename_item(self):
        # Renomeia o item selecionado no servidor FTP
        selected_item = self.file_list.currentItem().text()
        if selected_item:
            parts = selected_item.split()
            old_name = parts[-1]
            new_name, ok = QInputDialog.getText(self, "Rename Item", "New Name:")
            if ok and new_name:
                try:
                    self.ftp.rename(old_name, new_name)
                    self.update_file_list()
                except Exception as e:
                    QMessageBox.critical(self, "Rename Error", f"Could not rename item: {e}")

# Classe que gerencia a navegação local
class LocalFileBrowser(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout()

        # Lista de arquivos e diretórios locais
        self.file_list = QListWidget()
        self.file_list.itemDoubleClicked.connect(self.navigate_to_directory)
        self.file_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_list.customContextMenuRequested.connect(self.show_context_menu)
        self.layout.addWidget(self.file_list)

        self.setLayout(self.layout)
        self.load_local_directory(os.path.expanduser("~"))

    def load_local_directory(self, path):
        # Carrega a lista de arquivos e diretórios locais
        self.file_list.clear()
        try:
            for item in os.listdir(path):
                self.file_list.addItem(item)
            self.current_path = path
        except Exception as e:
            QMessageBox.critical(self, "Directory Load Error", f"Could not load directory: {e}")

    def navigate_to_directory(self, item):
        # Navega até o diretório local selecionado ou abre o arquivo
        selected_item = item.text()
        new_path = os.path.join(self.current_path, selected_item)
        if os.path.isdir(new_path):
            self.load_local_directory(new_path)
        else:
            QMessageBox.information(self, "File Selected", f"Selected file: {new_path}")

    def show_context_menu(self, position):
        # Menu contextual para criar, editar, renomear e excluir arquivos/pastas localmente
        menu = QMenu()

        create_folder_action = QAction("Create Folder", self)
        create_folder_action.triggered.connect(self.create_folder)
        menu.addAction(create_folder_action)

        create_file_action = QAction("Create File", self)
        create_file_action.triggered.connect(self.create_file)
        menu.addAction(create_file_action)

        delete_item_action = QAction("Delete", self)
        delete_item_action.triggered.connect(self.delete_item)
        menu.addAction(delete_item_action)

        rename_item_action = QAction("Rename", self)
        rename_item_action.triggered.connect(self.rename_item)
        menu.addAction(rename_item_action)

        menu.exec_(self.file_list.viewport().mapToGlobal(position))

    def create_folder(self):
        # Cria uma nova pasta localmente
        folder_name, ok = QInputDialog.getText(self, "Create Folder", "Folder Name:")
        if ok and folder_name:
            try:
                os.mkdir(os.path.join(self.current_path, folder_name))
                self.load_local_directory(self.current_path)
            except Exception as e:
                QMessageBox.critical(self, "Create Folder Error", f"Could not create folder: {e}")

    def create_file(self):
        # Cria um novo arquivo localmente
        file_name, ok = QInputDialog.getText(self, "Create File", "File Name:")
        if ok and file_name:
            try:
                open(os.path.join(self.current_path, file_name), 'w').close()
                self.load_local_directory(self.current_path)
            except Exception as e:
                QMessageBox.critical(self, "Create File Error", f"Could not create file: {e}")

    def delete_item(self):
        # Exclui o item selecionado localmente
        selected_item = self.file_list.currentItem().text()
        if selected_item:
            item_path = os.path.join(self.current_path, selected_item)
            try:
                if os.path.isdir(item_path):
                    os.rmdir(item_path)
                else:
                    os.remove(item_path)
                self.load_local_directory(self.current_path)
            except Exception as e:
                QMessageBox.critical(self, "Delete Error", f"Could not delete item: {e}")

    def rename_item(self):
        # Renomeia o item selecionado localmente
        selected_item = self.file_list.currentItem().text()
        if selected_item:
            old_path = os.path.join(self.current_path, selected_item)
            new_name, ok = QInputDialog.getText(self, "Rename Item", "New Name:")
            if ok and new_name:
                try:
                    new_path = os.path.join(self.current_path, new_name)
                    os.rename(old_path, new_path)
                    self.load_local_directory(self.current_path)
                except Exception as e:
                    QMessageBox.critical(self, "Rename Error", f"Could not rename item: {e}")

# Classe que gerencia as abas de confirmação de download
class ConfirmationTab(QWidget):
    def __init__(self, file_name, ftp_client, parent=None):
        super().__init__(parent)
        self.file_name = file_name
        self.ftp_client = ftp_client
        self.layout = QVBoxLayout()

        self.label = QLabel(f"Do you want to download the file: {file_name}?")
        self.layout.addWidget(self.label)

        self.confirmation_button = QPushButton("Download")
        self.layout.addWidget(self.confirmation_button)

        self.setLayout(self.layout)

    def close_tab(self):
        # Fecha a aba de confirmação após o download
        parent = self.parent().parent()
        index = parent.indexOf(self)
        parent.removeTab(index)

# Classe principal que gerencia a interface gráfica e a navegação entre abas
class FTPBrower(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FTP Browser")
        self.resize(800, 600)

        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        self.connection_tab = QWidget()
        self.connection_layout = QVBoxLayout()

        self.host_label = QLabel("FTP Host:")
        self.connection_layout.addWidget(self.host_label)
        self.host_input = QLineEdit()
        self.connection_layout.addWidget(self.host_input)

        self.user_label = QLabel("Username:")
        self.connection_layout.addWidget(self.user_label)
        self.user_input = QLineEdit()
        self.connection_layout.addWidget(self.user_input)

        self.passwd_label = QLabel("Password:")
        self.connection_layout.addWidget(self.passwd_label)
        self.passwd_input = QLineEdit()
        self.passwd_input.setEchoMode(QLineEdit.Password)
        self.connection_layout.addWidget(self.passwd_input)

        self.port_label = QLabel("Port:")
        self.connection_layout.addWidget(self.port_label)
        self.port_input = QLineEdit()
        self.port_input.setText("21")
        self.connection_layout.addWidget(self.port_input)

        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.connect_to_ftp)
        self.connection_layout.addWidget(self.connect_button)

        self.history_button = QPushButton("Show Connection History")
        self.history_button.clicked.connect(self.show_connection_history)
        self.connection_layout.addWidget(self.history_button)

        self.connection_tab.setLayout(self.connection_layout)
        self.tab_widget.addTab(self.connection_tab, "Connect to FTP")

        # Adicionando o explorador de arquivos locais encapsulado no QDockWidget à direita
        self.local_file_browser = QDockWidget("Local File Explorer", self)
        self.local_file_browser.setWidget(LocalFileBrowser(self))
        self.addDockWidget(Qt.RightDockWidgetArea, self.local_file_browser)

    def add_new_tab(self, ftp_host, ftp_user, ftp_passwd, ftp_port):
        # Adiciona uma nova aba para o cliente FTP
        new_tab = FTPClient(self, ftp_host, ftp_user, ftp_passwd, ftp_port)
        new_tab.load_ftp_directory()
        self.tab_widget.addTab(new_tab, f"{ftp_host}:{ftp_port}")
        self.tab_widget.setCurrentWidget(new_tab)

    def add_confirmation_tab(self, file_name, ftp_client):
        # Adiciona uma aba de confirmação para download
        new_tab = ConfirmationTab(file_name, ftp_client, self)
        self.tab_widget.addTab(new_tab, f"Download {file_name}")
        self.tab_widget.setCurrentWidget(new_tab)
        return new_tab

    def connect_to_ftp(self):
        # Estabelece a conexão FTP com os dados fornecidos pelo usuário
        ftp_host = self.host_input.text()
        ftp_user = self.user_input.text()
        ftp_passwd = self.passwd_input.text()
        ftp_port = int(self.port_input.text())
        self.add_new_tab(ftp_host, ftp_user, ftp_passwd, ftp_port)
        self.record_connection_history(ftp_host, ftp_user, ftp_port)

    def record_connection_history(self, ftp_host, ftp_user, ftp_port):
        # Registra o histórico de conexões
        with open("connection_history.txt", "a") as f:
            f.write(f"{ftp_host},{ftp_user},{ftp_port}\n")

    def show_connection_history(self):
        # Exibe o histórico de conexões para seleção
        history_manager = ConnectionHistoryManager(self)
        history_manager.exec_()

# Classe para gerenciar o histórico de conexões
class ConnectionHistoryManager(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Connection History")
        self.layout = QVBoxLayout()

        self.history_list = QListWidget()
        self.layout.addWidget(self.history_list)

        self.select_button = QPushButton("Connect")
        self.select_button.clicked.connect(self.connect_selected)
        self.layout.addWidget(self.select_button)

        self.setLayout(self.layout)
        self.load_history()

    def load_history(self):
        # Carrega o histórico de conexões a partir de um arquivo
        try:
            with open("connection_history.txt", "r") as f:
                lines = f.readlines()
                for line in lines:
                    self.history_list.addItem(line.strip())
        except FileNotFoundError:
            pass

    def connect_selected(self):
        # Conecta à seleção do histórico
        selected_item = self.history_list.currentItem()
        if selected_item:
            connection_info = selected_item.text().split(",")
            ftp_host = connection_info[0]
            ftp_user = connection_info[1]
            ftp_port = int(connection_info[2])
            self.parent().add_new_tab(ftp_host, ftp_user, "", ftp_port)
            self.close()

# Função principal para iniciar a aplicação
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FTPBrower()
    window.show()
    sys.exit(app.exec_())
