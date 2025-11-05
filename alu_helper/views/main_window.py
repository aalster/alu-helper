import base64

from PyQt6.QtCore import QByteArray
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtWidgets import QTabWidget, QMainWindow, QSystemTrayIcon, QMenu, QApplication, QStyle

from alu_helper.app_context import APP_CONTEXT
from alu_helper.services.utils import get_resource_path
from alu_helper.views.cars_tab import CarsTab
from alu_helper.views.maps_tab import MapsTab
from alu_helper.views.races_tab import RacesTab
from alu_helper.views.tracks_tab import TracksTab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ALU Helper")
        self.setWindowIcon(QIcon(get_resource_path("logo.png")))
        self.setMinimumSize(500, 600)
        self.restore_window_state()

        self.races_tab = RacesTab()
        self.tracks_tab = TracksTab()
        self.maps_tab = MapsTab()
        self.cars_tab = CarsTab()

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        self.tabs.currentChanged.connect(self.tab_selected) # type: ignore
        self.tabs.addTab(self.races_tab, "Races")
        self.tabs.addTab(self.tracks_tab, "Tracks")
        self.tabs.addTab(self.maps_tab, "Maps")
        self.tabs.addTab(self.cars_tab, "Cars")

        self.tray_icon = QSystemTrayIcon(QIcon(get_resource_path("logo.png")), self)
        self.tray_icon.setVisible(True)


        show_action = QAction("Open", self)
        quit_action = QAction("Quit", self)

        show_action.triggered.connect(self.show_window)
        quit_action.triggered.connect(QApplication.quit)

        tray_menu = QMenu()
        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)

        self.tray_icon.activated.connect(self.on_tray_icon_activated)

    def tab_selected(self, idx):
        tab = self.tabs.widget(idx)
        if tab.refresh:
            tab.refresh()

    def closeEvent(self, event):
        self.save_window_state()
        event.ignore()
        self.hide()
        # self.tray_icon.showMessage(
        #     "ALU Helper minimized to tray",
        #     "",
        #     self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxInformation),
        #     2000
        # )

    def show_window(self):
        self.showNormal()
        self.activateWindow()

    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_window()

    def save_window_state(self):
        settings = APP_CONTEXT.settings.get()
        settings.window_geometry = base64.b64encode(self.saveGeometry().data()).decode()
        settings.window_state = base64.b64encode(self.saveState().data()).decode()
        APP_CONTEXT.settings.save(settings)

    def restore_window_state(self):
        settings = APP_CONTEXT.settings.get()
        if settings.window_geometry:
            self.restoreGeometry(QByteArray(base64.b64decode(settings.window_geometry)))
        if settings.window_state:
            self.restoreState(QByteArray(base64.b64decode(settings.window_state)))
