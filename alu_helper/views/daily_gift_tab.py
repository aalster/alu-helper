from datetime import datetime, timedelta

from PyQt6.QtCore import QTimer, QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QCheckBox, QFormLayout, QLabel

from alu_helper.app_context import APP_CONTEXT
from alu_helper.utils.utils import format_time_delta, get_resource_path


class DailyGiftTab(QWidget):
    def __init__(self, show_badge, clear_badge):
        super().__init__()
        self.show_badge = show_badge
        self.clear_badge = clear_badge

        self.enable_timer = QCheckBox("Enable Daily Gift timer")
        self.enable_timer.checkStateChanged.connect(self.refresh_show_notification) # type: ignore

        self.timer_label = QLabel()

        self.show_notification = QCheckBox("Show notification")

        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.on_save) # type: ignore

        self.form = QFormLayout()
        self.form.addWidget(self.enable_timer)
        self.form.addWidget(self.show_notification)
        self.form.addWidget(self.timer_label)

        self.bottom_layout = QHBoxLayout()
        self.bottom_layout.addStretch()
        self.bottom_layout.addWidget(self.save_button)

        layout = QVBoxLayout()
        layout.addLayout(self.form)
        layout.addLayout(self.bottom_layout)
        layout.addStretch()
        self.setLayout(layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_time) # type: ignore
        self.timer.start(60 * 1000 - 100)

        self.refresh()
        self.refresh_show_notification()
        self.refresh_time()

    def refresh(self):
        settings = APP_CONTEXT.settings.get()
        self.enable_timer.setChecked(settings.daily_gift_timer)
        self.show_notification.setChecked(settings.daily_gift_notification)
        self.refresh_time()

    def refresh_show_notification(self):
        self.show_notification.setEnabled(self.enable_timer.isChecked())

    def refresh_time(self):
        settings = APP_CONTEXT.settings.get()
        if not settings.next_daily_gift_time:
            self.timer_label.setText("Next daily gift at N/A")
            return

        diff = settings.next_daily_gift_time - datetime.now()
        if diff.total_seconds() < 0:
            self.timer_label.setText("Next daily gift is available now!")
            self.show_badge()
            return

        # self.timer_label.setText(f"Next daily gift at {settings.next_daily_gift_time.strftime("%d.%m.%Y %H:%M:%S")}")
        self.timer_label.setText(f"Next daily gift in {format_time_delta(diff)}")
        self.clear_badge()

    def on_shop_open(self):
        settings = APP_CONTEXT.settings.get()
        if settings.daily_gift_link:
            QDesktopServices.openUrl(QUrl(settings.daily_gift_link))
        if settings.next_daily_gift_time < datetime.now():
            settings.next_daily_gift_time = datetime.now() + timedelta(days=1)
            APP_CONTEXT.settings.save(settings)
            self.refresh()

    def on_save(self):
        settings = APP_CONTEXT.settings.get()
        settings.daily_gift_timer = self.enable_timer.isChecked()
        settings.daily_gift_notification = self.show_notification.isChecked()
        if settings.daily_gift_timer and (not settings.next_daily_gift_time or settings.next_daily_gift_time < datetime.now()):
            settings.next_daily_gift_time = datetime.now() + timedelta(days=1)
        if not settings.daily_gift_timer and settings.next_daily_gift_time:
            settings.next_daily_gift_time = None
        APP_CONTEXT.settings.save(settings)
        self.refresh()
        self.refresh_time()