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

import os
import yaml

from pydantic import BaseModel, Field

from textual.app import App, ComposeResult
from textual.containers import Container, VerticalScroll, Horizontal
from textual.geometry import clamp
from textual.message import Message
from textual.reactive import reactive, var
from textual.widget import Widget
from textual.widgets import Input, Label, Switch, Header, Markdown, TextArea, OptionList, Static, Placeholder
from textual.widgets.option_list import Option

from typing import List, Dict

from .loader import BUNDLED_DIR

# use pydantic for this
class Server(BaseModel):
    """An instance of a server we are managing."""

    name: str
    arguments: dict[str, Any]
    print_format: Literal["markdown", "text", "none"] = "text"
    file: str | None = None


RUNNING_SERVERS : Dict[str, List[Server]]= {}

def load_yaml_file(file_path):
    """
    Loads a YAML file and returns its content as a Python dictionary.
    """
    try:
        with open(file_path, 'r') as file:
            data = yaml.safe_load(file)
        return data
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return None
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")
        return None
    
class InspectionWindow(Widget):
    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Markdown("Readme", id="readme")

class HistoryWindow(Widget):
    def compose(self) -> ComposeResult:
        yield Placeholder()

class ServerNotificationsWindow(Widget):
    def compose(self) -> ComposeResult:
        yield Placeholder()

class MainWindow(Widget):
    DEFAULT_CSS = """
    MainWindow > InspectionWindow {
        height: 3fr;
        align: center middle;
    }
    MainWindow > InspectionWindow.top {
        background: $boost;
    }
    MainWindow > Horizontal {
        height: 1fr;
    }
    MainWindow > Horizontal > HistoryWindow {
        width: 1fr;
    }
    MainWindow > Horizontal > ServerNotificationsWindow {
        width: 1fr;
    }
    MainWindow Input {
        width: 16;
    }
    """

    value : reactive[str] = reactive("")

    def compose(self) -> ComposeResult:
        yield InspectionWindow()
        with Horizontal():
            yield HistoryWindow()
            yield ServerNotificationsWindow()

    def watch_value(self, value: str) -> None:  
        """When self.value changes, update switches."""

        readme = ""

        # read the readme
        path = BUNDLED_DIR / "servers" / value / "README.md"
        if path.exists():
            with open(path, 'r') as f:
                readme = f.read()
        
        # read the yaml
        path = BUNDLED_DIR / "servers" / value / "server.yml"
        
        if path.exists:
            obj = load_yaml_file(path)
            # pull out agents
            # pull out servers
            # pull out tools
            # introspect things
            # have things be turned on or off
            # query the current environment / set values


        # set values
        

        self.query_one(InspectionWindow).query_one("#readme", Markdown).update(readme)


def get_bundled_list(p: str = "servers") -> List[str]:
    root = BUNDLED_DIR / p
    bundled = os.listdir(root)
    result = []
    for b in bundled:
        if os.path.isdir(root / b):
            if (root / b / "server.yml").exists():
                result.append(b)
    return result

class Bundled(Widget):
    def compose(self) -> ComposeResult:

        bundled = get_bundled_list()
        options = []
        for f in bundled:
            options.append(Option(f"{f}", id=f"option-{f}"))

        yield OptionList(
            *options
        )

class TuiApp(App):

    BINDINGS = [
        ("s", "toggle_sidebar", "Toggle Sidebar"),
        ("q", "quit", "Quit"),
    ]

    # local variables
    show_sidebar = var(True)


    CSS_PATH = "tui.tcss"


    # watcher functions
    def watch_show_sidebar(self, show_sidebar: bool) -> None:
        """Set or unset visible class when reactive changes."""
        self.set_class(show_sidebar, "-visible")


    # automatic action functions
    # binding functions
    def action_toggle_sidebar(self) -> None:
        """Toggle the sidebar visibility."""
        self.show_sidebar = not self.show_sidebar

    # UI functions
    def on_mount(self) -> None:
        self.query_one(Bundled).focus()

        def theme_change(_signal) -> None:
            """Force the syntax to use a different theme."""
            self.watch_server(self.server)

        self.theme_changed_signal.subscribe(self, theme_change)

    def on_option_list_option_selected(self, event : OptionList.OptionSelected) -> None:
        self.query_one(MainWindow).value = f"{event.option.prompt}"


    def compose(self) -> ComposeResult:
        yield MainWindow()
        yield Bundled(id="tree-view")


if __name__ == "__main__":
    app = TuiApp()
    app.run()