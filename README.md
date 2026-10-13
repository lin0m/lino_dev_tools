## About This Package

This package is a collection of developer tools used for programming in Python. The tools are classified into three categories:

| Module | Description |
| ---- | --- |
| colors | ANSI color and formatting |
| logs | Logging capabilities |
| utils | Functions that use powerful terminal-based user interface (TUI) for interacting with the user |

The modules provided in this package can improve your already-built Python projects and make them easier to use. With time, you'll grow so accustomed to using this package that you'll always import it at the top of your scripts. If you're unsure, just download and run! The modules have built-in demo scripts that run when you simply run the modules.

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