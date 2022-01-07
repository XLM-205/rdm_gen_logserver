# Main server configurations that can changed during runtime. Default values are defined as (Dft: T / F)
logger_config = {"PRE_INIT": [],         # Stuff to do before initialization
                 "POST_INIT": [],        # Stuff to do after initialization
                 "CLEAR_INIT": True,     # If True, will clear all Pre and Post init after each execution (Dft: T)
                 "VERBOSE": False,       # If True, each log added will produce an equivalent console output (Dft: F)
                 "LOAD_PRIVATE": False,  # If True, will try to load sensitive data (for debug purposes) (Dft: F)
                 "USE_DB": True,         # If True, will try to fetch users and severities from a database (Dft: T)
                 "PUBLIC": False,        # If True, all users can see each-others logs (Requires 'LOGIN'=True) (Dft: F)
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
                                      "CLASSES": "red",
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
            "INTERNAL": {"VERSION": "0.8.0",    # Server's Version
                         "ACCESS_POINT": "https://rdm-gen-logserver.herokuapp.com/",
                         "SERVER_NAME": "Internal"}}    # Server's name internally and on entries
