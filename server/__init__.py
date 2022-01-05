from classes import severities, known_list
from server_config import log_config
from server_boot import create_app
from utils import fill_simulate

if __name__ == "__main__":
    # Pre-configuring our server
    log_config["VERBOSE"] = True
    log_config["LOGIN"] = False
    log_config["PUBLIC"] = True
    # log_config["LOAD_PRIVATE"] = False
    # log_config["POST_INIT"].append((fill_simulate, (10000, severities, known_list)))

    # Ready to start the server
    create_app()
