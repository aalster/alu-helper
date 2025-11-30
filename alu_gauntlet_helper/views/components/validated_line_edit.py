from PyQt6.QtCore import QRegularExpression
from PyQt6.QtGui import QRegularExpressionValidator
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QLabel


class ValidatedLineEdit(QWidget):
    def __init__(self, text: str = "", placeholder: str = "", regex: str | None = None):
        super().__init__()

        self.input = QLineEdit(text)
        self.input.setPlaceholderText(placeholder)
        if regex:
            self.input.setValidator(QRegularExpressionValidator(QRegularExpression(regex)))
        self.input.textChanged.connect(self.clear_error) # type: ignore

        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: red; font-size: 11px;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.input)
        # layout.addWidget(self.error_label)


    def get_input(self) -> QLineEdit:
        return self.input

    def text(self) -> str:
        return self.input.text().strip()

    def setFocus(self):
        self.input.setFocus()

    def set_text(self, text: str):
        self.input.setText(text)

    def set_error(self, message: str = ""):
        self.input.setStyleSheet("background-color: rgba(255, 0, 0, 0.1);")
        self.error_label.setText(message)

    def clear_error(self):
        self.input.setStyleSheet("")
        self.error_label.clear()
