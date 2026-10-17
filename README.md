## About This Package

This package is a collection of developer tools used for programming in Python. The tools are classified into three categories:

| Module | Description |
| ---- | --- |
| colors | ANSI color and formatting |
| logs | Logging capabilities |
| utils | Functions that use powerful terminal-based user interface (TUI) for interacting with the user |

The modules provided in this package can improve your already-built Python projects and make them easier to use. With time, you'll grow so accustomed to using this package that you'll always import it at the top of your scripts. If you're unsure, just download and run! The modules have built-in demo scripts that run when you simply run the modules.

## Terminal UI Demo
The TUI is implemented from scratch without relying on UI frameworks or libraries such as Tkinter, textual, or curses. Rendering, layout, pagination, and keyboard input is all implemented manually.

The key binds and page index at the bottom re-arrange based on the terminal width.
![Terminal UI resizing demo 1 gif](https://raw.githubusercontent.com/lin0m/repository_assets/main/lino_dev_tools/terminal_ui_resize_demo_1.gif)

The visible content and number of pages adjusts based on the terminal height.
![Terminal UI resizing demo 2 gif](https://raw.githubusercontent.com/lin0m/repository_assets/main/lino_dev_tools/terminal_ui_resize_demo_2.gif)

When the terminal is too short, a warning is displayed and keyboard inputs are ignored to avoid unintentional commands.
![Terminal UI resizing demo 3 gif](https://raw.githubusercontent.com/lin0m/repository_assets/main/lino_dev_tools/terminal_ui_resize_demo_3.gif)

Custom validation functions and in-line error messages are supported.
![Terminal UI validation demo gif](https://raw.githubusercontent.com/lin0m/repository_assets/main/lino_dev_tools/terminal_ui_validation_demo.gif)

## Installation

### Requirements:

- Python 3.13 or newer
- macOS

### Dependencies:

- readchar >= 4.0.0

All required dependencies are automatically installed by pip.

Install the package directly from GitHub using pip:

```bash
$ python3 -m pip install git+https://github.com/lin0m/lino_dev_tools.git
```

Alternatively, clone the repository and install it locally:

```bash
$ git clone https://github.com/lin0m/lino_dev_tools.git
$ cd lino_dev_tools
$ python3 -m pip install .
```

Once installed, the package modules can be imported into your Python scripts:

```bash
from lino_dev_tools import colors, logs, utils
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.