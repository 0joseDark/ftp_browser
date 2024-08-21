import sys
import os
from ftplib import FTP
from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import (QApplication, QMainWindow, QToolBar, QAction, QLineEdit, QTabWidget, 
                             QVBoxLayout, QListWidget, QDialog, QPushButton, QFileDialog, 
                             QMessageBox)
from PyQt5.QtGui import QIcon

# Classe que gerencia a conexão FTP e a exibição do diretório atual
class FTPClient(QDialog):
    def __init__(self, parent=None, ftp_url="ftp://"):
        super().__init__(parent)
        self.ftp_url = ftp_url  # URL do servidor FTP
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
        url = QUrl(self.ftp_url)
        try:
            self.ftp.connect(url.host())  # Conecta ao servidor FTP
            self.ftp.login()  # Faz o login no servidor (modo anônimo por padrão)
            self.ftp.cwd(url.path() or "/")  # Navega até o diretório especificado
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
        self.tabs.tabBarDoubleClicked.connect(self.add_new_tab)  # Adiciona nova aba ao dar duplo clique na barra de abas
        self.tabs.currentChanged.connect(self.update_url)  # Atualiza a URL na barra de navegação quando a aba muda
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_current_tab)  # Fecha a aba quando solicitado

        self.setCentralWidget(self.tabs)

        # Barra de navegação
        self.navbar = QToolBar()
        self.addToolBar(self.navbar)

        # Campo de URL para o FTP
        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.connect_to_ftp)  # Conecta ao servidor FTP ao pressionar Enter
        self.navbar.addWidget(self.url_bar)

        # Botão de configuração (placeholder)
        settings_btn = QAction(QIcon('settings.png'), "Settings", self)
        settings_btn.triggered.connect(self.show_settings_manager)
        self.navbar.addAction(settings_btn)

        # Adicionar uma nova aba ao iniciar o navegador
        self.add_new_tab("ftp://example.com")

    def add_new_tab(self, ftp_url="ftp://"):
        # Adiciona uma nova aba ao navegador FTP
        browser = FTPClient(self, ftp_url)
        i = self.tabs.addTab(browser, ftp_url)
        self.tabs.setCurrentIndex(i)
        browser.load_ftp_directory()  # Carrega o diretório FTP

    def close_current_tab(self, i):
        # Fecha a aba atual se houver mais de uma aberta
        if self.tabs.count() > 1:
            self.tabs.removeTab(i)

    def update_url(self, i):
        # Atualiza a URL na barra de navegação
        ftp_client = self.tabs.currentWidget()
        self.url_bar.setText(ftp_client.ftp_url)

    def connect_to_ftp(self):
        # Conecta ao servidor FTP a partir da URL digitada
        ftp_url = self.url_bar.text()
        self.add_new_tab(ftp_url)

    def show_settings_manager(self):
        # Placeholder para gerenciador de configurações
        QMessageBox.information(self, "Settings", "Settings manager not implemented yet.")

# Executa o aplicativo
app = QApplication(sys.argv)
QApplication.setApplicationName("Python FTP Browser")
window = FTPBrowser()
window.show()
sys.exit(app.exec_())
