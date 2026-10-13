'''
This module provides various functions for capturing user input from the terminal. To test
the functions via an interactive demo, run this script.

* print_and_wait(): Prints and then waits for the user to press any key.
* select_option(): Allows the user to select an option from a list by using a text-based user
  interface (TUI) controlled by the arrow keys and `Enter`.
* select_folder(): Allows the user to select a folder in the file system by either using a
  text-based user interface (TUI) or by typing a folder path manually.
* select_folder_using_tui(): Allows the user to select a folder in the file system by using a
  text-based user interface (TUI) controlled by the arrow keys and `Enter`.

Author: Lino Mercado_Esquivias
'''

# import standard library & local modules
from lino_dev_tools.colors import *
import math
import os
import select
import shutil
import signal
import sys
from time import sleep
from typing import Any, Callable, TextIO

# import unix specific modules
try:
    import termios
    import tty
except ImportError as e:
    raise ImportError(
        "lino_dev_tools.utils requires the termios and tty modules " \
        "which are only available on Unix-based operating systems."
    ) from e

# import third-party modules
try:
    import readchar
except ImportError as e:
    raise ImportError(
        "lino_dev_tools.utils requires the readchar module. Install " \
        "it with: pip install readchar."
    ) from e

# public API (excludes internal helpers, classes, and legacy functions)
__all__ = [
    "print_and_wait",
    "select_option",
    "select_folder",
    "select_folder_using_tui",
]

# global variable
terminal_resized = False

def print_and_wait(*objects:            Any, 
                   sep:                 str             = ' ',
                   end:                 str             = '\n',
                   file:                TextIO          = None,
                   flush:               bool            = False
                   ) -> str:
    """
    This function prints and then waits for the user to press any key. After printing, it sets the
    terminal to raw mode, allowing it to read a single character from the standard input without the
    user needing to press the `Enter` key. It restores the terminal settings to their original state
    after reading a character.

    Parameters:
        *objects:                   The objects to print.

        sep (str):                  The seperation printed between objects.

        end (str):                  The string printed after all the objects.

        file (TextIO):              The I/O file stream to print to. Defaults to sys.stdout.

        flush (bool):               Whether to flush the buffer immediately. Defaults to false.     
        
    Returns:
        input_char (str):           The character read from the standard input.
    """

    # print
    print(*objects, sep=sep, end=end, file=file, flush=flush)

    output_stream = sys.stdout if file is None else file
    output_stream.flush()

    file_descriptor = sys.stdin.fileno()
    old_settings = termios.tcgetattr(file_descriptor)
    try:
        tty.setraw(file_descriptor)             # set terminal to raw mode
        termios.tcflush(file_descriptor, termios.TCIFLUSH)
        input_char = os.read(file_descriptor, 1).decode(errors='replace')
    finally:
        termios.tcsetattr(file_descriptor, termios.TCSADRAIN, old_settings)

    return input_char

def select_option(options:              list[Any],
                  header_message:       str                     = "Select an option from below.",
                  validation_function:  Callable[[Any], str]    = None
                  ) -> Any:
    """
    This function allows the user to select an option from a list by using a fancy text-based user
    interface (TUI).

    Parameters:
        options (list[Any]):                        The list of options to choose from.

        header_message (str):                       Header message printed at the top. Can be used to
                                                    display instructions or explain the content on the
                                                    screen.

        validation_function (Callable[[Any], str]): An optional function used to validate the user's
                                                    selection. The function must return a string upon
                                                    failure or None or emptry string on success. The
                                                    string returned is printed as an error message up
                                                    top in red.

    Returns:
        selected_option (Any):                      The selected option or `None` if the user selects
                                                    the 'Go Back' option.
    """

    # validate arguments
    if not isinstance(options, list):
        raise TypeError("options must be a list")
    for option in options:
        if type(option) == str and '\n' in option:
            raise ValueError("new line character not allowed in options")
    if len(options) < 2:
        raise ValueError("options must have two or more elements")
    if not isinstance(header_message, str):
        raise TypeError("header must be a string")
    if validation_function is not None and not callable(validation_function):
        raise TypeError("validation_function must be None or a Callable that returns a string")

    # initialize variables
    global terminal_resized
    terminal_resized = False
    file_descriptor = sys.stdin.fileno()
    old_settings = termios.tcgetattr(file_descriptor)
    error_message = ''
    key_binds = {"ARROW KEYS": "Navigate",
                 "ENTER": "Make Selection",
                 "B": "Go Back",
                 "Q": "Quit"}  
    terminal_ui = _TerminalUI(options, error_message, header_message, '', key_binds) 
    key = ''
        
    try:
        previous_handler = signal.getsignal(signal.SIGWINCH)
        signal.signal(signal.SIGWINCH, _handle_resize)
        tty.setcbreak(file_descriptor)

        while True:
            # hide cursor
            print(RESET_TERMINAL, end='')
            print(HIDE_CURSOR, end='')

            # print ui
            print(terminal_ui, end='', flush=True)

            # monitor terminal resize and key press
            key_pressed, _, _ = select.select([file_descriptor], [], [], 0.1)

            # re-render ui
            if terminal_resized:
                terminal_resized = False
                terminal_ui.render()
                continue

            # process key
            if key_pressed:
                key = _read_key(file_descriptor)
                # ignore key if terminal is too small
                if not terminal_ui.pages[terminal_ui.current_page_index].printable:
                    continue
                # arrow keys
                if terminal_ui.process_key(key):
                    terminal_ui.render()
                    continue
                # enter
                if key == readchar.key.ENTER:
                    selected_option = options[terminal_ui.current_selection]
                    if validation_function:
                        error_message = validation_function(selected_option)
                    else:
                        return selected_option
                    if not error_message: 
                        return selected_option
                    terminal_ui.error_message = error_message
                    terminal_ui.render()
                # b
                elif key.lower() == 'b':
                    return None
                # q
                elif key.lower() == 'q':
                    raise KeyboardInterrupt

    finally:
        # always restore terminal and cursor
        signal.signal(signal.SIGWINCH, previous_handler)
        termios.tcsetattr(file_descriptor, termios.TCSADRAIN, old_settings)
        print(RESET_TERMINAL, end='')

