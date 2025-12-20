from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QAbstractListModel, QModelIndex, QPersistentModelIndex, Qt

from toga.sources import ListSource

INVALID_INDEX = QModelIndex()


class ListSourceModel(QAbstractListModel):
    source: ListSource | None
    formatters: dict[int, Callable[[object, list[str]], object]]

    def __init__(self, source, formatters, **kwargs):
        super().__init__(**kwargs)
        self.source = source
        self.formatters = formatters

    def set_source(self, source):
        self.beginResetModel()
        self.source = source
        self.endResetModel()

    def reset_source(self):
        self.beginResetModel()
        # Nothing to do, clear has already happened
        self.endResetModel()

    def insert_item(self, index):
        self.beginInsertRows(QModelIndex(), index, index)
        # Nothing to do, insertion has already happened
        self.endInsertRows()

    def remove_item(self, index):
        self.beginRemoveRows(QModelIndex(), index, index)
        # Nothing to do, removal has already happened
        self.endRemoveRows()

    def item_changed(self, item):
        if self.source is None:
            return
        self.dataChanged.emit(self.index(self.source.index(item)))
        # Nothing to do, removal has already happened
        self.endInsertRows()

    def rowCount(
        self, parent: QModelIndex | QPersistentModelIndex = INVALID_INDEX
    ) -> int:
        if self.source is None:
            return 0
        return len(self.source)

    def data(
        self,
        index: QModelIndex | QPersistentModelIndex,
        /,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if not index.isValid():
            return None
        if self.source is None:
            return None
        if index.row() >= len(self.source):
            return None

        value = self.source[index.row()]
        if role in self.formatters:
            result = self.formatters[role](value, self.source._accessors)
            return result
        else:
            return None

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        /,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        return None
