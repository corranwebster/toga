from typing import Any

from PySide6.QtCore import QAbstractItemModel, QModelIndex, QPersistentModelIndex, Qt

from toga import Icon
from toga.sources import Node, TreeSource

INVALID_INDEX = QModelIndex()


class TreeSourceModel(QAbstractItemModel):
    source: TreeSource | None
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

    def insert_item(self, index: int, item: Node):
        if item._parent is None:
            model_index = INVALID_INDEX
        else:
            model_index = self._get_index(item._parent)
        self.beginInsertRows(model_index, index, index)
        # Nothing to do, insertion has already happened
        self.endInsertRows()

    def remove_item(self, index, item):
        if item._parent is None:
            model_index = INVALID_INDEX
        else:
            model_index = self._get_index(item._parent)
        self.beginRemoveRows(model_index, index, index)
        # Nothing to do, removal has already happened
        self.endRemoveRows()

    def item_changed(self, item):
        if self.source is None:
            return
        start_index = self._get_index(item)
        end_index = self.index(
            start_index.row(), len(self.headings) - 1, start_index.parent()
        )
        self.dataChanged.emit(start_index, end_index)

    def _get_index(self, node: Node | TreeSource, column: int = 0) -> QModelIndex:
        if self.source is None or isinstance(node, TreeSource):
            return INVALID_INDEX
        rows = []
        while node._parent is not None:
            rows.append(node._parent.index(node))
            node = node._parent
        index = self.index(self.source.index(node), column, INVALID_INDEX)
        while rows:
            index = self.index(rows.pop(), column, index)
        return index

    def _get_node(
        self, index: QModelIndex | QPersistentModelIndex
    ) -> TreeSource | Node | None:
        if self.source is None:
            return None
        # If we have a valid QModelIndex, the internalPointer is the node.
        # QPersistentModelIndex objects can't store the data, so we need to do a lookup.
        if isinstance(index, QModelIndex):
            if index.isValid():
                return index.internalPointer()
            else:
                return self.source
        else:
            # build list of row indexes in parents
            rows = []
            while not index.isValid():
                rows.append(index.row())
                index = index.parent()
            # climb down tree to find node we want
            node = self.source
            while rows:
                node = node[rows.pop()]
            return node

    def parent(self, index: QModelIndex) -> QModelIndex:
        if index.isValid():
            node = index.internalPointer()
            if node._parent is not None:
                parent = node._parent
                row = parent.index(node)
                return self.createIndex(row, 0, parent)

        return INVALID_INDEX

    def index(
        self,
        row: int,
        column: int,
        /,
        parent: QModelIndex | QPersistentModelIndex = INVALID_INDEX,
    ) -> QModelIndex:
        parent_node = self._get_node(parent)
        if parent_node is None or row >= len(parent_node):
            return INVALID_INDEX
        else:
            # We attach the node for the row to the index for speed.
            # The node must remain alive during the lifetime of the QModelIndex()
            node = parent_node[row]
            return self.createIndex(row, column, node)

    def rowCount(
        self,
        parent: QModelIndex | QPersistentModelIndex = INVALID_INDEX,
    ) -> int:
        parent_node = self._get_node(parent)
        if parent_node is None:
            return 0
        else:
            return len(parent_node)

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
        node = self._get_node(index)
        if node is None:
            return None

        accessor = self.accessors[index.column()]
        value = getattr(node, accessor, None)
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
