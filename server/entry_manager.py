import flask
import flask_login
from flask import request
from datetime import datetime

from console_printers import print_verbose
from server_config import defaults, logger_config

entry_list = []     # All of our entries
global_id = 0       # Global Entry Identifier
# Severities classes (FG Color, BG Color). The key is the severity
severities = defaults["SEVERITIES"]            # Severity name, color and backcolor
known_list = defaults["SERVERS"]               # User list with proper name, color, backcolor and expected URL
db_entries = []                                # DB Fetched past entries


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
    if logger_config["PUBLIC"] is False and logger_config["LOGIN"] is True:
        user = flask_login.current_user.url
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
    if s_from != defaults["INTERNAL"]["SERVER_NAME"] and s_from not in known_list:
        ip = flask.request.remote_addr
        if add_known_list(s_from, None, None, ip) is True:  # New server, but unknown one
            log_internal(severity="Warning", comment=f"Server {known_list[s_from][2]} from '{s_from}' was set",
                         body={s_from: known_list[s_from]})
            print_verbose(sender=__name__,
                          message=f"Server {known_list[s_from][2]} from '{s_from}' was set")
    entry_list.append(LogEntry(s_from, severity, comment, body))


def log_internal(severity="Information", comment="Not Specified", body=None):
    """Adds an entry log onto the server, explicitly as being internal"""
    log_add(s_from=defaults["INTERNAL"]["SERVER_NAME"], severity=severity, comment=comment, body=body)
    entry_list[-1].is_internal = True


def log_uncaught_exception(exc, body_json):
    """Adds an entry log onto the server, explicitly as being internal and reporting an unhandled exception"""
    log_internal(severity="Critical", comment=f"Uncaught exception: '{exc}'", body=body_json)


def add_severity(severity_name: str, color, backcolor, allow_replace=False):
    """
    Add a new severity to the list of severities.
    :param severity_name: The name of the severity, always lowercase (enforced)
    :param color: Text color in the format '#RRGGBB'
    :param backcolor: Background color in the format '#RRGGBB'
    :param allow_replace: If True, if 'severity_name' matches, will replace the old entry with this one (default False)
    :returns: True if the severity was added (new) and False if it didn't
    """
    global severities
    if severity_name is not None and (severity_name.lower() not in severities or allow_replace is True):
        severities[severity_name] = (color, backcolor)
        change_type = "Added new"
        if allow_replace:
            change_type = "Set"
        log_internal(severity="Success", comment=f"{change_type} severity class",
                     body={severity_name: severities[severity_name]})
        print_verbose(sender=__name__, message=f"{change_type} severity class '{severity_name}'")
        return True
    else:
        return False


def add_known_list(url: str, color, backcolor, name: str, allow_replace=False):
    """
    Add an url to the known server's list
    :param url: The new url (user) to add
    :param color: The new user's (text) color
    :param backcolor: The new user's background color
    :param name: The new user's nickname
    :param allow_replace: If True, if 'url' matches, will replace the old entry with this one (default False)
    :returns: True if the server was added (new) and False if it didn't
    """
    global known_list
    if url is not None and (url not in known_list or allow_replace):  # New server, but unknown one. Add it temporarily
        known_list[url] = (color, backcolor, name)
        change_type = "Added new"
        if allow_replace:
            change_type = "Set"
        # log_internal(severity="Success", comment=f"{change_type} server", body={url: known_list[url]})
        print_verbose(sender=__name__, message=f"{change_type} server '{url}'")
        return True
    else:
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
    if severity is not None:
        sev = severity.lower()
        if sev in severities:
            colors = severities[sev]
            if colors[0] is not None:
                flavor += f"color:{colors[0]};"
            if colors[1] is not None:
                flavor += f"background-color:{colors[1]};"
    return flavor


# If more users want colors, add them here, but NEVER add the "Internal", that should be handled manually!
def user_shade_flavor_keys(user_shade: str):
    """
    Fetches a 'flavor' color that matches the user requested
    :param user_shade: A user's url (from field) to grab it's corresponding colors
    :return: A 'flavor', which is a css3 style string of color and background-color
    """
    flavor = ""
    if user_shade is not None:
        usr = user_shade
        if usr in known_list:
            colors = known_list[usr]
            if colors[0] is not None:
                flavor += f"color:{colors[0]};"
            if colors[1] is not None:
                flavor += f"background-color:{colors[1]};"
    return flavor


def nickname(url):
    """
    Adds a nickname on the user's url (from field) if they are known
    :param url: The user's url (from field)
    :return: '( {Nickname / User's name} )'
    """
    try:
        if url in known_list:
            return " (" + known_list[url][2] + ")"
    except KeyError:
        log_internal(severity="Error", comment="Known server list's 'url' key is missing!")
    except Exception as exc:
        log_uncaught_exception(str(exc), request.json)
    return None
