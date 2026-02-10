from __future__ import annotations

from contextlib import contextmanager
from typing import Generic, Protocol, TypeVar, runtime_checkable

ListenerT = TypeVar("ListenerT")
ItemT = TypeVar("ItemT", contravariant=True)


@runtime_checkable
class ValueListener(Protocol, Generic[ItemT]):
    """The protocol that must be implemented by objects that will act as a listener on a
    value data source.
    """

    def change(self, *, item: ItemT) -> None:
        """A change has occurred in an item.

        :param item: The data object that has changed.
        """


@runtime_checkable
class ListListener(ValueListener[ItemT], Protocol, Generic[ItemT]):
    """The protocol that must be implemented by objects that will act as a listener on a
    list data source.
    """

    def pre_insert(self, *, index: int, item: ItemT) -> None:
        """An item is about to be added to the data source.

        :param index: The 0-index position in the data.
        :param item: The data object that was added.
        """

    def post_insert(self, *, index: int, item: ItemT) -> None:
        """An item has been added to the data source.

        :param index: The 0-index position in the data.
        :param item: The data object that was added.
        """

    def pre_remove(self, *, index: int, item: ItemT) -> None:
        """An item is about to be removed from the data source.

        :param index: The 0-index position in the data.
        :param item: The data object that was added.
        """

    def post_remove(self, *, index: int, item: ItemT) -> None:
        """An item has been removed from the data source.

        :param index: The 0-index position in the data.
        :param item: The data object that was added.
        """

    def clear(self) -> None:
        """All items have been removed from the data source."""


@runtime_checkable
class TreeListener(ListListener[ItemT], Protocol, Generic[ItemT]):
    """The protocol that must be implemented by objects that will act as a listener on a
    tree data source.
    """

    def pre_insert(
        self, *, index: int, item: object, parent: ItemT | None = None
    ) -> None:
        """An item is about to be added to the data source.

        :param index: The 0-index position in the data.
        :param item: The data object that was added.
        :param parent: The parent of the data object that was added, or `None`
            if it is a root item.
        """

    def post_insert(
        self, *, index: int, item: object, parent: ItemT | None = None
    ) -> None:
        """An item has been added to the data source.

        :param index: The 0-index position in the data.
        :param item: The data object that was added.
        :param parent: The parent of the data object that was added, or `None`
            if it is a root item.
        """

    def pre_remove(
        self, *, index: int, item: object, parent: ItemT | None = None
    ) -> None:
        """An item is about to be removed from the data source.

        :param index: The 0-index position in the data.
        :param item: The data object that was added.
        :param parent: The parent of the data object that was removed, or `None`
            if it is a root item.
        """

    def post_remove(
        self, *, index: int, item: object, parent: ItemT | None = None
    ) -> None:
        """An item has been removed from the data source.

        :param index: The 0-index position in the data.
        :param item: The data object that was added.
        :param parent: The parent of the data object that was removed, or `None`
            if it is a root item.
        """


class Source(Generic[ListenerT]):
    """A base class for data sources, providing an implementation of data
    notifications."""

    def __init__(self) -> None:
        self._listeners: list[ListenerT] = []

    @property
    def listeners(self) -> list[ListenerT]:
        """The listeners of this data source.

        :returns: A list of objects that are listening to this data source.
        """
        return self._listeners

    def add_listener(self, listener: ListenerT) -> None:
        """Add a new listener to this data source.

        If the listener is already registered on this data source, the request to add is
        ignored.

        :param listener: The listener to add
        """
        if listener not in self._listeners:
            self._listeners.append(listener)

    def remove_listener(self, listener: ListenerT) -> None:
        """Remove a listener from this data source.

        :param listener: The listener to remove.
        """
        self._listeners.remove(listener)

    @contextmanager
    def pre_notify(self, notification, **kwargs: object):
        """Context manager that sends a two-part notification.

        This context manager sends a notification with prefix
        "pre_" and the notification name when it enters the
        context manager, and then sends the actual notification
        when it is finished.

        This permits listeners to do any book-keeping they might
        need to do before the actual change occurs.

        :param notification: The notification to emit.
        :param kwargs: The data associated with the notification.
        """
        self.notify(f"pre_{notification}", **kwargs)
        try:
            yield
        finally:
            self.notify(f"post_{notification}", **kwargs)

    def notify(self, notification: str, **kwargs: object) -> None:
        """Notify all listeners an event has occurred.

        :param notification: The notification to emit.
        :param kwargs: The data associated with the notification.
        """
        for listener in self._listeners:
            if (method := getattr(listener, notification, None)) is not None:
                method(**kwargs)
            elif notification in {"post_insert", "post_remove"}:
                # Handle backwards compatibility for listener:
                # Feb 2026: In 0.5.3 and earlier, post_insert and post_remove
                # were insert and remove

                # try notification without the "post_"
                notification = notification[5:]
                if (method := getattr(listener, notification, None)) is not None:
                    import warnings

                    warnings.warn(
                        f"Listener {listener!r} does not have 'post_{notification}' "
                        f"method, using '{notification}' method instead. "
                        f"Update the listener to use the 'post_{notification}' "
                        "method.",
                        DeprecationWarning,
                        stacklevel=2,
                    )
                    method(**kwargs)
            elif notification in {"insert", "remove"}:
                # Handle backwards compatibility for source:
                # Feb 2026: In 0.5.3 and earlier, post_insert and post_remove
                # were insert and remove

                # try notification with "post_"
                if (
                    method := getattr(listener, f"post_{notification}", None)
                ) is not None:
                    import warnings

                    warnings.warn(
                        f"Listener does not have '{notification}' method, "
                        f"using 'post_{notification}' method instead. "
                        f"Update {self!r} to generate 'post_{notification}' "
                        "notifications.",
                        DeprecationWarning,
                        stacklevel=2,
                    )
                    method(**kwargs)


def __getattr__(name):
    if name == "Listener":
        import warnings

        # Alias for backwards compatibility:
        # Jan 2026: In 0.5.3 and earlier, ListListener was named Listener
        global Listener
        Listener = ListListener
        warnings.warn(
            "The Listener protocol has been deprecated; "
            "use ListListener or TreeListener instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return Listener
    else:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'") from None
