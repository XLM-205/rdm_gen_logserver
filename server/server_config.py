# Main server configurations that can changed during runtime
log_config = {"PRE_INIT": [],           # Stuff to do before initialization
              "POST_INIT": [],          # Stuff to do after initialization
              "CLEAR_INIT": True,       # If True, will clear all Pre and Post init after each execution
              "VERBOSE": False,         # If True, each log added will produce an equivalent console output
              "LOAD_PRIVATE": False,     # If True, will try to load sensitive data (for debug purposes)
              "PUBLIC": False,          # If True, all users can see each-others logs (Requires 'LOGIN' = True)
              "LOGIN": True}            # If True, all users need to login (Database dependent)

# Default values used within the server. Changing them during runtime is NOT RECOMMENDED
defaults = {"SEVERITIES": {"success": ('#000000', '#00ee55'),   # Default severity classes if DB fails loading
                           "warning": ('#000000', '#ffff00'),
                           "attention": (None, '#ff7700'),
                           "error": (None, '#ff2211'),
                           "critical": (None, '#aa0022')},
            "UI": {"ACCENT": 'background-color: var(--accent-color);',  # Default color accent
                   "EPP": 20},                                          # Entries Per Page
            "CC": {"SERVER_BOOT": "white",  # Console Color code for each module if it's to print something with Verbose
                   "CLASSES": "red",
                   "ENTRY_MANAGER": "green",
                   "UTILS": "yellow",
                   "PAGING": "blue",
                   "ROUTES": "pink",
                   "SERVER_CONFIG": "cyan"},
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
            "INTERNAL": {"VERSION": "0.7",  # Server's Version
                         "ACCESS_POINT": "https://rdm-gen-logserver.herokuapp.com/",
                         "SERVER_NAME": "Internal"}}    # Server's name internally and on entries


def print_format(message: str, color='', bold=False, underline=False):
    """
    Prints text with color, header, bold or underline

    :param message: The message to be written
    :param color: 'black', 'red', 'green', 'yellow', 'blue', 'pink', 'cyan', or 'white'
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
    color = str.lower(color)
    if color in palette:
        c = palette[color]

    print(f"{c}{b}{u}{message}{end}")


def private_info_fill():
    """If you have sensitive data, insert it here. Should reference files ignored by your VCS and local to the deploy.
       \nThis method is custom tailored for each use case and invoking and using it is OPTIONAL."""
    from os import path
    import importlib
    try:
        if log_config["VERBOSE"]:
            # noinspection PyTypeChecker
            print_format(f"[SERVER CONFIG] Loading private resources...",
                         color=defaults["CC"]["SERVER_CONFIG"], bold=True)
        confidential_path = "server/private_resources/conf_res"
        import_path = confidential_path.replace("/", ".")   # Since the importlib uses '.' instead of '/'
        # Grabbing a local DB url
        if path.exists(confidential_path + ".py"):
            conf_res = importlib.import_module(import_path)
            defaults["FALLBACK"]["DB_URL"] = conf_res.local_db_url
            if log_config["VERBOSE"]:
                # noinspection PyTypeChecker
                print_format(f"[SERVER CONFIG] Local Database url set to '{defaults['FALLBACK']['DB_URL']}'",
                             color=defaults["CC"]["SERVER_CONFIG"], bold=True)
        else:
            if log_config["VERBOSE"]:
                # noinspection PyTypeChecker
                print_format(f"[SERVER CONFIG] '{import_path}' module was not found. Loading aborted",
                             color=defaults["CC"]["SERVER_CONFIG"], bold=True)
    except Exception as ecp:
        # noinspection PyTypeChecker
        print_format(f"[SERVER CONFIG] Failed to fetch private resources, {str(ecp)}",
                     color=defaults["CC"]["SERVER_CONFIG"], bold=True)
        return
    if log_config["VERBOSE"]:
        # noinspection PyTypeChecker
        print_format(f"[SERVER CONFIG] Private resources loaded successfully",
                     color=defaults["CC"]["SERVER_CONFIG"], bold=True)
