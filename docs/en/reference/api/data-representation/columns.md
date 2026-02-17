{{ component_header("Columns") }}

## Usage

Columns are abstractions that allow you to specify how the data in a Table or Tree widget should be displayed. Each column object is responsible for taking a row from the data source and providing text, icon and other display elements suitable for the Table and Tree widgets to use.

The protocol, [`ColumnT`][toga.sources.columns.ColumnT], describes what custom Column implementations need to provide so that they can be used by the widget. Toga provides the [`AccessorColumn`][toga.sources.columns.AccessorColumn] as an implementation of the `Column` protocol which is used by default in the Table and Tree widgets.

Each `AccessorColumn` holds the heading text and an attribute name that is used to get values from each row to use in the column.

-8<- "snippets/accessors.md"

-8<- "snippets/accessor-values.md"

You can define your own subclasses that can override the way that text and icons are computed to provide custom formatting of text.  For example, we could create a column that takes a value which is a list of strings and formats it as a comma-separated list as follows:

```python
class ListStrColumn(AccessorColumn):

    def text(self, row, default=None):
        value = super(row, default)
        if value is not None:
            return ", ".join(value)

        return default
```
so a row providing the value `["Drama", "Action"]` would be displayed in the table cell as `"Drama, Action"`.

Custom columns can even override the default way of looking up values to allow such things as combining values from multiple attributes, looking up values by index rather than attribute, or using a method or function on the row.  The [`Column`][toga.sources.columns.Column] class provides a convenient minimal base class for implementing custom columns.
```python
class NameColumn(Column):

    def value(self, row):
        return f"row.lastname, row.firstname"
```


## Reference

::: toga.sources.columns.ColumnT

::: toga.sources.columns.Column

::: toga.sources.columns.AccessorColumn
