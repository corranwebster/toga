from PySide6.QtCore import QModelIndex
from PySide6.QtWidgets import QTreeView
from travertino.size import at_least

from ..sources.tree_source_model import TreeSourceModel
from .base import Widget


class Tree(Widget):
    def create(self):
        # Create the List widget
        self.native = QTreeView()

        self.native_model = TreeSourceModel(
            self.interface.data,
            self.interface.headings,
            self.interface.accessors,
            parent=self.native,
        )
        self.native.setModel(self.native_model)

        self.native.setSelectionBehavior(QTreeView.SelectionBehavior.SelectRows)
        if self.interface.multiple_select:
            self.native.setSelectionMode(QTreeView.SelectionMode.ExtendedSelection)
        else:
            self.native.setSelectionMode(QTreeView.SelectionMode.SingleSelection)

        # Automatically resize headers.
        self.native.header().setStretchLastSection(True)

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

    def insert(self, parent, index, item):
        self.native_model.insert_item(index, item)

    def change(self, item):
        self.native_model.item_changed(item)

    def remove(self, index, item):
        self.native_model.remove_item(item, index)

    def clear(self):
        self.native_model.reset_source()

    def get_selection(self):
        indexes = sorted(
            {
                (index.row(), index.internalPointer())
                for index in self.native.selectedIndexes()
            }
        )
        if self.interface.multiple_select:
            return [node for row, node in indexes]
        else:
            return indexes[0][1] if len(indexes) != 0 else None

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
