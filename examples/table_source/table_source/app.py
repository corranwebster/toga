import bisect
from operator import attrgetter
from random import choice

import toga
from toga.constants import COLUMN, ROW
from toga.sources import Source

bee_movies = [
    ("The Secret Life of Bees", "2008", "7.3", "Drama"),
    ("Bee Movie", "2007", "6.1", "Animation, Adventure, Comedy"),
    ("Bees", "1998", "6.3", "Horror"),
    ("The Girl Who Swallowed Bees", "2007", "7.5", "Short"),
    ("Birds Do It, Bees Do It", "1974", "7.3", "Documentary"),
    ("Bees: A Life for the Queen", "1998", "8.0", "TV Movie"),
    ("Bees in Paradise", "1944", "5.4", "Comedy, Musical"),
    ("Keeper of the Bees", "1947", "6.3", "Drama"),
]


class Movie:
    # A class to wrap individual movies
    def __init__(self, title, year, rating, genre):
        self.year = int(year)
        self.title = title
        self.rating = float(rating)
        self.genre = genre


class MovieSource(Source):
    def __init__(self):
        super().__init__()
        self._movies = []

    def __len__(self):
        return len(self._movies)

    def __getitem__(self, index):
        return self._movies[index]

    def index(self, entry):
        return self._movies.index(entry)

    def add(self, entry):
        movie = Movie(*entry)
        index = bisect.bisect(self._movies, movie.year, key=attrgetter("year"))
        with self.pre_notify("insert", index=index, item=movie):
            self._movies.insert(index, movie)

    def remove(self, item):
        index = self.index(item)
        with self.pre_notify("remove", index=index, item=item):
            del self._movies[index]

    def clear(self):
        self._movies = []
        self.notify("clear")


class GoodMovieSource(Source):
    # A data source that piggy-backs on a MovieSource, but only
    # exposes *good* movies (rating > 7.0)
    def __init__(self, source):
        super().__init__()
        self._source = source
        self._source.add_listener(self)
        self._removals = {}

    # Implement the filtering of the underlying data source
    def _filter(self, movie):
        """Whether or not to include the movie."""
        return movie.rating > 7.0

    def _filtered(self):
        """Current sorted and filtered list."""
        return sorted(
            (m for m in self._source._movies if self._filter(m)),
            key=attrgetter("rating"),
            reverse=True,
        )

    # Methods required by the ListSource interface
    def __len__(self):
        return len(list(self._filtered()))

    def __getitem__(self, index):
        return self._filtered()[index]

    def index(self, entry):
        return self._filtered().index(entry)

    def _notify_if_present(self, notification, item, index=None):
        if self._filter(item):
            # If the item exists in the filtered list, propagate the notification
            kwargs = {"item": item}
            if index is not None:
                # notification needs and index: where is it, or would it be,
                # in the sorted list?
                kwargs["index"] = bisect.bisect_left(
                    self._filtered(),
                    item.rating,
                    key=attrgetter("rating"),
                )
            self.notify(notification, **kwargs)

    def pre_insert(self, index, item):
        self._notify_if_present("pre_insert", item=item, index=index)

    def post_insert(self, index, item):
        self._notify_if_present("insert", item=item, index=index)

    def pre_remove(self, index, item):
        self._notify_if_present("pre_remove", item=item, index=index)

    def post_remove(self, index, item):
        self._notify_if_present("remove", item=item, index=index)

    def change(self, item):
        self._notify_if_present("change", item=item)

    def clear(self):
        self.notify("clear")


class TableSourceApp(toga.App):
    # Table callback functions
    def on_select_handler(self, widget, **kwargs):
        if isinstance(widget, toga.Table):
            row = widget.selection
        else:
            row = widget.value
        self.label.text = (
            f"You selected row: {row.title}" if row is not None else "No row selected"
        )

    # Button callback functions
    def insert_handler(self, widget, **kwargs):
        self.table1.data.add(choice(bee_movies))

    def delete_handler(self, widget, **kwargs):
        if self.table1.selection:
            self.table1.data.remove(self.table1.selection)
        elif len(self.table1.data) > 0:
            self.table1.data.remove(self.table1.data[0])
        else:
            print("Table is empty!")

    def clear_handler(self, widget, **kwargs):
        self.table1.data.clear()

    def startup(self):
        self.main_window = toga.MainWindow()

        # Label to show which row is currently selected.
        self.label = toga.Label("Ready.")

        # Create two tables with custom data sources; the data source
        # of the second reads from the first.
        # The headings are also in a different order.
        self.table1 = toga.Table(
            headings=["Year", "Title", "Rating", "Genre"],
            data=MovieSource(),
            flex=1,
            on_select=self.on_select_handler,
        )

        self.table2 = toga.Table(
            headings=["Rating", "Title", "Year", "Genre"],
            data=GoodMovieSource(self.table1.data),
            flex=1,
        )

        # Populate the table
        for entry in bee_movies:
            self.table1.data.add(entry)

        tablebox = toga.Box(children=[self.table1, self.table2], flex=1)

        # Create a Selection that is also using the data source
        self.selection = toga.Selection(
            items=self.table2.data,
            accessor="title",
            on_change=self.on_select_handler,
            flex=1,
        )
        selection_label = toga.Label("Choose a movie:", flex=0.5)
        selection_box = toga.Box(
            children=[selection_label, self.selection],
            direction=ROW,
        )

        # Buttons
        btn_insert = toga.Button("Insert Row", on_press=self.insert_handler, flex=1)
        btn_delete = toga.Button("Delete Row", on_press=self.delete_handler, flex=1)
        btn_clear = toga.Button("Clear Table", on_press=self.clear_handler, flex=1)
        btn_box = toga.Box(children=[btn_insert, btn_delete, btn_clear], direction=ROW)

        # Most outer box
        outer_box = toga.Box(
            children=[btn_box, tablebox, selection_box, self.label],
            flex=1,
            direction=COLUMN,
            margin=10,
        )

        # Add the content on the main window
        self.main_window.content = outer_box

        # Show the main window
        self.main_window.show()


def main():
    return TableSourceApp("Table Source", "org.beeware.toga.examples.table_source")


if __name__ == "__main__":
    main().main_loop()
