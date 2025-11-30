from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtWidgets import QLineEdit, QCompleter


class ItemCompleter(QCompleter):
    selected_item = None

    def __init__(self, input_: QLineEdit, autocomplete, presentation, allow_custom_text=True, selected_listener=None, parent=None):
        super().__init__(parent)
        self.input_ = input_
        self.autocomplete = autocomplete
        self.presentation = presentation
        self.selected_listener = selected_listener

        self._model = QStandardItemModel(self)
        self.setModel(self._model)
        self.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.setFilterMode(Qt.MatchFlag.MatchContains)
        self.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.activated.connect(self.on_completer_activated) # type: ignore
        self.highlighted.connect(self.on_completer_activated) # type: ignore

        self.debounce_timer = QTimer(self)
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.timeout.connect(self.update_completer) # type: ignore

        self.input_.textEdited.connect(self.on_text_changed)
        if not allow_custom_text:
            self.input_.editingFinished.connect(self.on_editing_finished)
        self.input_.setCompleter(self)

        # self.input_watcher = FocusWatcher(on_focus_in=self.update_completer)
        # self.input_.installEventFilter(self.input_watcher)

    def set_selected_item(self, item):
        self.selected_item = item

    def get_selected_item(self):
        return self.selected_item

    def on_editing_finished(self):
        if not self.selected_item:
            self.input_.clear()

    def on_text_changed(self, _):
        self.selected_item = None
        if self.selected_listener:
            self.selected_listener(None)
        self.debounce_timer.start(300)

    def on_completer_activated(self, text):
        self.input_.setText(text)
        self.debounce_timer.stop()

        index = self.popup().currentIndex()
        if index.isValid():
            self.selected_item = index.data(Qt.ItemDataRole.UserRole)
            if self.selected_listener:
                self.selected_listener(self.selected_item)

    def update_completer(self):
        try:
            query = self.input_.text().strip()
        except RuntimeError:
            return

        items = self.autocomplete(query)

        self._model.clear()
        for i in items:
            item = QStandardItem(self.presentation(i))
            item.setData(i, Qt.ItemDataRole.UserRole)
            self._model.appendRow(item)

        if items:
            self.complete()
        else:
            self.popup().hide()
