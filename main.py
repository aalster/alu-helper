import sys

from PyQt6.QtWidgets import QApplication

from alu_helper.app_context import APP_CONTEXT
from alu_helper.services.initial_data import init_data
from alu_helper.utils.single_instance_lock import single_instance_lock
from alu_helper.views.main_window import MainWindow
from alu_helper.database import init_db


def main():
    window: MainWindow | None = None

    def show_window():
        if not window is None:
            window.show_window()

    lock = single_instance_lock(show_window)
    if not lock:
        print("Application already running.")
        sys.exit(0)


    init_db()

    settings = APP_CONTEXT.settings.get()
    if not settings.initial_data_loaded:
        init_data()
        settings.initial_data_loaded = True
        APP_CONTEXT.settings.save(settings)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    font = app.font()
    font.setPointSize(10)
    app.setFont(font)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()