def select_folder(starting_dir:         str                     =   '',
                  header_message:       str                     =   "Select a folder from below",
                  validation_function:  Callable[[Any], str]    =   None,
                  view_hidden_folders:  bool                    =   False
                  ) -> str:
    """
    This function allows the user to select a folder in the file system by either using a fancy
    text-based user interface (TUI) or by typing a folder path manually.

    Parameters:
        starting_dir (str):                         The directory initially displayed to the user. If
                                                    none given, it defaults to user home. This 
                                                    parameter is forwarded to select_folder_using_tui().

        header_message (str):                       Header string printed at the top. Can be used to
                                                    display instructions or explain the content on the
                                                    screen. This parameter is forwarded to
                                                    select_folder_using_tui().

        validation_function (Callable[[Any], str]): An optional function used to validate the user's
                                                    selection. The function must return a string upon
                                                    failure or None or emptry string on success. The
                                                    string returned is printed as an error message up
                                                    top in red. This parameter is forwarded to
                                                    select_folder_using_tui().

        view_hidden_folders (bool):                 Whether to display hidden folders. Defaults to
                                                    `False`. This parameter is forwarded to
                                                    select_folder_using_tui().

    Returns:
        selected_folder (str):                      The path to the selected folder as a string or
                                                    `None` if the user selects the 'Go Back' option.
    """
    
    # initialize variables
    initial_header = "Would you like to type the folder path manually?"
    
    # prompt user
    while True:
        print(CLEAR_TERMINAL, end='')
        type_path_manually = select_option(["No", "Yes"], initial_header)

        # check if user cancelled
        if not type_path_manually:
            return None
        
        # select folder using a TUI
        elif type_path_manually == "No":
            selected_folder = select_folder_using_tui(starting_dir,
                                                      header_message,
                                                      validation_function,
                                                      view_hidden_folders)
            if not selected_folder:
                continue
            else:
                return selected_folder
    
        # type folder path manually
        elif type_path_manually == "Yes":
            while True:
                print(RESET_TERMINAL, end='')
                instructions = f"{DISABLE}Please enter a full valid folder path "
                instructions += f"(type {RESET+BOLD}q{RESET+DISABLE} and press enter " 
                instructions += "to quit and go back): {RESET}"
                selected_folder = input(instructions)
                if selected_folder.strip().lower() == 'q':
                    break
                if os.path.isdir(selected_folder.strip("' ")):
                    return selected_folder       

def select_folder_using_tui(starting_dir:           str                     =   '',
                            header_message:         str                     =   "Select a folder from below",
                            validation_function:    Callable[[Any], str]    =   None,
                            view_hidden_folders:    bool                    =   False
                            ) -> str:
    """
    This function allows the user to select a folder in the file system by using a fancy text-based user
    interface (TUI).

    Parameters:
        starting_dir (str):                         The directory initially displayed to the user. If
                                                    none given, it defaults to user home.

        header_message (str):                       Header string printed at the top. Can be used to
                                                    display instructions or explain the content on the
                                                    screen.

        validation_function (Callable[[Any], str]): An optional function used to validate the user's
                                                    selection. The function must return a string upon
                                                    failure or None or emptry string on success. The
                                                    string returned is printed as an error message up
                                                    top in red.

        view_hidden_folders (bool):                 Whether to display hidden folders. Defaults to
                                                    `False`.

    Returns:
        selected_folder (str):                      The path to the selected folder as a string or
                                                    `None` if the user selects the 'Go Back' option.
    """

    # validate arguments
    if not isinstance(starting_dir, str):
        raise TypeError("starting_dir must be a string")
    if not starting_dir:
        starting_dir = os.path.expanduser("~")  # better starting location I think
        # starting_dir = os.getcwd()
    if not os.path.isdir(starting_dir):
        raise NotADirectoryError(f"{starting_dir} is not a valid directory") 
    current_directory = starting_dir
    if not isinstance(header_message, str):
        raise TypeError("header_message must be a string")
    if validation_function is not None and not callable(validation_function):
        raise TypeError("validation_function must be None or a Callable that returns a string")
    if not isinstance(view_hidden_folders, bool):
        raise TypeError("view_hidden_folders must be a bool")

    # initialize variables
    global terminal_resized
    terminal_resized = False
    file_descriptor = sys.stdin.fileno()
    old_settings = termios.tcgetattr(file_descriptor)
    error_message = ''
    key = ''
    key_binds = {"ARROW KEYS": "Navigate",
                 "ENTER": "Open Folder",
                 "BACKSPACE": "Exit Folder",
                 "S": "Select Folder",
                 "B": "Go Back",
                 "Q": "Quit"}
    folders = [folder for folder in os.listdir(current_directory) 
                if os.path.isdir(os.path.join(current_directory, folder)) 
                and (view_hidden_folders or folder[0:2] != "__")]
    folders.sort()
    ui_stack = []
    ui_stack.append(_TerminalUI(folders, error_message, header_message, current_directory, key_binds))
    terminal_ui = ui_stack[-1]

    try:
        previous_handler = signal.getsignal(signal.SIGWINCH)
        signal.signal(signal.SIGWINCH, _handle_resize)
        tty.setcbreak(file_descriptor)

        while True:
            # hide cursor
            print(RESET_TERMINAL, end='')
            print(HIDE_CURSOR, end='')

            # print ui
            print(terminal_ui, end='', flush=True)

            # monitor terminal resize and key press
            key_pressed, _, _ = select.select([file_descriptor], [], [], 0.1)

            # re-render ui
            if terminal_resized:
                terminal_resized = False
                terminal_ui.render()
                continue

            # process key
            if key_pressed:
                key = _read_key(file_descriptor)
                # ignore key if terminal is too small
                if not terminal_ui.pages[terminal_ui.current_page_index].printable:
                    continue
                # arrow keys
                if terminal_ui.process_key(key):
                    continue
                # enter
                if key == readchar.key.ENTER:
                    # ignore key if there are no folders
                    if not terminal_ui.options:
                        continue
                    next_directory = os.path.join(terminal_ui.directory,
                                                    terminal_ui.options[terminal_ui.current_selection])
                    folders = [folder for folder in os.listdir(next_directory)
                               if os.path.isdir(os.path.join(next_directory, folder)) 
                               and (view_hidden_folders or folder[0:2] != "__")]
                    folders.sort()
                    ui_stack.append(_TerminalUI(folders,
                                                error_message,
                                                header_message,
                                                next_directory,
                                                key_binds))
                    terminal_ui = ui_stack[-1]
                    terminal_ui.render()
                # backspace
                elif key == '\x7f':
                    if len(ui_stack) == 1:
                        next_directory = os.path.dirname(terminal_ui.directory)
                        folders = [folder for folder in os.listdir(next_directory)
                                   if os.path.isdir(os.path.join(next_directory, folder)) 
                                   and (view_hidden_folders or folder[0:2] != "__")]
                        folders.sort()
                        ui_stack.insert(0, _TerminalUI(folders,
                                                       error_message,
                                                       header_message,
                                                       next_directory,
                                                       key_binds))
                        ui_stack.pop()
                        terminal_ui = ui_stack[-1]
                    else:
                        ui_stack.pop()
                        terminal_ui = ui_stack[-1]
                    terminal_ui.render()
                # b
                elif key.lower() == 'b':
                    return None
                # q
                elif key.lower() == 'q':
                    raise KeyboardInterrupt
                # s
                elif key.lower() == 's':
                    # ignore key if there are no folders
                    if not terminal_ui.options:
                        continue
                    selected_folder = terminal_ui.options[terminal_ui.current_selection]
                    selected_folder = os.path.join(terminal_ui.directory, selected_folder)
                    if validation_function:
                        error_message = validation_function(selected_folder)
                    else:
                        return selected_folder
                    if not error_message: 
                        return selected_folder
                    terminal_ui.error_message = error_message
                    terminal_ui.render()

    finally:
        # always restore terminal and cursor
        signal.signal(signal.SIGWINCH, previous_handler)
        termios.tcsetattr(file_descriptor, termios.TCSADRAIN, old_settings)
        print(RESET_TERMINAL, end='')

