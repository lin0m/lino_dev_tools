'''
This module provides easy to use logging functionality. It is essentially a wrapper
around python's logging module for simplified logging with none of the fuzz.

* log = Log(): Returns a ready to use log. The log will be saved in the directory
  '/logs/application.log'.
* log.write(): Writes to the log file.
* log.read(): Returns all log entries as a LogEntries object.
* log.new_session(): Creates a new log session.

Author: Lino Mercado_Esquivias
'''

# import standard library & local modules
from datetime import date, datetime, time, timedelta
import json
from lino_dev_tools.colors import *
from lino_dev_tools.utils import select_option, select_options
import logging
import os
from typing import Any, Callable

# re-export logging module constants for ease of use
DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL
VALID_LEVELS = [DEBUG, INFO, ERROR, WARNING, CRITICAL]
LEVEL_TO_INT = {"DEBUG":DEBUG,"INFO":INFO,"WARNING":WARNING,"ERROR":ERROR,"CRITICAL":CRITICAL}
LEVEL_TO_STR = {DEBUG:"DEBUG",INFO:"INFO",WARNING:"WARNING",ERROR:"ERROR",CRITICAL:"CRITICAL"}

class LogEntry:
    def __init__(self,
                 date:              datetime,
                 level:             int,
                 script:            str,
                 function:          str,
                 session_number:    int,
                 entry_number:      int,
                 reference_number:  int,
                 message:           str
                 ) -> None:
        """
        Constructs a LogEntry object.

        Parameters:
            date (datetime):            The date the entry was created in the following format:
                                        1999-12-31 11:59:59 PM
                                        (%Y-%m-%d %I:%M:%S %p).

            level (int):                The severity level of the entry. Restricted to one of the
                                        following constants: DEBUG, INFO, WARNING, ERROR, or
                                        CRITICAL.

            script (str):               The script responsible for creating the entry.

            function (str):             The function responsible for creating the entry.

            session_number (int):       The session responsible for creating the entry.

            entry_number (int):         The number assigned to the entry.

            reference_number (int):     The entry number of a related entry.

            message (str):              The entry message.

        Returns:
            None
        """
        
        self.date = date
        self.level = level
        self.script = script
        self.function = function
        self.session_number = session_number
        self.entry_number = entry_number
        self.reference_number = reference_number
        self.message = message

    def __str__(self) -> str:
        """
        Returns the LogEntry as a string.

        Parameters:
            None

        Returns:
            string_entry (str):         LogEntry as a string.
        """

        string_entry = f"DATE: {self.date} | "
        string_entry += f"LEVEL: {self.level} | "
        string_entry += f"SCRIPT: {self.script} | "
        string_entry += f"FUNCTION: {self.function} | "
        string_entry += f"SESSION#: {self.session_number} | "
        string_entry += f"ENTRY#: {self.entry_number} | "
        string_entry += f"REFERENCE#: {self.reference_number} | "
        string_entry += f"MESSAGE: {self.message}"

        return string_entry
        
    def to_string(self,
                  delimiter:                str = '|',
                  include_date:             bool = True,
                  include_level:            bool = True,
                  include_script:           bool = True,
                  include_function:         bool = True,
                  include_session_number:   bool = True,
                  include_entry_number:     bool = True,
                  include_reference_number: bool = True,
                  include_message:          bool = True
                  ) -> str:
        """
        Returns the LogEntry as a string. Optional parameters determine what fields are included in the
        string. Be careful when removing fields! In order to turn a string back into a LogEntry using
        the to_log_entry() function, all eight fields must be present in the string! The to_log_entry()
        function can safely handle any delimiter though.

        Parameters:
            delimiter (str):                        The delimiter between each field. One character
                                                    long. Space is added before and after automatically.

            include_date (bool):                    Whether to include the date field in the string.

            include_level (bool):                   Whether to include the level field in the
                                                    string.

            include_script (bool):                  Whether to include the script field in the
                                                    string.

            include_function (bool):                Whether to include the function field in the
                                                    string.

            include_session_number (bool):          Whether to include the session number field in
                                                    the string.

            include_entry_number (bool):            Whether to include the entry number field in the
                                                    string.

            include_reference_number (bool):        Whether to include the reference number field in
                                                    the string.

            include_message (bool):                 Whether to include the message field in the
                                                    string.

        Returns:
            string_entry (str):                     LogEntry as a string.
        """

        # validate arguments
        if not isinstance(delimiter, str):
            raise TypeError("delimiter must be a string")
        if len(delimiter) != 1:
            raise ValueError("delimiter must be exactly one character long")
        arguments_to_validate = {
            "include_date": include_date,
            "include_level": include_level,
            "include_script": include_script,
            "include_function": include_function,
            "include_session_number": include_session_number,
            "include_entry_number": include_entry_number,
            "include_reference_number": include_reference_number,
            "include_message": include_message
            }
        
        for argument_name, argument_value in arguments_to_validate.items():
            if not isinstance(argument_value, bool):
                raise TypeError(f"'{argument_name}' must be a bool")
        
        # construct string
        field_value_pairs = []
        
        if include_date:
            field_value_pairs.append(f"DATE: {self.date}")
        if include_level:
            field_value_pairs.append(f"LEVEL: {LEVEL_TO_STR[self.level]}")
        if include_script:
            field_value_pairs.append(f"SCRIPT: {self.script}")
        if include_function:
            field_value_pairs.append(f"FUNCTION: {self.function}")
        if include_session_number:
            field_value_pairs.append(f"SESSION#: {self.session_number:06}")
        if include_entry_number:
            field_value_pairs.append(f"ENTRY#: {self.entry_number:06}")
        if include_reference_number:
            field_value_pairs.append(f"REFERENCE#: {self.reference_number:06}")
        if include_message:
            field_value_pairs.append(f"MESSAGE: {self.message}")

        string_entry = f" {delimiter} ".join(field_value_pair for field_value_pair in field_value_pairs)

        return string_entry

