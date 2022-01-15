import flask
from datetime import datetime

from typing import Tuple

from flask_wrappers import authenticated_user_is
from server_config import defaults, logger_config, print_verbose

entry_list = []     # All of our entries
global_id = 0       # Global Entry Identifier
# Severities classes (FG Color, BG Color). The key is the severity
# This here ensure the severities AND server's lists are filled with at least default values
severities = defaults["SEVERITIES"]            # Severity name, color and backcolor
servers_list = defaults["SERVERS"]             # User list with proper name, color, backcolor and expected URL
db_entries = []                                # DB Fetched past entries


def lists_count() -> Tuple[int, int, int]:
    """
    Returns the current length of all lists
    :return: A tuple containing the lengths of (severity, server, entry) lists
    """
    return len(severities), len(servers_list), len(entry_list)


def log_count():
    """Returns the entry list length"""
    return len(entry_list)


def log_purge():
    """Clears the entry list"""
    entry_list.clear()


def log_get(filter_by=None, target=None):
    """ Returns a list of entries based on the filter
    :param filter_by: Will filter by whom sent the entry or the severity of the entry (default to 'off')
    :param target: The value to match against. if 'log_config["PUBLIC"] is True, target will be the user
    :returns: A list with only the selected severity, or the server + internal messages or everything if 'off'.
    If 'target' is invalid, still returns everything, but add an entry regarding the error
    """
    if filter_by is None:
        filter_by = "off"
    server_name = defaults["INTERNAL"]["SERVER_NAME"]
    cur_user = authenticated_user_is()
    if logger_config["PUBLIC"] is False and logger_config["LOGIN"] is True and cur_user is not None:
        user = cur_user.url
        if filter_by != "off":
            if filter_by == 'severity':      # Filter by severity and user + internal
                return [entry for entry in entry_list if entry.severity.casefold() == target.casefold() and
                        (entry.log_from == user or entry.log_from == server_name)]
            elif filter_by == 'from':        # Filter by name, but always include internals
                return [entry for entry in entry_list if (user in entry.log_from or entry.log_from == server_name)]
            else:                            # Unknown filter
                log_internal(severity="Error", comment=f"Filter '{filter_by}' targeting '{target}' is invalid")
                return [entry for entry in entry_list if (user in entry.log_from or entry.log_from == server_name)]
        else:
            return [entry for entry in entry_list if (user in entry.log_from or entry.log_from == server_name)]
    else:
        if filter_by.casefold() != "off":
            if filter_by == 'severity':      # Filter by severity
                return [entry for entry in entry_list if entry.severity.casefold() == target.casefold()]
            elif filter_by == 'from':        # Filter by name, but always include internals
                return [entry for entry in entry_list if (target in entry.log_from or entry.log_from == server_name)]
            else:                            # Unknown filter
                log_internal(severity="Error", comment=f"Filter '{filter_by}' targeting '{target}' is invalid")
                return entry_list
        else:
            return entry_list


def log_add(s_from="Unknown", severity="Information", comment="Not Specified", body=None):
    """
    Add an entry log onto the server
    :param s_from: Who sent the entry. It's recommended that it's the url or name in the database
    :param severity: How important is this entry, overall. Database may overwrite the defaults
    :param comment: A brief comment about this entry
    :param body: A JSON body, but in reality, any string, or object, can be used here
    """
    global entry_list
    if s_from not in defaults["INTERNAL"]["SERVER_NAME"] and s_from not in servers_list:
        ip = flask.request.remote_addr
        if add_server(s_from, None, None, ip) is True:  # New server, but unknown one
            log_internal(severity="Warning", comment=f"Server {servers_list[s_from][2]} from '{s_from}' was set",
                         body={s_from: servers_list[s_from]})
            print_verbose(sender=__name__,
                          message=f"Server {servers_list[s_from][2]} from '{s_from}' was set")
    print_verbose(sender=__name__, message=f"Added entry: '{s_from}' -> ('{severity}', '{comment}', '{body}')")
    entry_list.append(LogEntry(s_from, severity, comment, body))


def log_internal(severity="Information", comment="Not Specified", body=None):
    """
    Adds an entry log onto the server, explicitly as being internal
    :param severity: How important is this entry, overall. Database may overwrite the defaults
    :param comment: A brief comment about this entry
    :param body: A JSON body, but in reality, any string, or object, can be used here
    """
    log_add(s_from=defaults["INTERNAL"]["SERVER_NAME"], severity=severity, comment=comment, body=body)
    entry_list[-1].is_internal = True


