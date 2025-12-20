from typing import Any

from PySide6.QtCore import QAbstractTableModel, QModelIndex, QPersistentModelIndex, Qt

from toga import Icon
from toga.sources import ListSource

INVALID_INDEX = QModelIndex()


class TableSourceModel(QAbstractTableModel):
    source: ListSource | None
    headings: list[str]

    def __init__(self, source, headings, accessors, **kwargs):
        super().__init__(**kwargs)
        self.source = source
        self.headings = headings
        self.accessors = accessors

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
        self.dataChanged.emit(
            self.index(self.source.index(item), 0),
            self.index(self.source.index(item), len(self.headings)),
        )

    def rowCount(
        self,
        parent: QModelIndex | QPersistentModelIndex = INVALID_INDEX,
    ) -> int:
        if self.source is None:
            return 0
        return len(self.source)

    def columnCount(
        self,
        parent: QModelIndex | QPersistentModelIndex = INVALID_INDEX,
    ) -> int:
        if self.headings is None:
            return 0
        return len(self.headings)

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

        row = self.source[index.row()]
        accessor = self.accessors[index.column()]
        value = getattr(row, accessor, None)
        if role == Qt.ItemDataRole.DecorationRole:
            if isinstance(value, Icon):
                icon = value
            elif isinstance(value, tuple):
                icon = value[0]
            else:
                return None
            try:
                return icon._impl.native
            except Exception:
                return None
        elif role == Qt.ItemDataRole.DisplayRole:
            if isinstance(value, tuple):
                value = value[1]
            if value is not None:
                return str(value)
            else:
                return None
        return None

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        /,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if orientation == Qt.Orientation.Horizontal:
            if section >= len(self.headings):
                return None
            value = self.headings[section]
            if role == Qt.ItemDataRole.DisplayRole and value is not None:
                return str(value)

        return None