class LogEntries:
    def __init__(self, log_entries: list[LogEntry]) -> None:
        """
        Constructs a LogEntries object.

        Parameters:
            log_entries (list[LogEntry]):       A list of LogEntry objects.

        Returns:
            None
        """
        self.entries = log_entries

    def dates(self) -> list[date]:
        """
        Returns a list of dates for which there exist log entries. The list is sorted from newest to
        oldest date.

        Parameters:
            None

        Returns:
            None
        """

        dates = {entry.date.date() for entry in self.entries}

        # when printed: print date.strftime("%b %d, %Y")
        return sorted(dates, reverse=True)

    def filter(self,
               date_filter:             tuple[datetime]     = None,
               level_filter:            list[int]           = None,
               script_filter:           list[str]           = None,
               function_filter:         list[str]           = None,
               session_filter:          list[int]           = None,
               reference_filter:        list[int]           = None,
               message_filter:          list[str]           = ''
               ) -> "LogEntries":
        """
        Returns a LogEntries subset that matches the filters provided.

        Parameters:
            date_filter (tuple[datetime]):      Either a single datetime object or a date range
                                                given by a tuple of two datetime objects. Filters
                                                for entries in the dates provided: [start:end).
                                                Start is inclusive. End is exclusive.

            level_filter (list[int]):           A list containing any number of the following
                                                constants: DEBUG, INFO, WARNING, ERROR, or CRITICAL.
                                                Filters for entries of the provided levels.

            script_filter (list[str]):          A list of script names. Filters for entries created
                                                by any of the provided scripts.

            function_filter (list[str]):        A list of function names. Filters for entries
                                                created by any of the provided functions.

            session_filter (list[int]):         A list of session numbers. Filters for entries from 
                                                any of the provided session numbers.

            reference_filter (list[int]):       A list of reference numbers. Filters for entries
                                                containing any of the provided reference numbers.

            message_filter (list[str]):         A list of strings. Filters for entries containing 
                                                any of the provided substrings inside their message 
                                                field.

        Returns:
            filtered_log_entries (LogEntries):  The LogEntries subset that matches the filters provided.
        """
        
        # validate and normalize arguments
        start_date, end_date = self._validate_date_filter(date_filter)
        if not isinstance(level_filter, list) and level_filter is not None:
            level_filter = [level_filter]
        if not isinstance(script_filter, list) and script_filter is not None:
            script_filter = [script_filter]
        if not isinstance(function_filter, list) and function_filter is not None:
            function_filter = [function_filter]
        if not isinstance(session_filter, list) and session_filter is not None:
            session_filter = [session_filter]
        if not isinstance(reference_filter, list) and reference_filter is not None:
            reference_filter = [reference_filter]
        if not isinstance(message_filter, list) and message_filter is not None:
            message_filter = [message_filter]

        if not all(level in VALID_LEVELS for level in level_filter):
                raise ValueError(f"'level_filter' must contain one or more of the \
                                 following constants: {VALID_LEVELS}")
        if not all(isinstance(script, str) for script in script_filter):
                raise TypeError("'script_filter' must be a string or list of strings")
        if not all(isinstance(function, str) for function in function_filter):
                raise TypeError("'function_filter' must be a string or list of strings")
        if not all(isinstance(session, int) for session in session_filter):
                raise TypeError("'session_filter' must be an integer or list of integers")
        if not all(isinstance(reference, int) for reference in reference_filter):
                raise TypeError("'reference_filter' must be an integer or list of integers")
        if not all(isinstance(substring, str) for substring in message_filter):
                raise TypeError("'message_filter' must be a string or list of strings")
        
        
        # filter events
        matching_entries = []
        for log_entry in self.entries:
            if date_filter and not (start_date <= log_entry.date < end_date):
                continue
            if level_filter and log_entry.level not in level_filter:
                continue
            if script_filter and log_entry.script not in script_filter:
                continue
            if function_filter and log_entry.function not in function_filter:
                continue
            if session_filter and log_entry.session_number not in session_filter:
                continue
            if reference_filter and log_entry.reference_number not in reference_filter:
                continue
            if message_filter:
                if not all(message in log_entry.message for message in message_filter):
                    continue
            matching_entries.append(log_entry)
            
        return LogEntries(matching_entries)

    def _validate_date_filter(date_filter: tuple[datetime]) -> tuple[datetime]:
        """
        Validates and normalizes the filter() method's date_filter parameter.

        Parameters:
            date_filter (tuple[datetime]):      Either a single datetime object or a date range
                                                given by a tuple of two datetime objects.

        Returns:
            (tuple[datetime]):                  A date range given by a tuple of two datetime 
                                                objects.
        """

        if date_filter is None:
            return None
        
        # case: type tuple
        if isinstance(date_filter, tuple):
            if len(date_filter) != 2:
                raise ValueError("date_filter must be a tuple with exactly two dates")
            
            start_date, end_date = date_filter

            if not all(isinstance(date, datetime) for date in (start_date, end_date)):
                raise TypeError("date_filter must contain datetime objects")
            
            if start_date >= end_date:
                raise ValueError("In date_filter, the left must be less than the right")

            return (start_date, end_date)
        
        # case: type date
        if isinstance(date_filter, date) and not isinstance(date_filter, datetime):
            start_date = datetime.combine(date_filter, time.min)
            end_date = start_date + timedelta(days=1)
            return (start_date, end_date)
        
        # case: type datetime
        if isinstance(date_filter, datetime):
            start_date = datetime.combine(date_filter.date(), time.min)
            end_date = start_date + timedelta(days=1)
            return (start_date, end_date)
        
        raise TypeError("date_filter must be of type datetime or tuple[datetime, datetime]")
        