def _demo() -> None:
        """
        An interactive demo of this module's functions. Called at the bottom of this script under:
        'if __name__ == "__main__":'.

        Parameters:
            None

        Returns:
            None
        """

        try:
            while True:
                print(CLEAR_TERMINAL, end='')
                # print and wait demo
                string = "This is a demo of the `print_and_wait()` function. It simply "
                string += "prints this text and waits for you to press any key.\nPress "
                string += "any key to proceed to the next demo..."
                print_and_wait(string)

                while True:
                    # select option demo
                    string = "This is a demo of the `select_option()` function. In "
                    string += "this demo, you're not allowed to select an odd "
                    string += "number. Go ahead and try ;)"
                    nums = [i for i in range(1,48)]
                    selection = select_option(nums, string, _demo_validation_function)
                    if selection:
                        print_and_wait(f"You selected: {selection}. Press any key to proceed to the next demo...")
                    else:
                        break

                    # select folder demo
                    string = "This is a demo of the `select_folder()` function. Try "
                    string += "resizing the terminal and see what happens. Try "
                    string += "pressing `B` or `Q` and see what happens."
                    selected_folder = select_folder_using_tui('', string)
                    if selected_folder:
                        print(f"You selected the folder: {selected_folder}")
                        print_and_wait("Press any key to restart the demo...")
                        break
                    
        except KeyboardInterrupt:
            print(CLEAR_TERMINAL, end='')
            print("Demo ended.")
            exit(0)

# ------------------------------------------------------------------------------------------------------
# Helper Functions
# Used by the main functions.
# ------------------------------------------------------------------------------------------------------
def _handle_resize(signum, frame):
    """
    Helper function. Used to handle the SIGWINCH signal which signals that the terminal was resized.
    Simply sets the global variable. Other functions like select_option() and select_folder_using_tui()
    are responsible for checking when the global variable changes.

    Parameters:
        signum (int):           The number identifying the signal that triggered this handler.
                                Automatically provided by python.

        frame (FrameType):      The current stackframe at the time this handler was triggered.
                                Automatically provided by python.

    Returns:
        None
    """
    global terminal_resized
    terminal_resized = True

def _read_key(file_descriptor: int) -> str:
    """
    Helper function. Reads a keypress. In particular, it can read multi-byte escape sequences generated
    by keys like the arrow keys.

    Parameters:
        file_descriptor (int):  The file descriptor to read from.

    Returns:
        key (str):              The keypress, multi-byte or otherwise.
    """

    # read first byte
    key = os.read(file_descriptor, 1)
    # check if the first byte is an escape character
    if key == b'\x1b':
        while select.select([file_descriptor], [], [], 0.01)[0]:
            key += os.read(file_descriptor, 1)  # keep reading available bytes
    return key.decode()                         # decode bytes into a string

def _demo_validation_function(num: int) -> bool:
    """
    Demo function. Returns None if the input integer is even. Returns an error message if the integer is
    odd.
    
    Called by the select_option() function at the bottom of this script under:
    'if __name__ == "__main__":'. Runing this script runs an interactive demo of this module's
    functions. This function gives perspective developers interested in using this module an example of
    how to create a validation function for use with the select_option(), select_folder(), or
    select_folder_using_tui() functions.

    Parameters:
        num(int):               An integer selected using the select_option() function.

    Returns:
        error_message (str):    The error_message returned to the select_option() function.
    """

    if num % 2 == 0:
        return None
    else:
        return "Please select an even number"

