import logging
import warnings
from typing import Any, overload

from PySide6.QtCore import (
    QAbstractItemModel,
    QModelIndex,
    QObject,
    QPersistentModelIndex,
    Qt,
)
from PySide6.QtWidgets import QHeaderView, QTreeView
from travertino.size import at_least

from toga.sources import ListSource

from .base import Widget

logger = logging.getLogger(__name__)

# convenience root/invalid index object
INVALID_INDEX = QModelIndex()


class TreeSourceModel(QAbstractItemModel):
    def __init__(self, source, columns, missing_value, **kwargs):
        super().__init__(**kwargs)
        self._source = source
        self._columns = columns
        self._missing_value = missing_value

    def set_source(self, source):
        self.beginResetModel()
        self._source = source
        self.endResetModel()

    def reset_source(self):
        self.beginResetModel()
        # Nothing to do, clear has already happened
        self.endResetModel()

    def pre_insert_item(self, index, item, parent=None):
        pass

    def insert_item(self, index, item, parent=None):
        qt_index = self._get_index(parent)
        self.beginInsertRows(qt_index, index, index)
        self.endInsertRows()

    def pre_remove_item(self, index, item, parent=None):
        qt_parent = self._get_index(parent)
        self.beginRemoveRows(qt_parent, index, index)

    def remove_item(self, index, item, parent=None):
        self.endRemoveRows()

    def item_changed(self, item):
        if self._source is None:
            # The source can briefly be None during widget creation
            return  # pragma: no cover
        start_index = self._get_index(item)
        end_index = self.index(
            start_index.row(), len(self._columns) - 1, start_index.parent()
        )
        self.dataChanged.emit(start_index, end_index)

    def _get_rows_from_source(self, node):
        rows = []
        while node._parent is not None:
            rows.append(node._parent.index(node))
            node = node._parent
        rows.append(self._source.index(node))
        return rows

    def _get_rows_from_index(self, index: QModelIndex | QPersistentModelIndex):
        rows = []
        while index.isValid():
            rows.append(index.row())
            index = index.parent()
        return rows

    def _get_index(self, node, column=0) -> QModelIndex:
        if self._source is None or not hasattr(node, "_parent"):
            # The source can briefly be None during widget creation
            # and bad user implementations of nodes could lead here.
            return INVALID_INDEX  # pragma: no cover
        rows = self._get_rows_from_source(node)
        index = INVALID_INDEX
        while rows:
            index = self.index(rows.pop(), column, index)
        return index

    def _get_node(self, index: QModelIndex | QPersistentModelIndex):
        if self._source is None:
            # The source can briefly be None during widget creation
            return None  # pragma: no cover
        # If we have a valid QModelIndex, the internalPointer is the node.
        # QPersistentModelIndex objects can't store the data, so we need to do a lookup.
        # The tests don't create persistent model indices, but should handle case anyway
        # to future-proof for things like drag-and-drop support.
        if isinstance(index, QModelIndex):
            if index.isValid():
                parent = index.internalPointer()
            else:
                return self._source
            if len(parent) < index.row():
                # This should never happen in regular operation
                return None  # pragma: no cover
            else:
                return parent[index.row()]
        else:  # pragma: no cover
            # build list of row indexes in parents
            rows = self._get_rows_from_index(index)
            # climb down tree to find node we want
            node = self._source
            while rows:
                node = node[rows.pop()]
            return node

    @overload
    def parent(self) -> QObject: ...
    @overload
    def parent(self, index: QModelIndex | QPersistentModelIndex) -> QModelIndex: ...

    def parent(self, index=None):
        # handle QObject.parent(), not tested
        if index is None:
            return super().parent()  # pragma: no cover

        # index should always be valid, but check anyway
        if index.isValid():
            return INVALID_INDEX  # pragma: no cover

        parent_node = index.internalPointer()
        if parent_node is self._source:
            return INVALID_INDEX
        elif parent_node._parent is not None:
            grandparent = parent_node._parent
        else:
            grandparent = self._source

        row = grandparent.index(parent_node)
        return self.createIndex(row, 0, grandparent)

    def index(
        self,
        row: int,
        column: int,
        /,
        parent: QModelIndex | QPersistentModelIndex = INVALID_INDEX,
    ) -> QModelIndex:
        parent_node = self._get_node(parent)
        if parent_node is None:
            # this shouldn't happen in normal operation
            return INVALID_INDEX  # pragma: no cover
        else:
            # We attach the node for the parent to the index for speed.
            # The parent node must remain alive during the lifetime of the
            # QModelIndex()
            return self.createIndex(row, column, parent_node)

    def rowCount(
        self,
        parent: QModelIndex | QPersistentModelIndex = INVALID_INDEX,
    ) -> int:
        # this could call out to end-user data sources, so could fail.
        try:
            parent_node = self._get_node(parent)
            if parent_node is None:
                # this shouldn't happen in normal operation
                return 0  # pragma: no cover
            else:
                return len(parent_node)
        except Exception:  # pragma: no cover
            logger.exception("Could not get data length.")
        return 0  # pragma: no cover

    def columnCount(
        self,
        parent: QModelIndex | QPersistentModelIndex = INVALID_INDEX,
    ) -> int:
        # this could call out to end-user data sources, so could fail.
        try:
            if self._columns is not None:
                return len(self._columns)
        except Exception:  # pragma: no cover
            logger.exception("Could not get number of columns.")
        return 0  # pragma: no cover

    def data(
        self,
        index: QModelIndex | QPersistentModelIndex,
        /,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        # Return empty data if index is invalid, shouldn't happen in normal operation
        # but checking prevents crashes
        if index.isValid():  # pragma: no branch
            node = self._get_node(index)
            column_index = index.column()
            # this could call out to end-user data sources, so could fail.
            try:
                if self._source is None:
                    # this can happen briefly during initialization
                    return None  # pragma: no cover

                columns = self._columns
                if column_index >= len(columns):
                    # This should not happen in normal operation, but could occur
                    # if data changed and notification hasn't been sent
                    return None  # pragma: no cover

                column = columns[column_index]
                if column.widget(node) is not None:
                    warnings.warn(
                        "Qt does not support the use of widgets in cells",
                        stacklevel=2,
                    )

                # currently only handle icons and text
                if role == Qt.ItemDataRole.DecorationRole:
                    icon = column.icon(node)
                    if icon is not None:
                        return icon._impl.native
                elif role == Qt.ItemDataRole.DisplayRole:
                    return column.text(node, self._missing_value)
            except Exception:  # pragma: no cover
                logger.exception(
                    f"Could not get data for node {node}, column {column_index}"
                )
        return None

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        /,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        # QTreeViews only have horizontal headers, but check anyway
        if orientation == Qt.Orientation.Horizontal:  # pragma: no branch
            columns = self._columns
            # this could call out to end-user data sources, so could fail.
            try:
                if section < len(columns):  # pragma: no branch
                    if role == Qt.ItemDataRole.DisplayRole:
                        return columns[section].heading
            except Exception:  # pragma: no cover
                logger.exception(f"Could not header for column {section}.")

        return None


class Tree(Widget):
    def create(self):
        # Create the List widget
        self.native = QTreeView()

        self.native_model = TreeSourceModel(
            getattr(self.interface, "_data", ListSource(self.interface.accessors)),
            self.interface._columns[:],
            self.interface.missing_value,
            parent=self.native,
        )
        self.native.setModel(self.native_model)

        self.native.setSelectionBehavior(QTreeView.SelectionBehavior.SelectRows)
        if self.interface.multiple_select:
            self.native.setSelectionMode(QTreeView.SelectionMode.ExtendedSelection)
        else:
            self.native.setSelectionMode(QTreeView.SelectionMode.SingleSelection)

        if not self.interface._show_headings:
            # Hide the header
            self.native.header().hide()

        self.native.header().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.native.selectionModel().selectionChanged.connect(self.qt_selection_changed)
        self.native.activated.connect(self.qt_activated)

    def qt_selection_changed(self, added, removed):
        self.interface.on_select()

    def qt_activated(self, index):
        # Invalid index shouldn't occur in normal operation.
        if index.isValid():  # pragma: no branch
            self.interface.on_activate(node=self.native_model._get_node(index))

    def change_source(self, source):
        self.native_model.set_source(source)
        self.native.header().resizeSections(QHeaderView.ResizeMode.Stretch)

    # Listener Protocol implementation

    def pre_insert(self, index, item, parent=None):
        self.native_model.pre_insert_item(item=item, index=index, parent=parent)

    def insert(self, index, item, parent=None):
        self.native_model.insert_item(item=item, index=index, parent=parent)

    def change(self, item):
        self.native_model.item_changed(item)

    def pre_remove(self, index, item, parent=None):
        self.native_model.pre_remove_item(item=item, index=index, parent=parent)

    def remove(self, index, item, parent=None):
        self.native_model.remove_item(item=item, index=index, parent=parent)

    def clear(self):
        self.native_model.reset_source()

    def get_selection(self):
        # Deduplicate selection using row tuples and nodes.
        indexes = sorted(
            {
                (
                    tuple(reversed(self.native_model._get_rows_from_index(index))),
                    self.native_model._get_node(index),
                )
                for index in self.native.selectedIndexes()
            }
        )
        if self.interface.multiple_select:
            return [node for row, node in indexes]
        else:
            return indexes[0][1] if len(indexes) != 0 else None

    def expand_node(self, item):
        index = self.native_model._get_index(item)
        self.native.expandRecursively(index)

    def expand_all(self):
        self.native.expandAll()

    def collapse_node(self, item):
        index = self.native_model._get_index(item)
        self.native.collapse(index)

    def collapse_all(self):
        self.native.collapseAll()

    def rehint(self):
        self.interface.intrinsic.width = at_least(self.interface._MIN_WIDTH)
        self.interface.intrinsic.height = at_least(self.interface._MIN_HEIGHT)
        self.native.header().resizeSections(QHeaderView.ResizeMode.Stretch)

    def insert_column(self, index, heading, accessor):
        self.native_model.beginInsertColumns(QModelIndex(), index, index)
        self.native_model._columns.insert(index, self.interface._columns[index])
        self.native_model.endInsertColumns()
        self.native.header().resizeSections(QHeaderView.ResizeMode.Stretch)

    def remove_column(self, index):
        self.native_model.beginRemoveColumns(QModelIndex(), index, index)
        del self.native_model._columns[index]
        self.native_model.endRemoveColumns()
        self.native.header().resizeSections(QHeaderView.ResizeMode.Stretch)
