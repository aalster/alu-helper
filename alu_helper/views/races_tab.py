# gui/maps_tab.py
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QIntValidator
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QListWidget, QLineEdit, QListWidgetItem, QHBoxLayout, \
    QLabel, QCompleter

from alu_helper.app_context import APP_CONTEXT
from alu_helper.services.races import RaceView
from alu_helper.services.tracks import TrackView
from alu_helper.views.components import EditDialog, ValidatedLineEdit, ItemCompleter


class RaceDialog(EditDialog):
    def __init__(self, item: RaceView, action, parent=None):
        self.item = item

        self.track_edit = ValidatedLineEdit(item.track_name)
        self.car_edit = ValidatedLineEdit(item.car_name)
        self.rank_edit = ValidatedLineEdit(str(item.rank) if item.rank else "")
        self.rank_edit.get_input().setValidator(QIntValidator(0, 10000))

        self.tracks_completer = ItemCompleter(
            self.track_edit.get_input(),
            APP_CONTEXT.tracks_service.autocomplete,
            lambda i: f"{i.map_name} - {i.name}",
            False
        )
        self.tracks_completer.set_selected_item(TrackView(id=item.track_id, name=item.track_name, map_name=item.map_name))

        self.cars_completer = ItemCompleter(
            self.car_edit.get_input(),
            APP_CONTEXT.cars_service.autocomplete,
            lambda i: i.name,
            self.on_car_selected
        )

        super().__init__(action, parent)
        self.setWindowTitle("Edit Track" if item.id else "Add Track")

    def prepare_layout(self):
        form_layout = QVBoxLayout()
        form_layout.addWidget(QLabel("Track:"))
        form_layout.addWidget(self.track_edit)
        form_layout.addWidget(QLabel("Car:"))
        form_layout.addWidget(self.car_edit)
        form_layout.addWidget(QLabel("Rank:"))
        form_layout.addWidget(self.rank_edit)

        return form_layout

    def on_car_selected(self, car):
        self.rank_edit.set_text(str(car.rank) if car and car.rank >= 0 else "")

    def prepare_item(self):
        track_id = self.tracks_completer.get_selected_item().id if self.tracks_completer.get_selected_item() else 0
        car_id = self.cars_completer.get_selected_item().id if self.cars_completer.get_selected_item() else 0
        car_name = self.car_edit.text()
        rank = int(self.rank_edit.text()) if self.rank_edit.text() else 0

        error = False
        if track_id <= 0:
            self.track_edit.set_error()
            error = True

        if not car_name:
            self.car_edit.set_error()
            error = True

        if error:
            return None

        return RaceView(id=self.item.id, track_id=track_id, car_id=car_id, car_name=car_name, rank=rank)


class RacesTab(QWidget):
    def __init__(self):
        super().__init__()

        self.query = QLineEdit()
        self.query.setClearButtonEnabled(True)
        self.query.setPlaceholderText("Filter by name")
        self.query.textEdited.connect(self.refresh_debounce) # type: ignore

        self.add_button = QPushButton("Add")
        self.add_button.clicked.connect(self.on_add) # type: ignore

        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self.on_edit) # type: ignore

        self.debounce_timer = QTimer()
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.timeout.connect(self.refresh) # type: ignore

        top_layout = QHBoxLayout()
        top_layout.addWidget(self.query)
        top_layout.addWidget(self.add_button)

        layout = QVBoxLayout()
        layout.addLayout(top_layout)
        layout.addWidget(self.list_widget)
        self.setLayout(layout)
        self.refresh()

    def refresh_debounce(self):
        self.debounce_timer.start(300)

    def refresh(self):
        self.list_widget.clear()
        for i in APP_CONTEXT.races_service.get_all():
            item = QListWidgetItem(f"{i.id}: {i.map_name} {i.track_name} - {i.car_name}")
            item.setData(Qt.ItemDataRole.UserRole, i)
            self.list_widget.addItem(item)

    def on_add(self):
        if RaceDialog(item=RaceView(), action=APP_CONTEXT.races_service.save).exec():
            self.refresh()

    def on_edit(self, item: QListWidgetItem):
        if RaceDialog(item=item.data(Qt.ItemDataRole.UserRole), action=APP_CONTEXT.races_service.save).exec():
            self.refresh()