# ------------------------------------------------------------------------------------------------------
# Legacy Functions
# Simpler and lightweight alternatives without the dynamic terminal user interface.
# ------------------------------------------------------------------------------------------------------
def select_option_simple(options:               list[Any],
                         header_message:        str                     =   "Select an option from below.",
                         visible_lines:         int                     =   15,
                         validation_function:   Callable[[Any], str]    =   None
                         ) -> Any:
    """
    Legacy function. Similar to select_option() minus the fancy terminal user interface (TUI). This
    function allows the user to select an option from a list by using a bare-bones text-based user
    interface (TUI) controlled by the `Arrow Keys` and `Enter`.

    Parameters:
        options (list[Any]):                        The list of options to choose from.

        header_message (str):                       Header message printed at the top. Can be used to
                                                    display instructions or explain the content on the
                                                    screen.

        visible_lines (int):                        Number of rows to display.

        validation_function (Callable[[Any], str]): An optional function used to validate the user's
                                                    selection. The function must return a string upon
                                                    failure or None or emptry string on success. The
                                                    string returned is printed as an error message up
                                                    top in red.

    Returns:
        selected_option (Any):                      The selected option or `None` if the user selects
                                                    the 'Go Back' option.
    """

    # validate arguments
    if not isinstance(options, list):
        raise TypeError("options must be a list")
    if len(options) < 2:
        raise ValueError("options must have two or more elements")
    for option in options:
        if type(option) == str and '\n' in option:
            raise ValueError("new line character not allowed in options")
    if not isinstance(header_message, str):
        raise TypeError("header must be a string")
    if not isinstance(visible_lines, int):
        raise TypeError("visible_lines must be an integer")
    if visible_lines < 1:
        raise ValueError("visible_lines must be positive")
    if validation_function is not None and not callable(validation_function):
        raise TypeError("validation_function must be callable or None")

    try:
        # hide cursor
        print(RESET_TERMINAL, end='')
        print(HIDE_CURSOR, end='')

        # initialize variables
        error_message = ''
        current_selection = 0
        next_selection = 0
        selection_offset = 0
        current_page = 0
        next_page = 0
        starting_index = 0
        pages = len(options)//visible_lines
        if len(options)%visible_lines != 0:
            pages += 1
        if pages > 1:
            print_footer = True
        else:
            print_footer = False
        padding = visible_lines - (len(options)%visible_lines)
        padding = padding % visible_lines # for the case len(options)%visible_lines == 0
        # window_width = shutil.get_terminal_size().columns
        window_width = 94

        while True:
            # print header and instructions
            if error_message:
                print(f"{RED+BOLD}{error_message}{RESET}")
                error_message = ''
            else:
                print(f"{DISABLE}{header_message}{RESET}")
            print(f"{DISABLE}={RESET}"*window_width)

            # check if user changed selection or page
            selection_offset = current_selection - starting_index
            if next_page != current_page:
                current_page = next_page
                starting_index = current_page * visible_lines
                current_selection = starting_index + selection_offset
                if current_selection >= len(options):
                    current_selection = len(options) - 1
                next_selection = current_selection
            elif next_selection != current_selection:
                current_selection = next_selection
                current_page = current_selection//visible_lines
                next_page = current_page
                starting_index = current_page * visible_lines

            # determine visible options
            next_starting_index = starting_index + visible_lines
            visible_options = options[starting_index:next_starting_index]

            # print visible options
            for index, option in enumerate(visible_options):
                actual_index = starting_index + index
                if actual_index == current_selection:
                    print(LIGHT_GRAY_BCKGND + str(option) + RESET)
                else:
                    print(option)
            
            # print padding on last page
            if current_page == pages-1 and padding > 0:
                for i in range(padding):
                    print()

            # print footer
            key_binds = [
                ("ARROW KEYS", " Navigate"),
                ("ENTER", " Make Selection"),
                ("B", "Go Back"),
                ("Q", " Quit")
            ]
            print(f"{DISABLE}={RESET}" * window_width)
            
            # read user input and take appropriate action
            key = readchar.readkey()
            if key == readchar.key.UP:
                next_selection = (current_selection - 1) % len(options)
            elif key == readchar.key.DOWN:
                next_selection = (current_selection + 1) % len(options)
            elif key == readchar.key.LEFT:
                next_page = (current_page - 1) % pages
            elif key == readchar.key.RIGHT:
                next_page = (current_page + 1) % pages
            elif key.lower() == 'b':
                return None
            elif key.lower() == 'q':
                raise KeyboardInterrupt
            elif key == readchar.key.ENTER:
                # validate selected option
                selected_option = options[current_selection]
                if validation_function:
                    error_message = validation_function(selected_option)
                else:
                    return selected_option
                if not error_message: 
                    return selected_option
            print(RESET_TERMINAL, end='')
            print(HIDE_CURSOR, end='')

    finally:
        # always restore cursor
        print(RESET_TERMINAL, end='')

def select_folder_simple() -> str:
    """
    Legacy function. Similar to select_folder() minus the fancy terminal user interface (TUI). This
    function allows the user to select a folder in the file system by either using a bare-bones
    text-based user interface (TUI) or by typing a folder path manually.

    Parameters:
        None

    Returns:
        selected_folder (str):      The path to the selected folder as a string or None if the
                                    user selects the cancel option.
    """
    
    # prompt user
    while True:
        print(CLEAR_TERMINAL, end='')
        header = "Select an option from below."
        type_path_manually = select_option_simple(["Type a folder path manually",
                                            "Use UI to find the folder"], 
                                            header)

        # check if user cancelled
        if not type_path_manually:
            return None
        
        # select folder using a TUI
        elif type_path_manually == "Use UI to find the folder":
            selected_folder = select_folder_using_tui_simple()
            if not selected_folder:
                continue
            else:
                return selected_folder
    
        # type folder path manually
        elif type_path_manually == "Type a folder path manually":
            while True:
                print(RESET_TERMINAL, end='')
                instructions = f"{DISABLE}Please enter a full valid folder path "
                instructions += f"(press {RESET+BOLD}q{RESET+DISABLE} to quit and go back): {RESET}"
                selected_folder = input(instructions)
                if selected_folder.strip().lower() == 'q':
                    break
                if os.path.isdir(selected_folder.strip("' ")):
                    return selected_folder       

