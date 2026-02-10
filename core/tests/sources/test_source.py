from unittest.mock import Mock

import pytest

from toga.sources import Source


def test_notify():
    source = Source()

    # No listeners
    assert source.listeners == []
    source.notify("message0")

    listener1 = Mock()

    source.add_listener(listener1)
    assert source.listeners == [listener1]

    # Add the same listener a second time
    source.add_listener(listener1)
    assert source.listeners == [listener1]

    # activate listener
    source.notify("message1")
    listener1.message1.assert_called_once_with()

    # activate listener with data
    source.notify("message2", arg1=11, arg2=22)
    listener1.message2.assert_called_once_with(arg1=11, arg2=22)

    # add more widgets to listeners
    listener2 = Mock()
    source.add_listener(listener2)
    assert source.listeners == [listener1, listener2]

    # activate listener
    source.notify("message3")
    listener1.message3.assert_called_once_with()
    listener2.message3.assert_called_once_with()

    # activate listener with data
    source.notify("message4", arg1=11, arg2=22)
    listener1.message4.assert_called_once_with(arg1=11, arg2=22)
    listener2.message4.assert_called_once_with(arg1=11, arg2=22)

    # remove listener2
    source.remove_listener(listener2)
    assert source.listeners == [listener1]

    # Activate listeners; listener2 not notified.
    source.notify("message5")
    listener1.message5.assert_called_once_with()
    listener2.message5.assert_not_called()


def test_pre_notify():
    source = Source()
    listener1 = Mock()
    source.add_listener(listener1)

    with source.pre_notify("message", arg1=1, arg2=2):
        # Pre message called
        listener1.pre_message.assert_called_once_with(arg1=1, arg2=2)

    # Post message called
    listener1.post_message.assert_called_once_with(arg1=1, arg2=2)


def test_missing_listener_method():
    """If a listener doesn't implement a notification method, the notification is
    ignored."""
    full_listener = Mock()
    partial_listener = object()
    source = Source()

    source.add_listener(full_listener)
    source.add_listener(partial_listener)
    assert source.listeners == [full_listener, partial_listener]

    # This shouldn't raise an error
    source.notify("message1")

    full_listener.message1.assert_called_once_with()


def test_deprecate_insert():
    class Listener:
        pass

    source = Source()
    listener = Listener()
    listener.post_insert = Mock()

    source.add_listener(listener)

    # Warn about the notification
    with pytest.warns(
        DeprecationWarning, match=r"Listener does not have 'insert' method,"
    ):
        source.notify("insert", arg1=1, arg2=2)

    # post_insert should be called
    listener.post_insert.assert_called_once_with(arg1=1, arg2=2)

    del listener.post_insert
    listener.insert = Mock()

    # Warn about the notification
    with pytest.warns(
        DeprecationWarning, match=r"Listener .* does not have 'post_insert' method,"
    ):
        source.notify("post_insert", arg1=1, arg2=2)

    # insert should be called
    listener.insert.assert_called_once_with(arg1=1, arg2=2)

    del listener.insert

    # if neither, no warning, no calls
    source.notify("insert", arg1=1, arg2=2)
    source.notify("post_insert", arg1=1, arg2=2)


def test_deprecate_remove():
    class Listener:
        pass

    source = Source()
    listener = Listener()
    listener.post_remove = Mock()

    source.add_listener(listener)

    # Warn about the notification
    with pytest.warns(
        DeprecationWarning, match=r"Listener does not have 'remove' method,"
    ):
        source.notify("remove", arg1=1, arg2=2)

    # post_remove should be called
    listener.post_remove.assert_called_once_with(arg1=1, arg2=2)

    del listener.post_remove
    listener.remove = Mock()

    # Warn about the notification
    with pytest.warns(
        DeprecationWarning, match=r"Listener .* does not have 'post_remove' method,"
    ):
        source.notify("post_remove", arg1=1, arg2=2)

    # remove should be called
    listener.remove.assert_called_once_with(arg1=1, arg2=2)

    del listener.remove

    # if neither, no warning, no calls
    source.notify("remove", arg1=1, arg2=2)
    source.notify("post_remove", arg1=1, arg2=2)


def test_deprecate_listener():
    import toga.sources.base

    # Import Listener from toga.sources.base. Raises a deprecation warning.
    with pytest.warns(
        DeprecationWarning,
        match=r"The Listener protocol has been deprecated;",
    ):
        from toga.sources.base import Listener

    assert Listener is toga.sources.base.ListListener

    with pytest.raises(
        ImportError,
        match=r"cannot import name 'NonExistent' from 'toga.sources.base'",
    ):
        from toga.sources.base import NonExistent  # noqa: F401

    # "unimport" Listener
    del toga.sources.base.Listener

    # Import Listener from toga.sources.base. Raises a deprecation warning.
    with pytest.warns(
        DeprecationWarning,
        match=r"The Listener protocol has been deprecated;",
    ):
        from toga.sources import Listener

    assert Listener is toga.sources.base.ListListener

    with pytest.raises(
        ImportError,
        match=r"cannot import name 'NonExistent' from 'toga.sources'",
    ):
        from toga.sources import NonExistent  # noqa: F401
