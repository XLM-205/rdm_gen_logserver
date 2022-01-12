import flask
import flask_login
import sqlalchemy
from datetime import datetime, timedelta
from flask import flash
from flask_login import login_user

from db_models import Users
from server_config import defaults, print_verbose
from entry_manager import log_uncaught_exception, log_internal_echo

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


def make_login(log_in, wp):
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
    except (InjectionToken, sqlalchemy.exc.ProgrammingError):
        # Probable SQL Injection attack!
        log_internal_echo(severity="Critical", sender=__name__,
                          comment=f"SQL Injection Attempt identified from {flask.request.remote_addr} !",
                          body={"log_in": log_in, "wp": wp})
        flash("Login information had invalid characters")
        return None
    except (sqlalchemy.exc.NoSuchColumnError, AttributeError, TypeError):
        flash("Invalid Login Attempt")
        return None
    except Exception as exc:
        log_uncaught_exception(str(exc), None, __name__)
        print_verbose(sender=__name__, message=f"Uncaught exception trying to login user {log_in} with pass {wp}")
        return None
    return user


def attempt_login(log_in, wp, ip_address, remember=False):
    """
    Attempts to make a login, checking if this IP didn't have tried brute-forcing it before
    :param log_in: The login credentials (username / server url)
    :param wp: The WebPassword
    :param ip_address: Client's IP address currently attempting to login
    :param remember: If True, remember this user on the next login
    :return: A HTTP code relative to the response of the attempt.
    200 for a successful login, 401 for a failed one and 403 if locked
    """
    # Safeguarding against brute force
    success = 200
    bad_request = 400
    failed = 401
    locked = 403
    try:
        if ip_address in login_attempts:     # User is known
            if login_attempts[ip_address][1] is False:
                # User not locked. Attempt login
                user = make_login(log_in, wp)
            elif login_attempts[ip_address][2] <= datetime.now():
                # User is locked, but his lock have expired
                login_attempts[ip_address][0] = 0
                login_attempts[ip_address][1] = False
                user = make_login(log_in, wp)
            else:
                print_verbose(sender=__name__,
                              message=f"IP {ip_address} is still locked until {login_attempts[ip_address][2]}")
                # return redirect(url_for("auth.login"))
                return locked
        else:   # User is unknown
            login_attempts[ip_address] = [0, False, None]
            user = make_login(log_in, wp)

        # Attempting login
        if user is None:
            login_attempts[ip_address][0] += 1
            if login_attempts[ip_address][0] >= defaults["SECURITY"]["LOGIN"]["MAX_TRIES"]:  # Lock user
                lockout = datetime.now() + timedelta(seconds=defaults["SECURITY"]["LOGIN"]["LOCKOUT"])
                login_attempts[ip_address][1] = True
                login_attempts[ip_address][2] = lockout
                log_internal_echo(severity="Attention", sender=__name__,
                                  comment=f"IP {ip_address} is locked until {login_attempts[ip_address][2]}"
                                          f" (Too many failed attempts)")
            flash("Invalid Login")
            print_verbose(sender=__name__,
                          message=f"IP {ip_address} failed to login (Attempt {login_attempts[ip_address][0]})")
            # return redirect(url_for("auth.login"))
            return failed
    except (TypeError, KeyError) as exc:
        print_verbose(sender=__name__,
                      message=f"Login exception trying to login user {log_in} with pass {wp}: '{str(exc)}'")
        return bad_request
    except Exception as exc:
        log_uncaught_exception(str(exc), None, __name__)
        print_verbose(sender=__name__,
                      message=f"Uncaught exception trying to login user {log_in} with pass {wp}: '{str(exc)}'")
        return bad_request
    login_attempts[ip_address][0] = 0
    login_attempts[ip_address][1] = False
    login_user(user, remember=remember)
    print_verbose(sender=__name__,
                  message=f"{flask_login.current_user.name} ({ip_address}) logged in successfully")
    # return redirect(url_for("main.show_recent_entries"))
    return success
