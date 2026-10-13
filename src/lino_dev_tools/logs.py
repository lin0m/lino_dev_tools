'''
This module provides easy to use logging functionality. It is essentially a wrapper
around python's logging module for simplified logging with none of the fuzz.

* log = Log(): Returns a ready to use log. The log will be saved in the directory
  '/logs/application.log'.
* log.write(): Writes to the log file.
* log.read(): Returns all log entries as a LogEntries object.
* log.new_session(): Creates a new log session.

TODO:
    - create log_state.json with
        - next entry #
        - next session #
        - session history (sessions per date and session entry count)
Author: Lino Mercado_Esquivias
'''

# import standard library & local modules
from datetime import date, datetime, time, timedelta
import json
from lino_dev_tools.colors import *
import logging
import os
from typing import Any

# import third-party modules
try:
    import readchar
except ImportError as e:
    raise ImportError(
        "lino_dev_tools.logs requires the readchar module. Install " \
        "it with: pip install readchar."
    ) from e

# re-export constants for ease of use
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
                 date: datetime,
                 level: int,
                 script: str,
                 function: str,
                 session_number: int,
                 entry_number: int,
                 reference_number: int,
                 message: str
                 ) -> None:
        """
        This method initializes a LogEntry object.

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
        This method returns the string to print when a LogEntry object is printed.

        Parameters:
            None

        Returns:
            string_entry (str):         The string to print when a LogEntry object is printed.
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
                 include_date: bool = True,
                 include_level: bool = True,
                 include_script: bool = True,
                 include_function: bool = True,
                 include_session_number: bool = True,
                 include_entry_number: bool = True,
                 include_reference_number: bool = True,
                 include_message: bool = True
                 ) -> str:
        """
        This method returns the entry as a string. All the parameters are optional booleans that
        determine what fields to include in the string.

        Parameters:
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
            string_entry (str):                     The entry as a string.
        """

        # validate arguments
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

        string_entry = " | ".join(field_value_pair for field_value_pair in field_value_pairs)

        return string_entry

class LogEntries:
    def __init__(self, log_entries: list[LogEntry]) -> None:
        """
        This method initializes a LogEntries object.

        Parameters:
            log_entries (list[LogEntry]):       A list of log entries.

        Returns:
            None
        """
        self.log_entries = log_entries

    def dates(self) -> list[date]:
        """
        This method returns a list of dates for which there exist log entries. The list is sorted
        from newest to oldest date.

        Parameters:
            None

        Returns:
            None
        """

        dates = {entry.date.date() for entry in self.log_entries}

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
        This method accepts filters and returns log entries that match the filters
        provided.

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
            filtered_log_entries (LogEntries):  Returns all log entries matching the filters.
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
        for log_entry in self.log_entries:
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
        This method is called by the filter() method. It validates and normalizes the filter()
        method's date_filter parameter.

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
        
    def print(self, visible_lines: int = 15) -> None:
        """
