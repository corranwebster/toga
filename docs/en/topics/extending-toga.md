# Extending Toga

While Toga provides a rich set of features, because it is a cross-platform library it provides it necessarily can't provide every widget that is available on every platform.  Additionally, because widgets are implemented as time permits by contributors some backends may lack versions of some widgets that others have from time-to-time.  This means that application authors may find themselves in a situation where they need to write a custom widget.  This topic guide explains how Toga finds widget implementations, and how people can expand the available widgets for their application.

## Writing a Widget

As noted in the [Internal architecture](architecture.md) topic guide, a widget is made up of three layers: interface, implementation, and native.  Every interface widget has a `_create` method that is responsible for creating the implementation of the widget.  The implementation should be passed the interface object to its `__init__` method. The implementation in turn has its own `create` method that should create any native widgets or other state that is needed.  So if you are creating a widget for your own application where you only care about one backend, you can have the `create` directly import the implementation class and instantiate it.

### Example: A Qt Dial

As an example, the Qt library has a `QDial` class that acts a lot like a [`Slider`][toga.Slider] but displays a round dial instead of a linear slider.  We can write a subclass of [`Slider`][toga.Slider] that will use a `QDial` as follows.

In `dial.py` we create a subclass of [`Slider`][toga.Slider]
``` python
from toga import Slider

class Dial(Slider):
    """The Dial interface."""

    def _create(self):
        from .qt_dial import Dial
        return Dial(interface=self)
```

In `qt_dial.py` we create a subclass of `toga_qt.widgets.slider.Slider` that creates a `QDial`:
``` python
from PySide6.QtWidgets import QDial
from toga_qt.widgets.slider import Slider

class Dial(Slider):
    """The Dial implementation."""

    def create(self):
        IntSliderImpl.__init__(self)
        self.native = QDial()
        self.native.setMinimum(0)
        self.native.valueChanged.connect(self.qt_on_change)
        self.native.sliderPressed.connect(self.qt_on_press)
        self.native.sliderReleased.connect(self.qt_on_release)
```

More complex widgets will obviously have a lot more to them, but this will often be sufficient for a one-off custom widget for an application.

## Widgets with Multiple Backends

The previous section is fine as long as you only care about one backend implementation, but as soon as you have multiple backends that you care about you are faced with the problem of how does the interface know which implementation to use?

Toga solves this with "factory" objects which are namespaces that lazily load implementations based on the [`toga.backend`][toga.backend]. The default factory object uses the Python standard library [`importlib.metadata`][importlib.metadata] "entry point" system to load backend widgets in a plugin-style system.  Every backend advertises where to find the widget implementations as part of its `pyproject.toml`. So if you look at the Qt `pyproject.toml` you will see a section that looks like:
``` toml
[project.entry-points."toga_core.backend.toga_qt"]
App = "toga_qt.app:App"
Command = "toga_qt.command:Command"
Font = "toga_qt.fonts:Font"
```
and so-on.  This tells [`importlib.metadata`][importlib.metadata] that there is a group of entry points called `toga_core.backend.toga_qt` and each entry point consists of an interface name (like `App`) and the location of the implementation (like `toga_qt.app:App`, which means the `App` class in the `toga_at.app` module).

We can get a factory object by calling [`toga.platform.get_factory`][toga.platform.getfactory] and then get the implementation as an attribute on the factory. So `get_factory().Slider` will give you the implementation class for the slider in the current backend.  If you look at the widget interface classes in Toga, you will see that most of their [`_create`][toga.widgets.base.Widget._create] methods look like:
``` python
class Slider(Widget):

    def _create(self):
        return self.factory.Slider(interface=self)
```

### Implementing Missing Widgets

Not every widget is available in every backend. You may find yourself needing to implement a widget for a backend before the Toga core developers can provide it.  In this case you can write your implementation as part of your application code, and then add an entry point for that widget.

For example, at the time of writing, the `toga_textual` backend doesn't implement the [`toga.Switch`][toga.Switch] widget.  We could write one something like this in a module `my_app.textual_switch`:
``` python
from textual.widgets import Checkbox as TextualCheckbox
from travertino.size import at_least
from toga_textual.widgets.base import Widget

class TogaCheckbox(TextualCheckbox):
    def __init__(self, impl):
        super().__init__()
        self.interface = impl.interface
        self.impl = impl

    def on_checkbox_changed(self, event: TextualCheckbox.Changed) -> None:
        self.interface.on_change()


class Switch(Widget):
    def create(self):
        self.native = TogaCheckbox(self)

    def get_text(self):
        return self.native.label

    def set_text(self, text):
        self.native.label = text

    def get_value(self):
        return self.native.value

    def set_value(self, value):
        self.native.value = value

    def rehint(self):
        self.interface.intrinsic.width = at_least(len(self.native.label) + 8)
        self.interface.intrinsic.height = 3
```
and then add the following to the application's `pyproject.toml`:
``` toml
[project.entry-points."toga_core.backend.toga_textual"]
Switch = "my_app.textual_switch:Switch"
```
With this set-up, you can import and use `toga.Switch` within your application normally.

