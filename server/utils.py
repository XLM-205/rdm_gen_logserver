import os
import random

from entry_manager import log_add, log_internal
from server_config import print_verbose


def fill_simulate(amount: int, severities: dict, known_list: dict):
    """
    Simulate a workload of 'amount' requests, randomly choosing known users and severities from the given lists
    :param amount: Amount of entries to generate
    :param severities: A dictionary of severities to use
    :param known_list: A dictionary of known users to use
    """
    print_verbose(sender=__name__,
                  message=f"Filling {amount} entries with random severities and users")
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
    print_verbose(sender=__name__,
                  message=f"Filling {amount} entries")
    for i in range(amount):
        log_internal("Testing", "Navigation Test")


def fill_severities(severities: dict):
    """
    Picks all severities and make entries of them
    :param severities: The list of severities to use
    """
    print_verbose(sender=__name__,
                  message=f"Severity Classes")
    for key, sev in severities.items():
        log_internal(key, "Testing Internal Severity classes available")


def fill_servers(known_list: dict):
    """
    Picks all known users and make entries of them
    :param known_list: The list of known users to use
    """
    print_verbose(sender=__name__,
                  message=f"Known users")
    for key, sev in known_list.items():
        log_add(s_from=key, severity="Information", comment="Testing Internal user classes known")
