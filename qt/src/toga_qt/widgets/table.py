from PySide6.QtCore import QModelIndex
from PySide6.QtWidgets import QTableView
from travertino.size import at_least

from ..sources.table_source_model import TableSourceModel
from .base import Widget


class Table(Widget):
    def create(self):
        # Create the List widget
        self.native = QTableView()

        self.native_model = TableSourceModel(
            self.interface.data,
            self.interface.headings,
            self.interface.accessors,
            parent=self.native,
        )
        self.native.setModel(self.native_model)

        self.native.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        if self.interface.multiple_select:
            self.native.setSelectionMode(QTableView.SelectionMode.ExtendedSelection)
        else:
            self.native.setSelectionMode(QTableView.SelectionMode.SingleSelection)

        # Automatically resize headers.
        self.native.horizontalHeader().setStretchLastSection(True)

        self.native.selectionModel().selectionChanged.connect(self.qt_selection_changed)
        self.native.activated.connect(self.qt_activated)

        self.native.show()

    def qt_selection_changed(self, added, removed):
        self.interface.on_select()

    def qt_activated(self, index):
        if index.isValid():
            self.interface.on_activate(self.interface.data[index.row()])

    def change_source(self, source):
        self.native_model.set_source(source)

    # Listener Protocol implementation

    def insert(self, index, item):
        self.native_model.insert_item(index)

    def change(self, item):
        self.native_model.item_changed(item)

    def remove(self, index, item):
        self.native_model.remove_item(index)

    def clear(self):
        self.native_model.reset_source()

    def get_selection(self):
        indexes = self.native.selectedIndexes()
        if self.interface.multiple_select:
            return sorted({index.row() for index in indexes})
        else:
            return indexes[0].row() if len(indexes) == 0 else None

    def scroll_to_row(self, row):
        index = self.native.model().index(row, 0, QModelIndex())
        self.native.scrollTo(index)

    def rehint(self):
        self.interface.intrinsic.width = at_least(self.interface._MIN_WIDTH)
        self.interface.intrinsic.height = at_least(self.interface._MIN_HEIGHT)

    def insert_column(self, index, heading, accessor):
        self.native_model.beginInsertColumns(QModelIndex(), index, index)
        self.native_model.endInsertColumns()

    def remove_column(self, index):
        self.native_model.beginRemoveColumns(QModelIndex(), index, index)
        self.native_model.endRemoveColumns()