class Log:
    def __init__(self, app_name: str = None, log_folder_path: str = None) -> None:
        """
        Constructs a Log object:
            - creates the log file if it doesn't exist
            - gets the namespace logger and adds a handler and formatter
            - loads the next session number and the next entry number from the log file

        Parameters:
            app_name (str):             The name of the application using this module. Used to construct
                                        the log directory following the conventions of the operating
                                        system. On macOS, logs are stored in '~/Library/Logs/<app_name>.
                                        On Linux, logs are stored in XDG_STATE_HOME which usually
                                        defaults to: '~/.local/state/<app_name>/logs'. Use only one of
                                        the two parameters not both!

            log_folder_path (str):      Optional custom directory for saving log files. Overrides the
                                        operating system's default log directory. Using app_name is
                                        recommended for platform-appropriate storage. Use only one of
                                        the two parameters not both!

        Returns:
            None
        """

        # validate arguments
        if app_name is not None and log_folder_path is not None:
            raise ValueError("use only one of the two parameters app_name or log_folder_path")
        if app_name is not None and not isinstance(app_name, str):
            raise TypeError("app_name must be a string")
        if app_name == '':
            raise ValueError("app_name cannot be an empty string")
        for char in app_name:
            if char == '/':
                raise ValueError("app_name cannot contain a forward slash")
            elif char == '.':
                raise ValueError("app_name cannot contain a period")
            elif char == ':':
                raise ValueError("app_name cannot contain a colon")
        if log_folder_path is not None and not isinstance(log_folder_path, str):
            raise TypeError("log_folder_path must be a string")
        if log_folder_path == '':
            raise ValueError("log_folder_path cannot be an empty string")
        
        # construct log file path
        if log_folder_path is not None:
            self._log_folder_path = os.path.expanduser(log_folder_path)
        elif app_name is None:
            raise ValueError("either app_name or log_folder_path must be provided")
        elif sys.platform == "darwin":
            self._log_folder_path = os.path.join(os.path.expanduser('~'),
                                                 "Library", "Logs", app_name)
        else:
            xdg_state_home = os.environ.get("XDG_STATE_HOME")
            if not xdg_state_home:
                xdg_state_home = os.path.join(os.path.expanduser('~'), ".local", "state")
            self._log_folder_path = os.path.join(xdg_state_home, app_name, "logs")

        os.makedirs(self._log_folder_path, exist_ok=True)
        self._log_path = os.path.join(self._log_folder_path, "application.log")
        self._state_path = os.path.join(self._log_folder_path, "log_state.json")

        # create logger
        self._logger = logging.getLogger(__name__)
        self._logger.setLevel(logging.DEBUG)

        # if no handlers
        if not self._logger.handlers:
            # create handler
            handler = logging.FileHandler(
                self._log_path,
                encoding="utf-8",
                errors="replace"
            )
            handler.setLevel(logging.DEBUG)

            # create formatter
            formatter = logging.Formatter(
                "DATE: %(asctime)s | "
                "LEVEL: %(levelname)s | "
                "SCRIPT: %(filename)s | "
                "FUNCTION: %(funcName)s | "
                "SESSION#: %(session_number)s | "
                "ENTRY#: %(entry_number)s | "
                "REFERENCE#: %(reference_number)s | "
                "MESSAGE: %(message)s",
                datefmt="%Y-%m-%d %I:%M:%S %p")
            
            # add handler and formatter
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)

        # load log state
        self._next_entry_number, self._next_session_number  = self._load_state()
    
    def _load_state(self) -> tuple[int, int]:
        """
        Opens the state file and returns the state of the log as a tuple.

        Parameters:
            None            

        Returns:
            raw_state (tuple[int, int]):        The log's state as a tuple.
        """

        try:
            # load state
            with open(self._state_path, "r", encoding="utf-8") as f:
                raw_state = json.load(f)

            # validate state
            required_keys = {"next_entry_number", "next_session_number"}
            if not isinstance(raw_state, dict):
                raise ValueError("WARNING: The file `log_state.json` may be corrupted. "
                                "The file will be overwritten.")
            if not required_keys <= raw_state.keys():
                raise ValueError("WARNING: The file `log_state.json` may be corrupted. "
                                "The file will be overwritten.")

            # extract values
            next_entry_number = raw_state["next_entry_number"]
            next_session_number = raw_state["next_session_number"]

            # validate log state
            if type(next_entry_number) is not int or next_entry_number < 1:
                raise ValueError("invalid next entry number")
            if type(next_session_number) is not int or next_session_number < 1:
                raise ValueError("invalid next session number")

            return next_entry_number, next_session_number

        except (json.JSONDecodeError, ValueError):
            if os.path.isfile(self._state_path):
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                backup_path = os.path.join(self._log_folder_path,
                                           f"{timestamp}_corrupted_log_state.json")
                os.rename(self._state_path, backup_path)
            return self._load_state_manually()
        
        except FileNotFoundError:
            return self._load_state_manually()

    def _load_state_manually(self) -> tuple[int, int]:
        """
        Opens the log file, checks the last entry, and returns the next entry number and the next
        session number as a tuple.

        Parameters:
            None            

        Returns:
            log_state (tuple[int, int]):    A tuple containing the next entry number and next session
                                            number.
        """
        
        try:
            with open(self._log_path, 'r', encoding="utf-8") as log:
                log_entries = log.readlines()

            if not log_entries:
                return 1,1
            
            # check last log entry
            last_log_entry = log_entries[-1]

            # parse last session number and last entry number
            _, remaining_entry = last_log_entry.split("SESSION#: ")
            last_session_number, remaining_entry = remaining_entry.split(" | ENTRY#: ")
            last_entry_number, _ = remaining_entry.split(" | REFERENCE#: ")
            next_session_number = int(last_session_number) + 1
            next_entry_number = int(last_entry_number) + 1

            return next_entry_number, next_session_number

        except (FileNotFoundError, ValueError):
            return 1, 1

    def _save_state(self) -> None:
        """
        Saves the next entry number and next session number to the state file.

        Parameters:
            None            

        Returns:
            None
        """

        state = {"next_entry_number": self.next_entry_number, 
                 "next_session_number": self.next_session_number}
        temp_path = self._state_path + ".tmp"

        try:
            # wrtie to temp file first just in case
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(state, f, indent = 4)
            os.replace(temp_path, self._state_path)

        finally:
            # delete temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    def read(self) -> LogEntries:
        """
        Reads all LogEntries in the log file.

        Parameters:
            None

        Returns:
            log_entries (LogEntries):           All LogEntries in the log file.
        """

        log_entries = []
        with open(self._log_path, 'r', encoding="utf-8") as log:
            for string_entry in log:
                log_entry = to_log_entry(string_entry)
                log_entries.append(log_entry)

        return LogEntries(log_entries)
    
    def write(self, level: int, message: Any, reference_number: int = 0) -> bool:
        """
        Writes a new LogEntry.

        Parameters:
            level (int):                Must be one of the following constants: DEBUG, INFO, WARNING,
                                        ERROR, or CRITICAL. Also known as 'severity' in the logging
                                        module.

            message (Any):              The entry message.

            reference_number (int):     Optional parameter. Corresponds to the entry's 'REFERENCE'
                                        field, used to group a chain of realted entries. Should contain
                                        the entry number of a related entry.

        Returns:
            success (bool):             Returns `True` on success.
        """

        # validate arguments
        if level not in VALID_LEVELS:
            raise ValueError(f"Level must be one of the following constants: {VALID_LEVELS}")
        if not isinstance(reference_number, int):
            raise TypeError("'reference_id' must be an integer")
        if reference_number < 0:
            raise ValueError("'reference_id' must be positive")
        
        # format values
        session_number = f"{self._next_session_number:06}"
        entry_number = f"{self._next_entry_number:06}"
        reference_number = f"{reference_number:06}"

        self._logger.log(
            level,
            message,
            extra = {
                "session_number": session_number, 
                "entry_number": entry_number, 
                "reference_number": reference_number},
            stacklevel=2)
        
        # increment next entry number after successful write
        self._next_entry_number += 1
        self._save_state()

        return True
    
    def new_session(self) -> None:
        """
        Creates a new log session by incrementing the session counter. Any new LogEntry is part of the
        new session.

        Parameters:
            None            

        Returns:
            None
        """

        self._next_session_number += 1
        self._save_state()

