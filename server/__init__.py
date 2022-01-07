"""Prepares to start the server, setting the configuration desired, and tasks for before and after initialization.
Calls 'create_app' on 'server_boot', which actually starts the server
"""

# from entry_manager import severities, known_list
# from server_config import logger_config
from server_boot import create_app
# from utils import fill_simulate

if __name__ == "__main__":
    # Pre-configuring our server
    # logger_config["VERBOSE"] = True
    # logger_config["LOGIN"] = False
    # logger_config["PUBLIC"] = True
    # logger_config["USE_DB"] = False
    # logger_config["LOAD_PRIVATE"] = True
    # logger_config["POST_INIT"].append((fill_simulate, (200, severities, known_list)))

    # Ready to start the server
    create_app()
