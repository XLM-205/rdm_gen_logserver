"""Prepares to start the server, setting the configuration desired, and tasks for before and after initialization.
Calls 'create_app' on 'server_boot', which actually starts the server
"""
import os

from server_config import logger_config, defaults
from server_boot import create_app
# from utils import fill_simulate
# from entry_manager import severities, servers_list
# from utils import fill_simulate

if __name__ == "__main__":
    # Pre-configuring our server
    logger_config["VERBOSE"] = True
    # logger_config["LOGIN"] = False
    # logger_config["USE_DB"] = False
    # logger_config["LOAD_PRIVATE"] = True
    # logger_config["POST_INIT"].append((fill_simulate, (200, severities, servers_list)))

    # Ready to start the server
    app = create_app()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", defaults["FALLBACK"]["PORT"])), use_reloader=False)