def to_log_entry(string_entry: str) -> LogEntry:
    """
    Takes a log entry in string form, parses it, and returns it as a LogEntry object. Importantly, the
    string must contain all of the original eight LogEntry fields! So be careful when using the LogEntry
    to_string() method that can remove fields.

    Parameters:
        string_entry (str):             A log entry in string form.

    Returns:
        log_entry (LogEntry):           A LogEntry object.
    """

    try:
        # parse fields
        _, string_entry = string_entry.split("DATE: ")
        date, string_entry = string_entry.split("LEVEL: ")
        date = date[:-3]
        level, string_entry = string_entry.split("SCRIPT: ")
        level = level[:-3]
        script, string_entry = string_entry.split("FUNCTION: ")
        script = script[:-3]
        function, string_entry = string_entry.split("SESSION#: ")
        function = function[:-3]
        session_number, string_entry = string_entry.split("ENTRY#: ")
        session_number = session_number[:-3]
        entry_number, string_entry = string_entry.split("REFERENCE#: ")
        entry_number = entry_number[:-3]
        reference_number, message = string_entry.split("MESSAGE: ")
        reference_number = reference_number[:-3]

        # convert data types
        date = datetime.strptime(date, "%Y-%m-%d %I:%M:%S %p")
        level = LEVEL_TO_INT[level]
        session_number = int(session_number)
        entry_number = int(entry_number)
        reference_number = int(reference_number)

        # instantiate LogEntry object
        log_entry = LogEntry(
            date,
            level,
            script,
            function,
            session_number,
            entry_number,
            reference_number,
            message
        )

        return log_entry
    
    except:
        raise ValueError("The string entry provided was not in the correct format." \
                            "Make sure it contains all 8 fields.")