def select_folder_using_tui_simple(starting_dir:            str                     =   '',
                                   visible_lines:           int                     =   15,
                                   validation_function:     Callable[[Any], str]    =   None
                                   ) -> str:
    """
    Legacy function. Similar to select_folder() minus the fancy terminal user interface (TUI). This
    function allows the user to select a folder in the file system by using a bare-bones text-based
    user interface (TUI).

    Parameters:
        starting_dir (str):                         The directory initially displayed to the user. If
                                                    none given, it defaults to user home.

        visible_lines (int):                        Number of rows to display on the terminal.

        validation_function (Callable[[Any], str]): An optional function used to validate the user's
                                                    selection. The function must return a string upon
                                                    failure or None or emptry string on success. The
                                                    string returned is printed as an error message up
                                                    top in red.

    Returns:
        selected_folder (str):                      The path to the selected folder as a string or
                                                    `None` if the user selects the 'Go Back' option.
    """

    # validate arguments
    if not isinstance(starting_dir, str):
        raise TypeError("starting_dir must be a string")
    if not starting_dir:
        starting_dir = os.path.expanduser("~")
    if not os.path.isdir(starting_dir):
        raise NotADirectoryError(f"Not a valid directory: {starting_dir}") 
    current_directory = starting_dir
    if not isinstance(visible_lines, int):
        raise TypeError("visible_lines must be an intiger")
    if visible_lines < 1:
        raise ValueError("visible_lines must be positive")

    try:
        while True:
            # hide cursor
            print(RESET_TERMINAL, end='')
            print(HIDE_CURSOR, end='')

            # initialize variables
            error_message = ''
            current_selection = 0
            next_selection = 0
            selection_offset = 0
            current_page = 0
            next_page = 0
            window_start = 0
            # get folders in the current directory
            folders = [folder for folder in os.listdir(current_directory) 
                        if os.path.isdir(os.path.join(current_directory, folder)) 
                        and folder[0:2] != "__"]
            folders.sort()
            pages = len(folders)//visible_lines
            if len(folders)%visible_lines != 0:
                pages += 1
            if pages > 1:
                print_page_index = True
            else:
                print_page_index = False
            padding = visible_lines - (len(folders)%visible_lines)
            padding = padding % visible_lines # for the case len(folders)%visible_lines == 0
            # window_width = shutil.get_terminal_size().columns
            window_width = 94

            while True:
                # print header and instructions
                if error_message:
                    print(f"{RED+BOLD}{error_message}{RESET+DISABLE}")
                    error_message = ''
                # print(f"Current folder: {BOLD+UNDERLINE+current_directory+RESET+DISABLE}")
                print(f"{DISABLE}Current folder:{RESET} ", end='')
                split_directory = current_directory
                while len(split_directory) > window_width-17:
                    split_index = split_directory.rfind('/', 0, window_width-17)

                    if split_index == -1:
                        break

                    print(BOLD+UNDERLINE+split_directory[:split_index + 1])
                    split_directory = split_directory[split_index + 1:]

                print(BOLD+UNDERLINE+split_directory+RESET)
                print(f"{DISABLE}={RESET}"*window_width)

                # check if user changed selection or page
                selection_offset = current_selection - window_start
                if next_page != current_page:
                    current_page = next_page
                    window_start = current_page * visible_lines
                    current_selection = window_start + selection_offset
                    if current_selection >= len(folders):
                        current_selection = len(folders) - 1
                    next_selection = current_selection
                elif next_selection != current_selection:
                    current_selection = next_selection
                    current_page = current_selection//visible_lines
                    next_page = current_page
                    window_start = current_page * visible_lines

                # determine visible folders
                next_window_start = window_start + visible_lines
                visible_folders = folders[window_start:next_window_start]

                # print visible folders
                for index, folder in enumerate(visible_folders):
                    actual_index = window_start + index
                    if actual_index == current_selection:
                        print(LIGHT_GRAY_BCKGND + str(folder) + RESET)
                    else:
                        print(folder)

                # print padding on last page
                if current_page == pages-1 and padding > 0:
                    for i in range(padding):
                        print()
                elif len(folders) == 0:
                    for i in range(visible_lines):
                        print()
                
                # print footer
                key_binds = [
                    ("ARROW KEYS", " Navigate"),
                    ("ENTER", " Open Folder"),
                    ("BACKSPACE", " Back One Folder"),
                    ("S", " Select Folder"),
                    ("B", " Go Back"),
                    ("Q", " Quit")
                ]
                print(f"{DISABLE}={RESET}" * window_width)
                
                # read user input and take appropriate action
                key = readchar.readkey()
                if key == readchar.key.UP and len(folders) > 0:
                    next_selection = (current_selection - 1) % len(folders)
                elif key == readchar.key.DOWN and len(folders) > 0:
                    next_selection = (current_selection + 1) % len(folders)
                elif key == readchar.key.LEFT and pages > 0:
                    next_page = (current_page - 1) % pages
                elif key == readchar.key.RIGHT and pages > 0:
                    next_page = (current_page + 1) % pages
                elif key == readchar.key.ENTER and len(folders) > 0:
                    current_directory = os.path.join(current_directory, folders[current_selection])
                    print(RESET_TERMINAL, end='')
                    print(HIDE_CURSOR, end='')
                    break
                elif key == '\x7f':     # backspace
                    current_directory = os.path.dirname(current_directory)
                    break
                elif key.lower() == 'b':
                    return None
                elif key.lower() == 'q':
                    raise KeyboardInterrupt
                elif key.lower() == 's' and len(folders) > 0:
                    # validate selected folder
                    selected_folder = os.path.join(current_directory, folders[current_selection])
                    if validation_function:
                        error_message = validation_function(selected_folder)
                    else:
                        return selected_folder
                    if not error_message: 
                        return selected_folder
                print(RESET_TERMINAL, end='')
                print(HIDE_CURSOR, end='')
    finally:
        # always restore cursor
        print(RESET_TERMINAL, end='')

# ------------------------------------------------------------------------------------------------------
# Terminal User Interface Classes
# Classes that define the behavior of the TUI at the heart of this module's functions.
# ------------------------------------------------------------------------------------------------------
class _Header:
    def __init__(self,
                 terminal_width:        int,
                 error_message:         str     = '',
                 header_message:        str     = "Select an option from below",
                 directory:             str     = '',
                 print_header_on_error: bool    = True
                 ) -> None:
        """
        Constructs a Header object.

        Parameters:
            terminal_width (int):               The character width of the terminal.

            error_message (str):                The message printed when an error occurs.

            header_message (str):               The header message printed at the top. Can be used to
                                                display instructions or explain the content on the
                                                screen.

            directory (str):                    Optional string used to print the current directory.
                                                Used by the functions select_folder() and
                                                select_folder_using_tui().

            print_header_on_error (bool):       Whether to also print the header message when there is 
                                                an error message. Defaults to True.
            
        Returns:
            None
        """

        self.terminal_width = terminal_width
        self.error_message = error_message
        self.header_message = header_message
        self.directory = directory
        self.print_header_on_error = print_header_on_error
        self.divider_line = '=' * terminal_width
        self.header = ''
        self.height = 0
        self.render_header()

    def render_header(self) -> None:
        """
        Renders the header and saves it into the string variable self.header. Also calculates
        self.height.

        Parameters:
            self
            
        Returns:
            None
        """

        # initialize variables
        self.header = ''
        self.height = 0

        # render error message
        self.header += BOLD + RED + self.error_message + RESET + '\n'
        self.height += max(1, math.ceil(len(self.error_message) / self.terminal_width))

        # render header message
        if self.error_message and not self.print_header_on_error:
            self.header += '\n'
            self.height += 1
        else:
            self.header += self.header_message + '\n'
            self.height += sum(max(1, math.ceil(len(line) / self.terminal_width))
                                   for line in self.header_message.split('\n'))

        # render directory
        if self.directory:
            directory_line = f"{DISABLE}Current folder:{RESET} "
            split_directory = self.directory
            while len(split_directory) > self.terminal_width - 19:
                split_index = split_directory.rfind('/', 0, self.terminal_width - 19)

                if split_index == -1:
                    break

                directory_line += BOLD + UNDERLINE + split_directory[:split_index + 1] + '\n'
                split_directory = split_directory[split_index + 1:]
                self.height += 1

            directory_line += BOLD + UNDERLINE + split_directory + RESET + '\n'
            self.height += 1
            self.header += directory_line

        # render divider line
        self.header += self.divider_line
        self.height += 1

    def __str__(self) -> str:
        """
        Returns the string variable self.header.

        Parameters:
            self
            
        Returns:
            self.header (str):          The rendered header saved as a string.
        """
        return self.header

