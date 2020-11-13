import sys
from PyQt5.QtWidgets import QApplication

from ui.main_window import MainWindow


# Run window when file was called as executable
if __name__ == '__main__':

    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    window = MainWindow()

    sys.exit(app.exec())
