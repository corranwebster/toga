# Backends

The core Toga project comes with a variety of different backends that implement the behaviour of the core Widgets and act as an intermediary between the core interface objects and the underlying native objects.

The name of the currently active backend can be found as `toga.backend`.

## Backend Selection

Toga discovers available backends via Python's entry point mechanism. Each backend advertises that it provides a backend by setting an entry-point in the `toga.core.backends` group in its package metadata.

Normally there should be exactly one backend installed in an application's virtual environment, and so Toga will use that. However it is possible that there might be multiple valid backends installed in an environment, such as when a developer is working on Toga itself. For example on Linux there could be any out of the Gtk, Qt, Textual and Web backends installed and working in a given environment.

When faced with multiple backends, Toga will look for the `TOGA_BACKEND` environment variable, and use the backend named there. Otherwise it will raise an Exception.

## Implementation Objects and the Factory

Once the backend is known, the implementations of the widgets and other backend features are also provided via entrypoints in the backend's package that contribute to the `toga.core.backend.{backend}` group. So, for example all the iOS backend widgets are contributed to the `toga.core.backend.{backend}` group.

The `toga.platform.factory` object is responsible for lazily loading the backend objects as they are needed. Widget implementation classes are available as `factory.<widget>` (so for example, the implementation of the `LineEdit` widget for the active backend can be accessed as `factory.LineEdit`).

The factory is an instance of a general `Factory` class that is given a project name (the default is "core") and looks up the current backend name from `toga.backend`, and then lazily loads from the entrypoint group `toga.<project_name>.backend.<backend_name>`, so if the current backend is `toga_cocoa` then:

``` python
my_factory = Factory("my_project")
my_factory.MyWidget
```
will look for an entrypoint with name "MyWidget" in the entrypoint group `toga.my_project.backend.toga_cocoa` and then call the entrypoint's `load()` method to get the implementation class object. If no such object is found, it will raise an error. It then adds the object as an attribute so it doesn't need to load the entrypoint multiple times.

# Use Cases

This scheme is designed to support a number of use cases.

## Adding a New Widget to Core Toga

The developer needs to write the interface object and the concrete interface classes in each backend. For each backend, the developer needs to add an entry point of the form `<Widget class name> = <implementation module>:<Widget class name>` to the `toga.core.backend.<backend name>`.

So for example, the iOS canvas widget is registered in the `pyproject.toml` for `toga_iOS`.

``` toml
[project.entry-points."toga.core.backend.toga_iOS"]
Canvas = "toga_iOS.widgets.canvas:Canvas"
```

## Adding a Third-Party Implementation for an Unimplemented Core Widget

Some backends may not yet have implementations for all core widgets. In these cases if your application needs this widget, you can write an implementation and make it available via an entry point in your application or library. Add an entrypoint for the widget to you application's `pyproject.toml`.

So say you had implemented a `Table` widget for iOS in a module `my_ios_app.widgets.table` in your application, then you could add the following to your `pyproject.toml`:

``` toml
[project.entry-points."toga.core.backend.toga_iOS"]
Table = "my_ios_app.widgets.table:Table"
```

## Adding a new Backend

To add a new backend for Toga you need to create a project with the backend implementations of the Toga widgets. You then need to add entrypoints for your backend, and then for each object that Toga expects to see in the factory.

So for example, to implement a backend for watchOS, you would add something like the following to the `pyproject.toml`:

``` toml
[project.entry-points."toga.core.backends"]
watchOS = "toga_watchOS"

[project.entry-points."toga.core.backend.watchOS"]
App = "toga_watchOS.app:App"
DocumentApp = "toga_watchOS.app:DocumentApp"
Button = "toga_watchOS.widgets.button:Button"
...
```

It probably makes sense to follow the same module and class layout as other backends, but there is no requirement to do so.

Note that the name of the backend doesn't have to match the name of the platform: in most cases the dependencies for your backend will make it difficult or impossible to install on a platform where it won't work.


