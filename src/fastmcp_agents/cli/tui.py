"""Textual TUI for the FastMCP Agents CLI.

Much of this is inspired by the following:

* [Posting](https://github.com/darrenburns/posting)
* [Textual](https://github.com/Textualize/textual)
* [Trogon](https://github.com/Textualize/trogon)

Ascii art for the layout:

```

    +-----------------------+---------------------------------------------------------------------+
    | MCP Inspector v0.14.3 |                                                                     |
    |-----------------------|                                                                     |
    | Transport Type        |                                                                     |
    | | STDIO         v |   |                                                                     |
    |                       |                                                                     |
    |  Command              |                                                                     |
    | |   uvx           |   |                                                                     |
    |                       |                                                                     |
    |  Arguments            |                                                                     |
    | | --from "git+https:| |                                                                     |
    |                       |                                                                     |
    |  |>Environment Vars   |                                                                     |
    |                       |                                                                     |
    |                       |                                                                     |
    |                       |                                                                     |
    |                       |                                                                     |
    |                       |                                                                     |
    |                       |                                                                     |
    |                       +--------------------------------------+------------------------------+
    |                       |                                      |                              |
    |                       |                                      |                              |
    |                       |                                      |                              |
    |                       |                                      |                              |
    |                       |                                      |                              |
    |                       |                                      |                              |
    |                       |                                      |                              |
    |                       |                                      |                              |
    +-----------------------+--------------------------------------+------------------------------+

```

A simple animated sidebar.

See comments for details.

"""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.containers import Vertical, Container, VerticalScroll
from textual.reactive import reactive, var
from textual.widget import Widget
from textual.widgets import Label, DirectoryTree, Footer, Header, Static

import os
import sys

from rich.syntax import Syntax
from rich.traceback import Traceback



TEXT = """I must not fear.
Fear is the mind-killer.
Fear is the little-death that brings total obliteration.
I will face my fear.
I will permit it to pass over me and through me.
And when it has gone past, I will turn the inner eye to see its path.
Where the fear has gone there will be nothing. Only I will remain."""


class TuiApp(App):
    """
    Test app to show our sidebar.
    """

    """Textual code browser app."""

    CSS_PATH = "tui.tcss"
    BINDINGS = [
        ("s", "toggle_sidebar", "Toggle Sidebar"),
        ("q", "quit", "Quit"),
    ]

    show_sidebar = var(True)
    path: reactive[str | None] = reactive(None)

    def watch_show_sidebar(self, show_sidebar: bool) -> None:
        """Set or unset visible class when reactive changes."""
        self.set_class(show_sidebar, "-visible")


    def compose(self) -> ComposeResult:
        """Compose our UI."""
        path = os.getcwd()
        yield Header()
        with Container():
            yield DirectoryTree(path, id="tree-view")
            with VerticalScroll(id="code-view"):
                yield Static(id="code", expand=True)
        yield Footer()


    def on_mount(self) -> None:
        self.query_one(DirectoryTree).focus()

        def theme_change(_signal) -> None:
            """Force the syntax to use a different theme."""
            self.watch_path(self.path)

        self.theme_changed_signal.subscribe(self, theme_change)

    def on_directory_tree_file_selected(
        self, event: DirectoryTree.FileSelected
    ) -> None:
        """Called when the user click a file in the directory tree."""
        event.stop()
        self.path = str(event.path)

    def watch_path(self, path: str | None) -> None:
        """Called when path changes."""
        code_view = self.query_one("#code", Static)
        if path is None:
            code_view.update("")
            return
        try:
            syntax = Syntax.from_path(
                path,
                line_numbers=True,
                word_wrap=False,
                indent_guides=True,
                theme="github-dark" if self.current_theme.dark else "github-light",
            )
        except Exception:
            code_view.update(Traceback(theme="github-dark", width=None))
            self.sub_title = "ERROR"
        else:
            code_view.update(syntax)
            self.query_one("#code-view").scroll_home(animate=False)
            self.sub_title = path


    def action_toggle_sidebar(self) -> None:
        """Toggle the sidebar visibility."""
        self.show_sidebar = not self.show_sidebar


if __name__ == "__main__":
    app = TuiApp()
    app.run()