import os
import random
from server_config import defaults, print_format
from entry_manager import log_add, log_internal


# Debug Functions ------------------------------------------------------------------------------------------------------
def fill_simulate(amount: int, severities: dict, known_list: dict):
    print_format(f"[LOG SERVER] Filling {amount} entries with random severities and users", color=defaults["CC"]["LOG_SERVER"])
    users = list(known_list.keys())
    sev = list(severities.keys())
    for i in range(amount):
        log_add(s_from=random.choice(users), severity=random.choice(sev),
                comment="Simulated Navigation Test", body={os.urandom(16).hex(): os.urandom(16).hex()})


def fill(amount: int):
    print_format(f"[LOG SERVER] Filling {amount} entries", color=defaults["CC"]["LOG_SERVER"])
    for i in range(amount):
        log_internal("Testing", "Navigation Test")


def fill_severities(severities: dict):
    print_format(f"[LOG SERVER] Severity classes", color=defaults["CC"]["LOG_SERVER"])
    for key, sev in severities.items():
        print_format(str((key, sev)), color=defaults["CC"]["LOG_SERVER"])
        log_internal(key, "Testing Internal Severity classes available")


def fill_servers(known_list: dict):
    print_format(f"[LOG SERVER] Known users", color=defaults["CC"]["LOG_SERVER"])
    for key, sev in known_list.items():
        print_format(str((key, sev)), color=defaults["CC"]["LOG_SERVER"])
        log_add(s_from=key, severity="Information", comment="Testing Internal user classes known")


class InjectionToken(Exception):
    """ Raised if the Injection Guard function detects an Injection Attempt """
    pass


def injection_guard(queries: []):
    # These tokens will reject a query if found at any time
    cases = defaults["SECURITY"]["INJ_GUARD"]["CASES"]
    # These tokens will reject a query if found in the order provided
    groups = defaults["SECURITY"]["INJ_GUARD"]["GROUPS"]
    # This tokens will be replaced to, if found
    replaces = defaults["SECURITY"]["INJ_GUARD"]["REPLACES"]
    for query in queries:
        # First pass: Common tokens
        for case in cases:
            if case in query:
                raise InjectionToken("Invalid characters detected on input string!", )
        # Second pass: Following Matching tokens
        for group in groups:
            full_match = True
            continue_from = 0
            for pair in group:
                continue_from = query.find(pair, continue_from)
                if continue_from == -1:
                    full_match = False
                    break
            if full_match:
                raise InjectionToken("Invalid characters detected on input string!", )
        # Third pass: Hard replace tokens if found
        for replace in replaces:
            query.replace(replace[0], replace[1])
    pass