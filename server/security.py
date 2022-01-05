import flask
import sqlalchemy
from datetime import datetime, timedelta
from flask import flash, url_for
from flask_login import login_user
from werkzeug.utils import redirect

from classes import Users
from server_config import defaults, log_config, print_format
from entry_manager import log_internal

# Holds all ips that tried to connect "{IP}": [tries: int, locked: bool, lock_until: datetime]
login_attempts = {}


class InjectionToken(Exception):
    """ Raised if the Injection Guard function detects an Injection Attempt """
    pass


def injection_guard(queries: []):
    """
    Analyses all query strings in 'queries' to prevent injection attacks in 3 phases. The last one attempts to fix them
    :param queries: List of query strings
    """
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


def try_login(log_in, wp):
    """
    Tries to login, verifying first against SQL Injection attempts
    :param log_in: The login credentials (username / server url)
    :param wp: The WebPassword
    :return: An Users object, if successful, and None if doesn't
    """
    # noinspection PyUnresolvedReferences
    try:
        injection_guard([log_in, wp])
        user = Users.authenticate(log_in, wp)
    except InjectionToken:
        # Probable SQL Injection attack!
        log_internal(severity="Critical",
                     comment=f"SQL Injection Attempt identified from {flask.request.remote_addr} !",
                     body={"log_in": log_in, "wp": wp})
        flash("Login information had invalid characters")
        return None
    except sqlalchemy.exc.ProgrammingError:
        # Probable SQL Injection attack!
        log_internal(severity="Critical",
                     comment=f"SQL Injection Attempt identified from {flask.request.remote_addr} !",
                     body={"log_in": log_in, "wp": wp})
        flash("Login information had invalid characters")
        return None
    except (sqlalchemy.exc.NoSuchColumnError, AttributeError, TypeError):
        flash("Invalid Login Attempt")
        return None
    return user


def attempt_login(log_in, wp, ip_address, remember=False):
    """
    Attempts to make a login, checking if this IP didn't have tried brute-forcing it before
    :param log_in: The login credentials (username / server url)
    :param wp: The WebPassword
    :param ip_address: Client's IP address currently attempting to login
    :param remember: If True, remember this user on the next login
    :return: A redirect to the actual Server GUI if successful, or back to the login page, if failed
    """
    # Safeguarding against brute force
    # 403 -> Known IP
    if ip_address in login_attempts:     # User is known
        if login_attempts[ip_address][1] is False:
            # User not locked. Attempt login
            user = try_login(log_in, wp)
        elif login_attempts[ip_address][2] <= datetime.now():
            # User is locked, but his lock have expired
            login_attempts[ip_address][0] = 0
            login_attempts[ip_address][1] = False
            user = try_login(log_in, wp)
        else:
            if log_config["VERBOSE"]:
                print_format(f"[ROUTES] IP {ip_address} is still locked until {login_attempts[ip_address][2]}",
                             color=defaults["CC"]["ROUTES"])
            return redirect(url_for("auth.login"))
    else:   # User is unknown
        login_attempts[ip_address] = [0, False, None]
        user = try_login(log_in, wp)

    # Attempting login
    if user is None:
        login_attempts[ip_address][0] += 1
        if login_attempts[ip_address][0] >= defaults["SECURITY"]["LOGIN"]["MAX_TRIES"]:  # Lock user
            lockout = datetime.now() + timedelta(seconds=defaults["SECURITY"]["LOGIN"]["LOCKOUT"])
            login_attempts[ip_address][1] = True
            login_attempts[ip_address][2] = lockout
            if log_config["VERBOSE"]:
                print_format(f"[ROUTES] IP {ip_address} is locked until {login_attempts[ip_address][2]}",
                             color=defaults["CC"]["ROUTES"])
        flash("Invalid Login")
        if log_config["VERBOSE"]:
            print_format(f"[ROUTES] IP {ip_address} failed to login (Attempt {login_attempts[ip_address][0]})",
                         color=defaults["CC"]["ROUTES"])
        return redirect(url_for("auth.login"))
    login_attempts[ip_address][0] = 0
    login_attempts[ip_address][1] = False
    if log_config["VERBOSE"]:
        print_format(f"[ROUTES] IP {ip_address} logged in successfully",
                     color=defaults["CC"]["ROUTES"])
    login_user(user, remember=remember)
    return redirect(url_for("main.show_recent_entries"))