----------------------------------------------------------------------------------------------------
        This function prints every log event given. Optionally, parameters can be provided to
        filter which events are returned.

        Parameters:
            function_filter (list[str]):        A list of function names. Filters for events created
                                                by any of the provided functions.

            session_filter (list[int]):         A list of session ids. Filters for events from any
                                                of the provided sessions.

        Returns:
            filtered_log_events (list[dict]):   Returns a list of events matching the filters. Each
                                                event is a dictionary with elements
                                                {field_name : value}.
        """

        # validate arguments
        if not isinstance(visible_lines, int):
            raise TypeError("'visible_lines' must be an intiger")
        if visible_lines < 1:
            raise ValueError("'visible_lines' must be positive")
                
        # initialize variables
        header = ''
        current_selection = 0
        next_selection = 0
        selection_offset = 0
        current_page = 0
        next_page = 0
        window_start = 0
        pages = len(self.self.log_entries)//visible_lines
        if len(self.self.log_entries)%visible_lines != 0:
            pages += 1
        if pages > 1:
            print_footer = True
        else:
            print_footer = False
        padding = visible_lines - (len(self.log_entries)%visible_lines)
        columns_to_print ={"DATE": True,
                        "LEVEL": True,
                        "SCRIPT": False,
                        "FUNCTION": False, 
                        "SESSION#": True,
                        "ENTRY#": False,
                        "REFERENCE#": False,
                        "MESSAGE": True}
        
        try:
            # hide cursor
            print(RESET_TERMINAL, end='')
            print(HIDE_CURSOR, end='')

            while True:
                # print header and instructions
                print(f"{RED}{header}{RESET}")
                print(f"{DISABLE}(Use the {RESET+BOLD}Arrow Keys{RESET+DISABLE} to ", end='')
                print(f"navigate. Press {RESET+BOLD}Enter{RESET+DISABLE} to select an ", end='')
                print(f"event. Press {RESET+BOLD}q{RESET+DISABLE} to cancel.){RESET}")

                # check if user changed selection or page
                selection_offset = current_selection - window_start
                if next_page != current_page:
                    current_page = next_page
                    window_start = current_page * visible_lines
                    current_selection = window_start + selection_offset
                    if current_selection >= len(self.log_entries):
                        current_selection = len(self.log_entries) - 1
                    next_selection = current_selection
                elif next_selection != current_selection:
                    current_selection = next_selection
                    current_page = current_selection//visible_lines
                    next_page = current_page
                    window_start = current_page * visible_lines

                # determine visible events
                next_window_start = window_start + visible_lines
                if not self.log_entries:
                    print(f"{RED}No events{RESET}")
                    visible_events = []
                else:
                    visible_events = self.log_entries[window_start:next_window_start]

                # print visible events
                for index, event in enumerate(visible_events):
                    actual_index = window_start + index
                    if actual_index == current_selection:
                        line = f"{LIGHT_GRAY_BCKGND} | ".join(
                            f"{LIGHT_GRAY_BCKGND}{YELLOW}{field}: {GREEN}{event[field]:^10}{RESET}"
                            for field, enabled in columns_to_print.items()
                            if enabled
                        )
                        if line:
                            print(line, end='')
                    else:
                        line = " | ".join(
                            f"{YELLOW}{field}: {GREEN}{event[field]:^10}{RESET}"
                            for field, enabled in columns_to_print.items()
                            if enabled
                        )
                        if line:
                            print(line, end='')
                
                # print padding on last page
                if current_page == pages-1 and padding > 0 and padding != visible_lines:
                    for i in range(padding):
                        print()

                # print footer
                if print_footer:
                    print(f"{DISABLE}(Page {current_page+1}/{pages}){RESET}")

                # read user input and take appropriate action
                key = readchar.readkey()
                if key == readchar.key.UP:
                    next_selection = (current_selection - 1) % len(self.log_entries)
                elif key == readchar.key.DOWN:
                    next_selection = (current_selection + 1) % len(self.log_entries)
                elif key == readchar.key.LEFT:
                    next_page = (current_page - 1) % pages
                elif key == readchar.key.RIGHT:
                    next_page = (current_page + 1) % pages
                elif key.lower() == 'q':
                    return None
                elif key == readchar.key.ENTER:
                    selected_option = self.log_entries[current_selection]
                    return selected_option
                print(RESET_TERMINAL, end='')
                print(HIDE_CURSOR, end='')

        finally:
            # always restore cursor
            print(RESET_TERMINAL, end='')

class Log:
    def __init__(self, log_folder_path: str = None) -> None:
        """
        This function initializes a Log object:
            - creates the log file if it doesn't exist
            - gets the namespace logger and adds a handler and formatter
            - loads the next session number and the next entry number from the log file

        Parameters:
            None            

        Returns:
            None
        """

        # construct log file path
        if log_folder_path:
            self._log_folder_path = log_folder_path
        else:
            self._log_folder_path = os.path.join(os.getcwd(), "logs")

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
        self._raw_state = self._load_state()
        self._next_entry_number = None
        self._next_session_number = None
        self.sessions = None
        
    def _load_state(self) -> dict:
        try:
            # load state
            with open(self._state_path, "r", encoding="utf-8") as f:
                raw_state = json.load(f)

            # validate state
            required_keys = {"next_entry_number", "next_session_number", "session_history"}
            if not isinstance(raw_state, dict):
                raise ValueError
            if not required_keys <= raw_state.keys():
                raise ValueError

        except (json.JSONDecodeError, OSError, ValueError):
            raw_state = self._load_state_manually()

        return raw_state

    def _load_state_manually(self) -> tuple[int, int]:
        """
        This method is called by the init() method when a Log object is instantiated. It opens the
        log file, checks the last entry, and returns the next session number and the next entry
        number.

        Parameters:
            None            

        Returns:
            log_state (tuple):          A tuple containing the next session number and next entry
                                        number.
        """
        
        try:
            with open(self._log_path, 'r', encoding="utf-8") as log:
                log_entries = log.readlines()

            if not log_entries:
                return 1,1
            
            # check last log entry
            last_log_entry = log_entries[-1]

            # parse last session number
            last_session_number = last_log_entry.split("SESSION#: ")
            if len(last_session_number) < 2:
                last_session_number = 1     # if log is corrupted restart count
            else:
                last_session_number = last_session_number[1]
                last_session_number = last_session_number.split(" | ")[0]
                next_session_number = int(last_session_number) + 1
    
            # parse last entry number
            last_entry_number = last_log_entry.split("ENTRY#: ")
            if len(last_entry_number) < 2:
                last_entry_number = 1       # if log is corrupted restart count
            else:
                last_entry_number = last_entry_number[1]
                last_entry_number = last_entry_number.split(" | ")[0]
                next_entry_number = int(last_entry_number) + 1

            return next_session_number, next_entry_number

        except (FileNotFoundError, ValueError):
            return 1,1
    
    def read(self) -> LogEntries:
        """
        This method loads all entries from the log file.

        Parameters:
            None

        Returns:
            log_entries (LogEntries):               Returns all entries in the log file.
        """

        log_entries = []
        with open(self._log_path, 'r', encoding="utf-8") as log:
            for string_entry in log:
                log_entry = to_log_entry(string_entry)
                log_entries.append(log_entry)

        return LogEntries(log_entries)
    
    def write(self, level: int, message: Any, reference_number: int = 0) -> bool:
        """
        This function writes a new log entry.

        Parameters:
            level (int):                Must be one of the following constants: DEBUG, INFO,
                                        WARNING, ERROR, or CRITICAL. Also known as 'severity' in the
                                        logging module.

            message (Any):              The entry message.

            reference_number (int):     This optional parameter corresponds to the entry's
                                        'REFERENCE' field, used to group a chain of realted entries.
                                        Should contain the entry number of a related entry.

        Returns:
            (bool):                     Returns 'True' on success.
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

        return True
    
    def new_session(self) -> None:
        """
        This function creates a new log session by incrementing the session counter. Any new log 
        entries are part of the new session.

        Parameters:
            None            

        Returns:
            None
        """

        self._next_session_number += 1

def to_log_entry(string_entry: str) -> LogEntry:
    """
    This function takes a log entry in string form, parses it, and returns it as a LogEntry
    object.

    Parameters:
        string_entry (str):             A log entry in string form.

    Returns:
        log_entry (LogEntry):           A LogEntry object.
    """

    try:
        # parse fields
        _, string_entry = string_entry.split("DATE: ")
        date, string_entry = string_entry.split(" | LEVEL: ")
        level, string_entry = string_entry.split(" | SCRIPT: ")
        script, string_entry = string_entry.split(" | FUNCTION: ")
        function, string_entry = string_entry.split(" | SESSION#: ")
        session_number, string_entry = string_entry.split(" | ENTRY#: ")
        entry_number, string_entry = string_entry.split(" | REFERENCE#: ")
        reference_number, message = string_entry.split(" | MESSAGE: ")

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
