import os
import random
from server_config import defaults, print_format, log_config
from entry_manager import log_add, log_internal


def fill_simulate(amount: int, severities: dict, known_list: dict):
    """
    Simulate a workload of 'amount' requests, randomly choosing known users and severities from the database
    :param amount: Amount of entries to generate
    :param severities: The list of severities to use
    :param known_list: The lest of known users to use
    """
    if log_config["VERBOSE"]:
        print_format(f"[UTILS] Filling {amount} entries with random severities / users", color=defaults["CC"]["UTILS"])
    users = list(known_list.keys())
    sev = list(severities.keys())
    for i in range(amount):
        log_add(s_from=random.choice(users), severity=random.choice(sev),
                comment="Simulated Navigation Test", body={os.urandom(16).hex(): os.urandom(16).hex()})


def fill(amount: int):
    """
    Simulate a workload of 'amount' requests
    :param amount: Amount of entries to generate
    """
    if log_config["VERBOSE"]:
        print_format(f"[UTILS] Filling {amount} entries", color=defaults["CC"]["UTILS"])
    for i in range(amount):
        log_internal("Testing", "Navigation Test")


def fill_severities(severities: dict):
    """
    Picks all severities and make entries of them
    :param severities: The list of severities to use
    """
    if log_config["VERBOSE"]:
        print_format(f"[UTILS] Severity classes", color=defaults["CC"]["UTILS"])
    for key, sev in severities.items():
        print_format(str((key, sev)), color=defaults["CC"]["UTILS"])
        log_internal(key, "Testing Internal Severity classes available")


def fill_servers(known_list: dict):
    """
    Picks all known users and make entries of them
    :param known_list: The list of known users to use
    """
    if log_config["VERBOSE"]:
        print_format(f"[LOG SERVER] Known users", color=defaults["CC"]["UTILS"])
    for key, sev in known_list.items():
        print_format(str((key, sev)), color=defaults["CC"]["UTILS"])
        log_add(s_from=key, severity="Information", comment="Testing Internal user classes known")