def log_internal_echo(severity="Information", comment="Not Specified", body=None, sender=__name__):
    """
    Adds and entry explicitly as being internal and 'echos' it trough verbose, if enabled
    :param severity: How important is this entry, overall. Database may overwrite the defaults
    :param comment: A brief comment about this entry
    :param body: A JSON body, but in reality, any string, or object, can be used here
    :param sender: The module that sent the message. If it matches any entry on 'defaults["INTERFACE"]["CONSOLE"]' this
    message will have that defined color. If not, it will use 'printer_color'
    """
    log_internal(severity=severity, comment=comment, body=body)
    print_verbose(sender=sender, message=comment)


# noinspection PyBroadException
def log_uncaught_exception(exc: str, body_json, module: str):
    """
    Adds an entry log onto the server, explicitly as being internal and reporting an unhandled exception at 'module'
    :param exc: The exception that wasn't handled correctly
    :param body_json: Additional information about the issue
    :param module: The module that invoked this entry
    """
    try:
        log_internal(severity="Critical", comment=f"[{module.upper()}] Uncaught exception: '{exc}'", body=body_json)
    except Exception as exc2:
        new_body = {"original_body": body_json, "additional_exception": str(exc2)}
        log_internal(severity="Critical", body=new_body,
                     comment=f"[UNKNOWN] Uncaught exception: '{exc}'\nAdditionally, module name was invalid")


def add_severity(severity_name: str, color, backcolor, allow_replace=False, log_suppress=False):
    """
    Add a new severity to the list of severities.
    :param severity_name: The name of the severity, always lowercase (enforced)
    :param color: Text color in the format '#RRGGBB'
    :param backcolor: Background color in the format '#RRGGBB'
    :param allow_replace: If True, if 'severity_name' matches, will replace the old entry with this one (default False)
    :param log_suppress: If True, will not make log entries on warnings. Only set to True during server initialization
    (Will still produce verbose if enabled)
    :returns: True if the severity was added (new) and False if it didn't
    """
    global severities
    try:
        if severity_name is not None:
            if severity_name.lower() not in severities or allow_replace is True:
                severities[severity_name] = (color, backcolor)
                msg = f"Added new severity class"
                if allow_replace:
                    msg = f"Set severity class"
                if log_suppress is False:
                    log_internal(severity="Success", comment=msg, body={severity_name: severities[severity_name]})
                print_verbose(sender=__name__, message=msg)
                return True
            else:
                msg = f"Severity '{severity_name}' already exists and wasn't allowed to be replaced"
                if log_suppress:
                    print_verbose(sender=__name__, message=msg + " (Entry Suppressed)")
                else:
                    log_internal_echo(severity="Warning", comment=msg, sender=__name__,
                                      body={'current': {severity_name: severities[severity_name]},
                                            'new': {severity_name: (color, backcolor)}})
        else:
            msg = "Severity didn't had a valid name and was ignored"

            log_internal_echo(severity="Attention", comment=msg, sender=__name__,
                              body={'severity': severity_name, 'color': color, 'backcolor': backcolor})
            return False
    except (KeyError, ValueError):
        msg = f"Severity {severity_name} had invalid data and was ignored"
        log_internal_echo(severity="Error", comment=msg, sender=__name__,
                          body={'severity': severity_name, 'color': color, 'backcolor': backcolor})
        return False
    except Exception as exc:
        log_uncaught_exception(str(exc), None, __name__)
        return False