class _BodyRow:
    def __init__(self,
                 content:               str,
                 starting_page_index:   int,
                 height:                int,
                 list_index:            int
                 ) -> None:
        """
        Constructs a BodyRow object.

        Parameters:
            content (str):                      The string to be printed on this row.

            starting_page_index (int):          The local index of this row within the current page.
                                                This is only the starting index, the row may still take
                                                up multiple physical rows on the terminal.

            height (int):                       The number of physical rows on the terminal this row
                                                takes up.

            list_index (int):                   The absolute index of this row within the entire list of 
                                                rows across all terminal pages.
            
        Returns:
            None
        """

        self.content = content
        self.page_index = list(range(starting_page_index, starting_page_index+height))
        self.list_index = list_index

    def __str__(self) -> str:
        """
        Returns the string variable self.content.

        Parameters:
            self
            
        Returns:
            self.content (str):         The row content.
        """
        return self.content
    
class _Body:
    def __init__(self,
                 rows:                  list[_BodyRow],
                 remaining_body_height: int
                 ) -> None:
        """
        Constructs a Body object.

        Parameters:
            rows (list[_BodyRow]):              The list of rows that make up the body.

            remaining_body_height (int):        The integer used to add padding if the number of rows
                                                doesn't take up the whole terminal's height.
            
        Returns:
            None
        """
        
        self.rows = rows
        self.remaining_body_height = remaining_body_height
        first = rows[0].list_index
        last = rows[-1].list_index
        self.list_index_range = range(first, last + 1)

    def __str__(self) -> str:
        """
        Returns the content of every row in the body as one big string. This method isn't actually
        used since the render() method in the TerminalUI class defaults to use the __str__() method in
        the BodyRow class instead. This method is still here because why not right?

        Parameters:
            self
            
        Returns:
            row_contents (str):         The new line seperated rows as one big string.
        """
       
        row_contents = '\n'.join(row.content for row in self.rows)
        row_contents += '\n' * self.remaining_body_height
        return row_contents

class _Footer:
    def __init__(self,
                 terminal_width:    int,
                 key_binds:         dict,
                 current_page:      int     = 0,
                 page_count:        int     = 1,
                 print_index:       bool    = True,
                 sep_length:        int     = 4
                 ) -> None:
        """
        Constructs a Footer object.

        Parameters:
            terminal_width (int):               The character width of the terminal.

            key_binds (dict):                   The strings explaining how to navigate the TUI. Example
                                                key binds:  {"ARROW KEYS" : "Navigate",
                                                            "ENTER" : "Make Selection",
                                                            "B" : "Go Back",
                                                            "Q" : "Quit"}}
            
            current_page (int):                 The current page number (0 indexed).

            page_count (int):                   The total number of pages.

            print_index (bool):                 Whether to print the page index "Page x/y".

            sep_length (int):                   The space between each key bind.
            
        Returns:
            None
        """

        self.terminal_width = terminal_width
        self.key_binds = key_binds
        self.current_page = current_page + 1
        self.page_count = page_count
        self.print_index = print_index
        self.sep_length = sep_length
        self.footer = ''
        self.height = 0
        self.divider_line = '=' * terminal_width
        self.index = f"(Page {self.current_page}/{page_count})"
        self.print_index_first = False
        self.render_footer()

    def render_footer(self) -> None:
        """
        Renders the footer and saves it into the string variable self.footer. Also calculates
        self.height.

        Parameters:
            self
            
        Returns:
            None
        """

        # initialize variables
        footer_lines = [self.divider_line]
        separator = ' ' * self.sep_length
        key_binds = []
        for key, value in self.key_binds.items():
            plain = key + ' ' + value
            formatted = BOLD + UNDERLINE + DISABLE + key + RESET + ' ' + DISABLE + value + RESET
            key_binds.append([plain, formatted])
        key_binds_length = (sum(len(plain) for plain,_ in key_binds)
                                    + self.sep_length * len(key_binds) - 1)
        
        # handle case when index is printed first
        if self.print_index:
            total_footer_length = (key_binds_length+ self.sep_length + len(self.index))
            if total_footer_length > self.terminal_width:
                self.print_index_first = True
                footer_lines.append(self.index.rjust(self.terminal_width))

        # build key bind lines
        key_bind_lines = []
        for plain, formatted in key_binds:
            # append first key bind
            if not key_bind_lines:
                key_bind_lines.append([plain, formatted])
                continue

            # calculate the space the key bind takes up
            required_space = self.sep_length + len(plain)

            # add key bind to current line if it fits
            if len(key_bind_lines[-1][0]) + required_space <= self.terminal_width:
                key_bind_lines[-1][0] += separator + plain
                key_bind_lines[-1][1] += separator + formatted
            # otherwise add key bind to new line
            else:
                key_bind_lines.append([plain, formatted])

        # handle case when index is printed last
        if self.print_index and not self.print_index_first:
            available_space = self.terminal_width - len(key_bind_lines[-1][0])
            if available_space >= len(self.index):
                key_bind_lines[-1][0] += self.index.rjust(available_space)
                key_bind_lines[-1][1] += self.index.rjust(available_space)
            else:
                key_bind_lines.append([self.index.rjust(self.terminal_width),
                                       self.index.rjust(self.terminal_width)])

        # build footer
        footer_lines.extend(formatted for _,formatted in key_bind_lines)
        self.height = len(footer_lines)
        self.footer = '\n'.join(footer_lines)

    def __str__(self) -> str:
        """
        Returns the string variable self.footer.

        Parameters:
            self
            
        Returns:
            self.footer (str):          The rendered footer saved as a string.
        """
        return self.footer

class _TerminalPage:
    def __init__(self,
                 header:    _Header,
                 body:      _Body,
                 footer:    _Footer,
                 printable: bool
                 ) -> None:
        """
        Constructs a TerminalPage object.

        Parameters:
            header (Header):                Page header.

            body (Body):                    Page body.

            footer (Footer):                Page footer.

            printable (bool):               Whether the page is printable. False when the body doesn't
                                            fit given the current heights of: terminal, header, and
                                            footer.

        Returns:
            None
        """
        
        self.header = header
        self.body = body
        self.footer = footer
        self.printable = printable

