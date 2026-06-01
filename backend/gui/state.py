from PyQt6.QtCore import QObject, pyqtSignal
from session import SessionState


class AppState(QObject):
    file_loaded = pyqtSignal()
    evaluated = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.session = SessionState()

    def reset(self):
        self.session = SessionState()


app_state = AppState()