def add_server(url: str, color, backcolor, name: str, allow_replace=False, log_suppress=False):
    """
    Add an url to the known server's list
    :param url: The new url (user) to add
    :param color: The new user's (text) color
    :param backcolor: The new user's background color
    :param name: The new user's nickname
    :param allow_replace: If True, if 'url' matches, will replace the old entry with this one (default False)
    :param log_suppress: If True, will not make log entries on warnings. Only set to True during server initialization
    (Will still produce verbose if enabled)
    :returns: True if the server was added (new) and False if it didn't
    """
    global servers_list
    try:
        if url is not None:
            if url not in servers_list or allow_replace:  # New server, but unknown one. Add it temporarily
                servers_list[url] = (color, backcolor, name)
                change_type = "Added new"
                if allow_replace:
                    change_type = "Set"
                if log_suppress is False:
                    log_internal(severity="Success", comment=f"{change_type} server", body={url: servers_list[url]})
                print_verbose(sender=__name__, message=f"{change_type} server '{url}'")
                return True
            else:
                msg = f"Server {url} already exists and wasn't allowed to be replaced"
                if log_suppress:
                    print_verbose(sender=__name__, message=msg + " (Entry Suppressed)")
                else:
                    log_internal_echo(severity="Warning", comment=msg, sender=__name__,
                                      body={'current': {url: servers_list[url]},
                                            'new': {url: (color, backcolor, name)}})
                return False
        else:
            msg = f"Server {name} didn't had a valid url and was ignored"
            log_internal_echo(severity="Attention", comment=msg, sender=__name__,
                              body={'url': url, 'color': color, 'backcolor': backcolor, 'name': name})
            return False
    except (KeyError, ValueError):
        log_internal_echo(severity="Error", comment=f"Server {name} had invalid data and was ignored", sender=__name__,
                          body={'url': url, 'color': color, 'backcolor': backcolor, 'name': name})
        return False
    except Exception as exc:
        log_uncaught_exception(str(exc), None, __name__)
        return False


class LogEntry:
    def __init__(self, s_from="Unknown", severity="Information", comm="Not Specified", body=None):
        global global_id
        self.msg_id = global_id
        self.log_from = s_from
        self.nickname = nickname(s_from)
        self.severity = severity
        self.comment = comm
        self.timestamp = datetime.now().strftime("%H:%M:%S.%f - %d/%m/%Y")
        self.body = body
        self.is_internal = False    # Only true if the entry was sent BY THE SERVER. Don't manually change this
        global_id += 1

    # Returns the whole entry as a JSON object to be used when rendering the page
    def json(self):
        full_name = self.log_from + (self.nickname if self.nickname is not None else "")
        out = {
            "id": self.msg_id,
            "from": full_name,
            "severity": self.severity,
            "comment": self.comment,
            "timestamp": self.timestamp,
            "body": self.body,
            # Cosmetic hints
            "flavor": {"severity": severity_flavor_keys(self.severity),
                       "user_shade": user_shade_flavor_keys(self.log_from) if
                       self.is_internal is False else defaults["INTERFACE"]["PAGE"]["ACCENT"]}
        }
        return out


def severity_flavor_keys(severity: str):
    """
    Fetches a 'flavor' color that matches the 'severity' described
    :param severity: A severity to grab it's corresponding colors
    :return: A 'flavor', which is a css3 style string of color and background-color
    """
    flavor = ""
    try:
        sev = severity.lower()
        if sev in severities:
            colors = severities[sev]
            if colors[0] is not None:
                flavor += f"color:{colors[0]};"
            if colors[1] is not None:
                flavor += f"background-color:{colors[1]};"
    except KeyError:
        pass    # Just ignore
    except Exception as exc:
        log_uncaught_exception(str(exc), None, __name__)
    return flavor


# If more users want colors, add them here, but NEVER add the "Internal", that should be handled manually!
def user_shade_flavor_keys(user_shade: str):
    """
    Fetches a 'flavor' color that matches the user requested
    :param user_shade: A user's url (from field) to grab it's corresponding colors
    :return: A 'flavor', which is a css3 style string of color and background-color
    """
    flavor = ""
    try:
        if user_shade in servers_list:
            colors = servers_list[user_shade]
            if colors[0] is not None:
                flavor += f"color:{colors[0]};"
            if colors[1] is not None:
                flavor += f"background-color:{colors[1]};"
    except KeyError:
        pass    # Just ignore
    except Exception as exc:
        log_uncaught_exception(str(exc), None, __name__)
    return flavor


def nickname(url: str):
    """
    Adds a nickname on the user's url (from field) if they are known
    :param url: The user's url (from field)
    :return: '( {Nickname / User's name} )'
    """
    try:
        if url in servers_list:
            return " (" + servers_list[url][2] + ")"
    except KeyError:
        log_internal(severity="Error", comment="Known server list's 'url' key is missing!")
    except Exception as exc:
        log_uncaught_exception(str(exc), None, __name__)
    return None
