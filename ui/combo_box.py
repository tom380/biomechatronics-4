from PyQt5.QtWidgets import QComboBox
from PyQt5.QtCore import pyqtSignal


class ComboBox(QComboBox):
    """Extend QComboBox widget to handle click event"""

    popupAboutToBeShown = pyqtSignal()

    def showPopup(self):
        """Fire event first, then call parent popup method"""
        self.popupAboutToBeShown.emit()
        super().showPopup()
