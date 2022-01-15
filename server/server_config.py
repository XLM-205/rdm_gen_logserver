from datetime import datetime

# Main server configurations that can changed during runtime. Default values are defined as (Dft: T / F)
logger_config = {"PRE_INIT": [],         # Stuff to do before initialization
                 "POST_INIT": [],        # Stuff to do after initialization
                 "CLEAR_INIT": True,     # If True, will clear all Pre and Post init after each execution (Dft: T)
                 "VERBOSE": False,       # If True, each log added will produce an equivalent console output (Dft: F)
                 "LOAD_PRIVATE": False,  # If True, will try to load sensitive data (for debug purposes) (Dft: F)
                 "USE_DB": True,         # If True, will try to fetch users and severities from a database (Dft: T)
                 "PUBLIC": True,         # If True, all users can see each-others logs (Requires 'LOGIN'=True) (Dft: F)
                 "LOGIN": True}          # If True, all users need to login (Database dependent) (Dft: T)

# Default values used within the server. Changing them during runtime is NOT RECOMMENDED
defaults = {"SEVERITIES": {"success": ('#000000', '#00ee55'),   # Default severity classes if DB fails loading
                           "warning": ('#000000', '#ffff00'),
                           "attention": (None, '#ff7700'),
                           "error": (None, '#ff2211'),
                           "critical": (None, '#aa0022')},
            "SERVERS": {},                                      # Defaults servers (Internal is added in runtime)
            "INTERFACE": {"PAGE": {"ACCENT": 'background-color: var(--accent-color);',  # Default color accent
                                   "EPP": 20,                                           # Entries Per Page
                                   "EPP_LIST": [10, 20, 50, 100],                       # Options of EPP (only ints)
                                   "FETCH_INTERVAL": 3000},                             # How many ms between fetches
                          "CONSOLE": {"SERVER_BOOT": "white",  # Console Color code for each module
                                      "DB_MODELS": "red",
                                      "ENTRY_MANAGER": "green",
                                      "UTILS": "yellow",
                                      "PAGING": "blue",
                                      "ROUTES": "pink",
                                      "SECURITY": "cyan"}},
            "SECURITY": {"INJ_GUARD": {"CASES": ["--", "\')", ");"],         # If any is found in the query, reject
                                       "GROUPS": [["\'", ")"], [")", ";"]],  # If found in the order, reject
                                       "REPLACES": [["\'", "´"], ]},         # If [0] is found, replace to [1]
                         "LOGIN": {"MAX_TRIES": 5,      # Maximum amount of wrong guesses before locking the login
                                   "LOCKOUT": 3600}     # How many seconds should the login for that IP be locked
                         },
            "FALLBACK": {"PORT": 5001,      # Default port
                         "DB_URL": None},   # Default Database URL
            "SERVICES": {"TIMEOUT": 10,     # How many seconds between each service request
                         "LOCKED": False},  # If True, the server cannot make another request
            "INTERNAL": {"VERSION": "0.9.0",    # Server's Version
                         "ACCESS_POINT": "https://rdm-gen-logserver.herokuapp.com/",
                         "SERVER_NAME": "Internal",         # Server's name internally and on entries
                         "PRODUCT_NAME": "GPS LogServer"}}  # Server's 'pretty' product name


# Methods --------------------------------------------------------------------------------------------------------------
def print_verbose(sender: str, message: str, color: str = None, bold: bool = False, underline: bool = False):
    """
    # Prints a message on the console if 'logger_config["VERBOSE"]' is True
    :param sender: The module that sent the message. If it matches any entry on 'defaults["INTERFACE"]["CONSOLE"]' this
    message will have that defined color. If not, it will use 'printer_color'
    :param message: The message to be printer on the console
    :param color: A color to override the default one. Needs to be a valid color of 'print_rich'. Default is None
    :param bold: If true, prints the message in bold. Default is False
    :param underline: If true, prints the message with an underline. Default is False
    """
    if sender is None:  # Abort
        return
    sender = sender.upper()
    if logger_config["VERBOSE"]:
        printer_color = None
        if color is not None:
            printer_color = color
        elif sender in defaults["INTERFACE"]["CONSOLE"]:
            # noinspection PyTypeChecker
            printer_color = defaults["INTERFACE"]["CONSOLE"][sender]
        print_rich(f"[{datetime.now().strftime('%H:%M:%S.%f')}][{sender}] {message}",
                   color=printer_color, bold=bold, underline=underline)


def print_rich(message: str, color=None, bold=False, underline=False):
    """
    Prints text with color, header, bold or underline
    :param message: The message to be written
    :param color: 'black', 'red', 'green', 'yellow', 'blue', 'pink', 'cyan', or 'white'. Defaults to '' (none color)
    :param bold: Boolean
    :param underline: Boolean
    """
    # From https://stackoverflow.com/questions/287871/how-to-print-colored-text-to-the-terminal
    end = '\033[0m'
    b = '\033[1m' if bold else ''
    u = '\033[4m' if underline else ''
    palette = {'black': '\033[90m', 'red': '\033[91m', 'green': '\033[92m', 'yellow': '\033[93m', 'blue': '\033[94m',
               'pink': '\033[95m', 'cyan': '\033[96m', 'white': '\033[97m', }
    c = ''
    if color is None:
        color = ''
    else:
        color = str.lower(color)
    if color in palette:
        c = palette[color]

    print(f"{c}{b}{u}{message}{end}")