def select_log_entry(log_entries:           LogEntries,
                     header_message:        str = "Select a log entry from below.",
                     validation_function:   Callable[[list[Any]], str]  = None
                     ) -> LogEntry:
    """
    This function allows the user to select a LogEntry from a list of LogEntries by using a fancy
    text-based user interface (TUI). This function is a wrapper around the select_option() function from
    the lino_dev_tools utils module.

    Parameters:
        log_entries (LogEntries):                   The list of log entries to choose from.

        header_message (str):                       Header message printed at the top. Despite
                                                    defaulting to an empty string, header_message is
                                                    initialized below in the validation section.

        validation_function (Callable[[Any], str]): An optional function used to validate the user's
                                                    selection. The function must return a string upon
                                                    failure or None or emptry string on success. The
                                                    string returned is printed as an error message up
                                                    top in red.

    Returns:
        selected_entry (LogEntry):                  The selected LogEntry or `None` if the user selects
                                                    the 'Go Back' option.
    """

    # validate arguments
    if not isinstance(log_entries, LogEntries):
        raise TypeError("log_entries must be a LogEntries object")
    if len(log_entries.entries) < 2:
        raise ValueError("log_entries must contain at least two elements")
    if not isinstance(header_message, str):
        raise TypeError("header must be a string")
    if validation_function is not None and not callable(validation_function):
        raise TypeError("validation_function must be None or a Callable that returns a string")

    return select_option(log_entries, header_message, validation_function)

