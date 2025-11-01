import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLineEdit, QListWidget
from database import init_db, add_record, get_records

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("My First Python App")
        self.setGeometry(300, 200, 300, 300)

        layout = QVBoxLayout()
        self.input = QLineEdit()
        self.button = QPushButton("Add Record")
        self.listbox = QListWidget()

        layout.addWidget(self.input)
        layout.addWidget(self.button)
        layout.addWidget(self.listbox)
        self.setLayout(layout)

        self.button.clicked.connect(self.on_add)
        self.load_records()

    def load_records(self):
        self.listbox.clear()
        for _id, name in get_records():
            self.listbox.addItem(f"{_id}: {name}")

    def on_add(self):
        name = self.input.text().strip()
        if not name:
            return
        add_record(name)
        self.input.clear()
        self.load_records()

# def main():
#     print("🔧 Initializing database...")
#     init_db()
#     print("✅ Database ready!")

# if __name__ == "__main__":
#     main()

if __name__ == "__main__":
    init_db()
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec())