class _TerminalUI:
    def __init__(self,
                 options:               list[Any],
                 error_message:         str         = '',
                 header_message:        str         = "Select an option from below",
                 directory:             str         = '',
                 key_binds:             dict        = {"ARROW KEYS" : "Navigate",
                                                       "ENTER" : "Make Selection",
                                                       "B" : "Go Back",
                                                       "Q" : "Quit"},
                 print_header_on_error: bool        = True,
                 ) -> None:
        """
        Constructs a TerminalUI object.

        Parameters:
            options (list[Any]):                The list of options to choose from.

            error_message (str):                The message printed when an error occurs.

            header_message (str):               The header message printed at the top. Can be used to
                                                display instructions or explain the content on the
                                                screen.

            directory (str):                    Optional string used to print the current directory.
                                                Used by the functions select_folder() and
                                                select_folder_using_tui().

            key_binds (dict):                   The strings explaining how to navigate the TUI. Example
                                                key binds:  {"ARROW KEYS" : "Navigate",
                                                            "ENTER" : "Make Selection",
                                                            "B" : "Go Back",
                                                            "Q" : "Quit"}}

            print_header_on_error (bool):       Whether to also print the header message when there is 
                                                an error message. Defaults to True.
            
        Returns:
            None
        """
        
        # validate argument
        if not isinstance(options, list):
            raise TypeError("options must be a list")
        for option in options:
            if type(option) == str and '\n' in option:
                raise ValueError("new line character not allowed in options")
        
        self.options = options
        self.error_message = error_message
        self.header_message = header_message
        self.directory = directory
        self.key_binds = key_binds
        self.print_header_on_error = print_header_on_error
        self.pages = []
        self.current_page_index = 0
        self.current_selection = 0
        self.warning = RED + BOLD + "WARNING: The terminal is too "
        self.warning += "short. Please resize to view the content." + RESET
        self.render()

    def render(self) -> None:
        """
        Renders the terminal and saves it into self.pages. 
        
        Importantly, this method may perform up to two sequential renders due to the fact that there is
        a circular dependence between the body and footer. The body needs to know how big the footer is
        in order to render and vice versa. The values settle after two renders if not one. This is the
        price paid for the beautiful and dynamic way the footer reacts to the terminal width. :)

        Parameters:
            self
            
        Returns:
            None
        """

        # check for edge selections before rendering
        selection_first = False
        selection_last = False
        if self.pages:      # if this is not the 1st render and pages exist
            body = self.pages[self.current_page_index].body
            selection_first = self.current_selection == body.rows[0].list_index
            selection_last = self.current_selection == body.rows[-1].list_index

        # estimate page count and page size
        terminal_width, terminal_height = shutil.get_terminal_size()
        estimated_body_height, estimated_footer_height, estimated_page_count = self._estimate_size(terminal_width,
                                                                                                  terminal_height)
        # first render
        re_render = self._render_pass(terminal_width,
                                      estimated_body_height,
                                      estimated_footer_height,
                                      estimated_page_count)

        # second render
        if re_render:
            actual_page_count = len(self.pages)
            self._render_pass(terminal_width,
                              estimated_body_height,
                              estimated_footer_height,
                              actual_page_count)

        # handle edge selections after rendering
        # (this occurs when resizing so fast that the selection moves to another page)
        body = self.pages[self.current_page_index].body
        if selection_first:
            self.current_selection = body.rows[0].list_index
        elif selection_last:
            self.current_selection = body.rows[-1].list_index
        elif self.current_selection < body.rows[0].list_index:
            self.current_selection = body.rows[0].list_index
        elif self.current_selection > body.rows[-1].list_index:
            self.current_selection = body.rows[-1].list_index
                
    def _estimate_size(self,
                       terminal_width:  int,
                       terminal_height: int
                       ) -> tuple[int,int,int]:
        """
        Estimates the size of the terminal given the current terminal width and height.
        
        Importantly, this method may perform up to two sequential renders due to the fact that there is
        a circular dependence between the body and footer. The body needs to know how big the footer is
        in order to render and vice versa. The values settle after two renders if not one. This is the
        price paid for the beautiful and dynamic way the footer reacts to the terminal width. :)

        Parameters:
            terminal_width (int):               The character width of the terminal.

            terminal_height (int):              The character height of the terminal.
            
        Returns:
            (tuple[int,int,int]):               The following three values:
                                                estimated_body_height
                                                estimated_footer_height
                                                estimated_page_count
        """
        
        dummy_header = _Header(terminal_width,
                               self.error_message,
                               self.header_message,
                               self.directory,
                               self.print_header_on_error)
        dummy_footer = _Footer(terminal_width, self.key_binds)
        estimated_header_height = dummy_header.height
        estimated_footer_height = dummy_footer.height
        estimated_body_height = terminal_height - estimated_header_height - estimated_footer_height
        # avoid dividing by zero
        if estimated_body_height == 0:
            estimated_page_count = 1
        else:
            estimated_page_count = max(1, math.ceil(len(self.options) / estimated_body_height))
        return estimated_body_height, estimated_footer_height, estimated_page_count

    def _render_pass(self,
                     terminal_width:            int,
                     estimated_body_height:     int,
                     estimated_footer_height:   int,
                     estimated_page_count:      int
                     ) -> bool:
        """
        Performs one pass in the render sequence in the render() method.

        Parameters:            
            terminal_width (int):               The character width of the terminal.

            estimated_body_height (int):        The estimated height of the body.

            estimated_footer_height (int):      The estimated height of the footer.

            estimated_page_count (int):         The estimated total number of pages.
            
        Returns:
            re_render (bool):                   Whether to re-render or not. Set to `True` when the
                                                current page count > estimated page count.
        """

        # variables
        MIN_BODY_HEIGHT = 1
        if estimated_page_count > 1:
            print_index = True
        else:
            print_index = False
        re_render = False
        self.pages =[]
        current_page_index = 0
        current_page_rows = []
        current_row_index = 0
        remaining_body_height = estimated_body_height
        header = _Header(terminal_width,
                         self.error_message,
                         self.header_message,
                         self.directory,
                         self.print_header_on_error)
        footer = _Footer(terminal_width, self.key_binds, current_page_index, estimated_page_count, print_index)
        remaining_body_height -= footer.height - estimated_footer_height
        # printable value for all pages
        if remaining_body_height >= MIN_BODY_HEIGHT:
            printable = True
        else:
            printable = False

        # handle terminal that is too small
        if estimated_body_height <= 0:
            for i in range(5):
                current_page_rows.append(_BodyRow('', i, 1, i))
            self.pages.append(_TerminalPage(header,
                                            _Body(current_page_rows, 0),
                                            footer,
                                            False))
            self.current_page_index = 0
            return False
        
        # handle empty options list
        if not self.options:
            for i in range(1):
                current_page_rows.append(_BodyRow('', i, 1, i))
            self.pages.append(_TerminalPage(header,
                                            _Body(current_page_rows, remaining_body_height-1),
                                            footer,
                                            printable))
            return re_render

        # render pages
        for index, option in enumerate(self.options):
            # check if re-render is necessary
            if current_page_index + 1 > estimated_page_count:
                re_render = True
            
            # reset row variables
            current_row = ''
            current_row_height = 0
            string_option = str(option)
            current_row += string_option
            current_row_height += max(1, math.ceil(len(string_option) / terminal_width))

            # case when current row fits on the page (append row)
            if remaining_body_height - current_row_height >= 0:
                current_page_rows.append(_BodyRow(current_row, current_row_index, current_row_height, index))
                current_row_index += current_row_height
                remaining_body_height -= current_row_height
            # case when current row cropped fits on the page (append cropped row)
            elif remaining_body_height != 0:
                # finish current page
                cropped_row_height = remaining_body_height
                cropped_row_length = cropped_row_height * terminal_width
                current_row = current_row[:cropped_row_length]
                current_page_rows.append(_BodyRow(current_row, current_row_index, cropped_row_height, index))
                self.pages.append(_TerminalPage(header,
                                                _Body(current_page_rows, 0),
                                                footer,
                                                printable))
                # reset page variables
                current_page_index += 1
                current_page_rows = []
                current_row_index = 0
                remaining_body_height = estimated_body_height
                footer = _Footer(terminal_width,
                                 self.key_binds,
                                 current_page_index,
                                 estimated_page_count,
                                 print_index)
                remaining_body_height -= footer.height - estimated_footer_height
                if remaining_body_height >= MIN_BODY_HEIGHT:
                    printable = True
                else:
                    printable = False
            # case when current row fits on next page (page full)
            else:
                # finish current page
                self.pages.append(_TerminalPage(header,
                                                _Body(current_page_rows, remaining_body_height),
                                                footer,
                                                printable))
                # reset page variables
                current_page_index += 1
                current_page_rows = []
                current_row_index = 0
                remaining_body_height = estimated_body_height
                footer = _Footer(terminal_width,
                                 self.key_binds,
                                 current_page_index,
                                 estimated_page_count,
                                 print_index)
                remaining_body_height -= footer.height - estimated_footer_height
                if remaining_body_height >= MIN_BODY_HEIGHT:
                    printable = True
                else:
                    printable = False
                # append row to next page
                current_page_rows.append(_BodyRow(current_row, current_row_index, current_row_height, index))
                current_row_index += current_row_height
                remaining_body_height -= current_row_height

        if current_page_rows:
            # check if re-render is necessary
            if current_page_index + 1 > estimated_page_count:
                re_render = True
            self.pages.append(_TerminalPage(header,
                                            _Body(current_page_rows, remaining_body_height),
                                            footer,
                                            printable))

        return re_render

    def process_key(self, key) -> bool:
        """
        Processes a key press and takes the appropriate action. This method only processes arrow keys
        used for navigation. Keys like `Enter`, `Backspace`, and character keys are processed by the
        calling function that defines its own custom behavior such as select_option() and
        select_folder_using_tui().

        Parameters:
            key (str):              The key pressed.
            
        Returns:
            (bool):                 Whether the method successfully processed the key or not. Important
                                    for the calling function since only the arrow keys are processed
                                    by this method.
        """

        # return if there are no options to print
        if not self.options:
            return False

        # handle unprintable pages
        if not self.pages[self.current_page_index].printable:
            return False
        
        # up
        if key == readchar.key.UP:
            option_count = len(self.options)
            self.current_selection = (self.current_selection-1) % option_count
            if self.current_selection not in self.pages[self.current_page_index].body.list_index_range:
                self.current_page_index = (self.current_page_index - 1) % len(self.pages)
            self.render()
            return True

        # down
        elif key == readchar.key.DOWN:
            option_count = len(self.options)
            self.current_selection = (self.current_selection+1) % option_count
            if self.current_selection not in self.pages[self.current_page_index].body.list_index_range:
                self.current_page_index = (self.current_page_index + 1) % len(self.pages)
            self.render()
            return True

        # left
        elif key == readchar.key.LEFT:
            # find page index (relative) for current selection
            for row in self.pages[self.current_page_index].body.rows:
                if row.list_index == self.current_selection:
                    page_index = row.page_index[0]
            # update page number
            self.current_page_index = (self.current_page_index - 1) % len(self.pages)
            # find list index (absolute) for next selection
            next_page_rows = self.pages[self.current_page_index].body.rows
            self.current_selection = next_page_rows[-1].list_index
            for row in next_page_rows:
                if page_index in row.page_index:
                    self.current_selection = row.list_index
            self.render()
            return True

        # right
        elif key == readchar.key.RIGHT:
            # find page index (relative) for current selection
            for row in self.pages[self.current_page_index].body.rows:
                if row.list_index == self.current_selection:
                    page_index = row.page_index[0]
            # update page number
            self.current_page_index = (self.current_page_index + 1) % len(self.pages)
            # find list index (absolute) for next selection
            next_page_rows = self.pages[self.current_page_index].body.rows
            self.current_selection = next_page_rows[-1].list_index
            for row in next_page_rows:
                if page_index in row.page_index:
                    self.current_selection = row.list_index
            self.render()
            return True

        return False

    def __str__(self) -> str:
        """
        Returns the string representation of the current terminal page indicated by
        self.current_page_index. If the terminal is too small to print the current page, a warning
        message is returned instead.

        Parameters:
            None
            
        Returns:
            (str):          The fully rendered current page as one big string.
        """

        # handle small terminal
        if not self.pages[self.current_page_index].printable:
            return self.warning
        
        # assemble header lines
        string = str(self.pages[self.current_page_index].header) + '\n'

        # assemble body lines
        for row in self.pages[self.current_page_index].body.rows:
            if row.list_index == self.current_selection:
                string += LIGHT_GRAY_BCKGND + row.content + RESET + '\n'
            else:
                string += row.content + '\n'
        string += '\n' * self.pages[self.current_page_index].body.remaining_body_height

        # assemble footer lines
        string += str(self.pages[self.current_page_index].footer)

        return string

if __name__ == "__main__":
    _demo()