## Adding Your Own Custom Widgets

You may find your application or library has a need for a new Widget which isn't available as part of Toga yet. The first step, as with any widget, is writing the interface class; after that you need to write the implementation of the backends you need.

For a simple application with one backend, this may be enough, with your interface code simply importing the implementation object directly in the `create` method:

``` python
from toga import Widget

class MyWidget(Widget):
    def create(self):
        from my_app.backend.my_widget import MyWidget
        self._impl = MyWidget(self)
```

But if you want your application to be cross-platform, you will have multiple implementations for different backends, and you should do the following:

- create a new `Factory` object for your application or library with it's own project name and make that factory object part of your internal API.
- in your `pyproject.toml` add entrypoints for each implementation of the interface of in groups of the form `toga.<project_name>.backend.<backend_name>`.

Particularly complex applications or libraries which are defining many new widgets may find it useful to follow Toga's example and break out the implementations into separate projects to make dependency management easier.

### Example

As a concrete example, assume that you are writing a cross-platform bitmap editing application. In your application, you create a Factory object for your project, passing it the name you want to use for your entrypoint groups (in this case `"my_app"`).

In module :my_app.platform`
``` python
from toga.platform import Factory

factory = Factory("my_app")
```

You then might write the interface for a new `BitmapView` widget. In `my_app.widgets.bitmap_view`:
``` python
from toga import Widget
from my_app.factory import my_factory

class BitmapView(Widget):

    def create(self):
        self._impl = my_factory.BitmapView(self)
```

Then you might write the implementation for macOS. In `my_app.cocoa.widgets.bitmap_view`:
``` python
from toga_cocoa.widgets.base import Widget

class BitmapView(Widget):
    def create(self):
        self.native = ...
```

And another for GTK. In `my_app.gtk.widgets.bitmap_view`:
``` python
from toga_gtk.widgets.base import Widget

class BitmapView(Widget):
    def create(self):
        self.native = ...
```

And then in your `pyproject.toml` you might have something like:
``` toml
[project]
dependencies = ['toga_core']

[project.optional-dependencies]
cocoa = ["toga_cocoa"]
gtk = ["toga_gtk"]

[project.entry-points."toga.my_app.backend.toga_cocoa"]
BitmapView = "my_app.cocoa.bitmap_view:BitmapView"

[project.entry-points."toga.my_app.backend.toga_gtk"]
BitmapView = "my_app.gtk.bitmap_view:BitmapView"
```

Note that instead of the "toga.core.backend..." groups, you are contributing to the "toga.my_app.backend..." groups, matching the project name of the toolkit object

## Adding an Implementation of a Third-Party Widget for a Backend

It may be that someone has written a third-party widget that is useful to you, but not on the platform you need. Assuming that they have followed the pattern of the previous section and created a factory object of their own, then if you write an implementation of the backend in your project you can contribute it to their project's `toga.<project_name>.backend.<backend_name>` entrypoint group.

### Example

Continuing the provious example, assume that someone has a pjorject as described above that has a `BitmapView` widget, but only for macOS and GTK.  If you needed an implementation for Qt, for example, you could write your own implementation, something like this:

In module `another_app.qt.bitmap_view`:
``` python
from toga_qt.widgets.base import Widget

class BitmapView(Widget):
    def create(self):
        self.native = ...
```

And then add it to *your* `pyproject.toml` contributing to *their* entrypoint groups:
``` toml
[project.optional-dependencies]
qt = ["toga_qt"]

[project.entry-points."toga.my_app.backend.toga_qt"]
BitmapView = "another_app.qt.bitmap_view:BitmapView"
```

Once you've done this you can import the interface from their library and use it in your application with the backend you want:

In module `another_app.app`:
```python
from toga import App
from my_app.widgets.bitmap_view import BitmapView

class AnotherApp(App):
    def startup(self):
        bitmap_view = BitmapView()
        ...