def select_log_entries(log_entries:         LogEntries,
                       header_message:      str                         = '',
                       validation_function: Callable[[list[Any]], str]  = None,
                       max_selections:      int                         = None
                       ) -> LogEntries:
    """
    This function allows the user to select several LogEntries from a list of LogEntries by using a
    fancy text-based user interface (TUI). This function is a wrapper around the select_options()
    function from the lino_dev_tools utils module.

    Parameters:
        log_entries (LogEntries):                   The list of log entries to choose from.

        header_message (str):                       Header message printed at the top. Despite
                                                    defaulting to an empty string, header_message is
                                                    initialized below in the validation section.

        validation_function (Callable[[Any], str]): An optional function used to validate the user's
                                                    selections. The function must return a string upon
                                                    failure or None or emptry string on success. The
                                                    string returned is printed as an error message up
                                                    top in red.

        max_selections (int):                       The maximum number of selections the user is allowed
                                                    to make.

    Returns:
        selected_entries (LogEntries):              The selected LogEntries or `None` if the user
                                                    selects the 'Go Back' option.
    """

    # validate arguments
    if not isinstance(log_entries, LogEntries):
        raise TypeError("log_entries must be a LogEntries object")
    if len(log_entries.entries) < 2:
        raise ValueError("log_entries must contain at least two elements")
    if not isinstance(header_message, str):
        raise TypeError("header must be a string")
    if validation_function is not None and not callable(validation_function):
        raise TypeError("validation_function must be None or a Callable that returns a string")
    if not isinstance(max_selections, int) and max_selections is not None:
        raise TypeError("max_selections must be an integer")
    if max_selections is not None and max_selections <= 0:
        raise ValueError("max_selections must be be greater than or equal to one")
    if not header_message and max_selections:
        header_message = f"Select up to {max_selections} log entries from below."
    elif not header_message:
        header_message = "Select log entries from below"

    return select_options(log_entries, header_message, validation_function, max_selections)
