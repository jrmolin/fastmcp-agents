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

import pathlib
from pydantic import BaseModel, Field

from textual import log
from textual.app import App, ComposeResult
from textual.containers import Container, VerticalScroll, Horizontal, Center
from textual.geometry import clamp
from textual.message import Message
from textual.reactive import reactive, var
from textual.widget import Widget
from textual.widgets import (
    Input, Label, Switch, Header, Markdown, TextArea, OptionList, Static, Placeholder,
    ContentSwitcher, Button, DataTable,
    ListItem, ListView,
)
from textual.widgets.option_list import Option

from typing import List, Dict

from .models import AugmentedServerModel
from .loader import get_config_for_bundled, get_list_of_bundled_servers
from .base import CliContext

# use pydantic for this
class Server(BaseModel):
    """An instance of a server we are managing."""
    name: str
    augmented_server_model: AugmentedServerModel


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
    """Maybe this should start with all the available bundled servers.
    """
    value : reactive(str) = reactive("")

    def update(self, value) -> None:
        self.value = value


    def watch_value(self, server: str) -> None:

        log(f"got a value in watch_value: {server}")
        # md = self.readme
        # md.load(path)
        # md.loading = False

    
        # table = self.query_one(DataTable)
        # agents = ",".join([x["name"] for x in obj.get("agents", [])])
        # table.add_rows(
        #     [
        #         (pathlib.Path(value).name.ljust(35), agents)
        #     ]
        # )

    def compose(self) -> ComposeResult:

        with Horizontal(id="buttons"):  
            yield Button("DataTable", id="data-table")  
            yield Button("Markdown", id="markdown")  

        with ContentSwitcher(initial="data-table"):
            yield DataTable(id="data-table")

            with VerticalScroll(id="markdown"):
                yield Markdown()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.query_one(ContentSwitcher).current = event.button.id  

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("server", "agents")

        readme = self.query_one(Markdown)
        readme.loading = True
        readme.update("readme here")


class HistoryWindow(Widget):
    """This should be a running list of all actions so far.
    """
    def append(self, value: str) -> None:
        self.query_one(ListView).append(ListItem(Label(value)))

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            with Center():
                yield ListView()

    def on_mount(self) -> None:
        widget = self.query_one(ListView)
        widget.styles.background = "darkblue"
        widget.styles.border = ("heavy", "yellow")
        widget.border_title = f"{self.__class__.__name__}"
        widget.border_title_align = "center"


class ServerNotificationsWindow(Widget):
    """Maybe the status of all running servers, in a tree
    """
    def compose(self) -> ComposeResult:
        self.widget = Static(f"{self.__class__.__name__}")
        with Center():
            yield self.widget

    def on_mount(self) -> None:
        self.widget.styles.background = "darkblue"
        self.widget.styles.border = ("heavy", "yellow")
        self.widget.border_title = f"{self.__class__.__name__}"
        self.widget.border_title_align = "center"


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
        self.inspection = InspectionWindow()
        yield self.inspection
        with Horizontal():
            yield HistoryWindow()
            yield ServerNotificationsWindow()

    def watch_value(self, value: str) -> None:  
        """When self.value changes, update switches."""

        self.query_one(HistoryWindow).append(value)
        self.inspection.update(value)


class Bundled(Widget):
    def compose(self) -> ComposeResult:

        bundled = get_list_of_bundled_servers()
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

    selected_bundle : reactive(str) = ""

    cli_ctx : CliContext = None

    history : List[Server] = []

    def __init__(self, cliContext : CliContext | None) -> None:
        self.cli_ctx = cliContext
        super().__init__()

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

    async def on_option_list_option_selected(self, event : OptionList.OptionSelected) -> None:
        # event.stop()
        value = event.option.prompt
        self.query_one(MainWindow).value = value


        self.log(f"watching selected bundle: {value}")
        server = await self.get_server(value)

    async def get_server(self, value: str) -> Server:

        # look for value in our history
        for h in self.history:
            if h.name == value:
                # TODO: implement LRU by moving this to the front of the list
                return h

        # Didn't find it, so create one
        try:
            augmented_server_model = get_config_for_bundled(value)

            # agents, mcp_clients, server = await augmented_server_model.to_fastmcp_server(
            #     server_settings=self.cli_ctx.server_settings)

            # don't do this
            # await run_server_or_call_tools(
            #     agents=agents,
            #     mcp_clients=mcp_clients,
            #     server=server,
            #     pending_tool_calls=None,
            #     transport=s.transport,
            # )

            server = Server(name=value, augmented_server_model=augmented_server_model)
            self.history.append(server)
            return server

        except FileNotFoundError as f:
            return None
        except Exception as e:
            self.log(f"Error raised: {e}")
            raise e

        # introspect things
        # have things be turned on or off
        # query the current environment / set values 

    def compose(self) -> ComposeResult:
        yield MainWindow()
        yield Bundled(id="tree-view")


if __name__ == "__main__":
    app = TuiApp()
    app.run()