Ideally, if you have a working implementation of a missing widget, you'd make a pull-request to add it to the appropriate Toga backend.

### Implementing a New Backend

You can use these ideas to implement a new backend for Toga.  To do this, you would need to write as many of the backend class implementations as is possible in a project, and then in the `pyproject.toml` list entrypoints in the `toga.backend` group for each platform that supports the backend, and then have entrypoints for each backend implementation.

For example, Toga is not likely to ever have a WxPython backend as part of the core library because WxPython is not a native UI toolkit.  But there may be value in such a backend for applications that are already using WxPython.  Since this is not an official backend, you might call it `togax_wx`, and your `pyproject.toml` would look like:
``` toml
[project.entry-points."toga.backends"]
linux = "togax_wx"
windows = "togax_wx"
macOS = "togax_wx"
freeBSD = "togax_wx"

[project.entry-points."toga_core.backend.togax_wx"]
App = "togax_wx.app:App"
Command = "togax_wx.command:Command"
```
and so on.

### Implementing New Interfaces

All of the examples with multiple backends rely on widgets which already exist as part of the `toga_core` interface.  What if we want to implement our own interface widgets?

We could implement them using the `toga_core.backend.*` groups, but this runs the risk of colliding with other libraries, or with future widgets added to Toga by the core team.  The solution in this case is to create your own custom `togax_*` interface and use it instead of `toga_core`.

For example, at the time of writing the Toga core does not provide a `Toggle Button` widget (ie. a push-button which toggles state when pressed), relying on the similar `Switch` for this sort of UI interaction.  We could write a library which provides this widget in the following way.

We will call the library `togax_toggle` and write a collection of implementations as `togax_toggle.cocoa_toggle`, `togax_toggle.gtk_toggle`, `togax_toggle.qt_toggle`, `togax_toggle.winforms_toggle` and so-on.  For example `togax_toggle.qt_toggle` might look something like:
``` python
from PySide6.QtWidgets import QPushButton
from travertino.size import at_least

from toga_qt.widgets.switch import Switch

class Toggle(Switch):

    def create(self):
        self.native = QPushButton()
        self.native.setCheckable(True)
        self.native.toggled.connect(self.qt_on_change)
```
Other backends would be implemented similarly.

When it comes time to write the interface class we can base it directly on `Switch`, but instead of being in the `toga_core` set of widge interfaces, it is in the `togax_toggle` interface group.  This is indicated by [`_interface_group`][toga.widgets.base._interface_group] class attribute, which is passed to the factory so that it uses the correct entry points:
``` python
from toga import Switch

class Toggle(Switch)
    _interface_group = "togax_toggle"
```

Once this is written, we can add the entry points to the `pyproject.toml`:
``` toml
[project.entry-points."togax_toggle.backend.toga_qt"]
Toggle = "togax_toggle.qt_toggle:Toggle"

[project.entry-points."togax_toggle.backend.toga_gtk"]
Toggle = "togax_toggle.gtk_toggle:Toggle"

[project.entry-points."togax_toggle.backend.toga_cocoa"]
Toggle = "togax_toggle.cocoa_toggle:Toggle"
```
and so on.

## Other Backend-Dependent Objects

There are other objects beyond widgets which are dependent on different backend implementations, particularly hardware features, but also things like notification displays, clipboards, and other OS services.

To extend Toga in this way, ensure that you get the appropriate factory for your extension, and use that to create the implementation object.

For example, an accelerometer hardware interface as part of a `togax_sensors` library could look something like:
``` python
from toga.platform import get_factory

class Accelerometer:

    def __init__(self, app: App):
        self.factory = get_factory('togax_sensors')
        self._app = app
        self._impl = self.factory.Accelerometer(interface=self)

    @property
    def acceleration(self):
        return self._impl.get_acceleration()
```
with the corresponding backend for Qt looking something like:
``` python
from PySide6.QtSensors import QAccelerometer

class Accelerometer:

    def __init__(self, interface):
        self.interface = interface
        self.native = QAccelerometer(interface._app._impl.native)

    def get_acceleration(self):
        reading = self.native.reading()
        return (reading.x(), reading.y(), reading.z())
```
and entry points like:
``` toml
[project.entry-points."togax_sensors.backend.toga_qt"]
Accelerometer = "togax_sensors.qt.accelerometer:Accelerometer"
```