```

## Writing Composite Widgets or Reusing Implementations

It might be the case that an existing core widget implementation provides everything you need for another widget.

For example, you may be writing an HTML documentation-browsing widget for you application's help system. For these purposes, the WebView widget's implementation likely provides everything that you need, but you don't need the full power of it. In cases like this, you can get the implementation from the factory and use it in your interface class:

``` python
from pathlib import Path
from toga import Widget
from toga.platform import toolkit

HELP_PATH = Path(...)

class HelpViewer(Widget):
    def __init__(self, topic=None, ...):
        super().__init__(...)
        self.topic = topic

    def create(self):
        self._impl = toolkit.WebView(self)

    @property
    def topic(self):
        return self._topic

    @topic.setter
    def topic(self, value):
        path = HELP_PATH.join(value + ".html")
        content = open(path).read()
        self._impl.set_content(content)
```

## Overriding the Implementation of a Widget

Sometimes you may need to use a different implementation of a widget for your application.

In this case the simplest approach may be a subclass of the original widget which uses your implementation: this is essentially the same process as adding a custom widget.

XXX: not sure this is a good idea!

It might be that this doesn't work for your needs and you need to use the original widget interface but with a different implementation, for example replacing the implementation with a mock for testing. You can't use the entrypoint mechanism for this: if the factory discovers multiple entrypoints for the same widget in the same backend, it is undefined which one will be chosen.

What you can do is define your own factory object for your app, and contribute your implementations for each backend to that factory as if you were writing implementations for your own custom widget::

In module `my_app.cocoa.line_edit`:
``` python
from toga_cocoa.widgets.line_edit

class MyLineEdit(LineEdit):
    # override with new behaviour
```

And in the `pyproject.toml` have entries like
``` toml
[project.entry-points."toga.my_app.backend.toga_cocoa"]
LineInput = "my_app.cocoa.line_edit:MyLineEdit"
```

And then in your App, or anywhere else you are creating widgets, do something like:
``` python
from toga import App, LineInput
from toga.platform import factory

from my_app.platform import my_factory

class MyApp(App):
    def startup(self):
        # replace core LineInput implementation with custom one
        factory.LineInput = my_factory.LineInput

        line_input = LineInput()  # patched line input
        ...

        # the core LineInput can be restored
        del factory.LineInput

        another_line_input = LineInput()  # unpatched line input
        ...
```

XXX: This is an even worse idea

In the extreme, you could create your own factory instance and monkeypatch `toga.platform` with your own. In this case you'd need to make sure that you have entrypoints for everything that you're going to use, including ones pointing to the core implementations.

# Design Notes

In comparison to the current system, this makes the following changes:

- the notion of a "platform", or the linking between platforms and backends, is diminished. In practice, most of the time an application will have a well-controlled environment and so there will be exactly one backend. A regular entrypoint search should be enough, augmented by the ability to override with an environment variable to force selection which would be used by developers who happen to have multiple backends in an environment.
- This has the side-effect of making support for new platforms easier: there is no need to update `toga.platforms._TOGA_PLATFORMS` every time a new platform comes along (eg. currently OpenBSD isn't in this list, and isn't listed as an entrypoint for Gtk or Qt backends, but I would expect the GTK or Qt backends to work on a correctly configured system).
- we might want to have a manually curated list of "preferred backends" for each platform, but even them that feels like a problem for Briefcase more than Toga.
- the backend "factory" modules can be dispensed with completely.
- the number of entrypoint searches isn't unreasonable. It should be two in most cases - one to lookup the backend, and one to find all the widget entrypoints. I'm old enough that my instincts are that entrypoints are slow, but I think `importlib.metadata` is significantly more performant than `pkg_resources`.
- rather than using `import_module` we use `EntryPoint.load` which is more flexible and doesn't require exact matching between organization of modules in the backend (particularly important for an app that needs to add a custom widget or two).
