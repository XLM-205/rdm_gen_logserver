from datetime import datetime
import flask
import flask_login

from flask import request
from server_config import defaults, log_config, print_format
from classes import severities, known_list, add_known_list

entry_list = []     # All of our entries
global_id = 0       # Global Entry Identifier


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
    if log_config["PUBLIC"] is False and log_config["LOGIN"] is True:
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


def log_add(s_from="Unknown", severity="Information", comment="Not Specified", body=None, internal=False):
    """
    Add an entry log onto the server
    :param s_from: Who sent the entry. It's recommended that it's the url or name in the database
    :param severity: How important is this entry, overall. Database may overwrite the defaults
    :param comment: A brief comment about this entry
    :param body: A JSON body, but in reality, any string, or object, can be used here
    :param internal: True if the entry is coming from the server itself. It's not recommended to set it to True
    """
    global entry_list
    is_new = False
    entry_list.append(LogEntry(s_from, severity, comment, body))
    if s_from not in known_list and internal is False:    # New server, but unknown one. Add it temporarily
        add_known_list(s_from, None, None, f"{flask.request.remote_addr}")
        log_internal(severity="Warning", comment=f"New server '{s_from}' ({known_list[s_from][2]}) added")
        is_new = True
    if log_config["VERBOSE"]:
        print_format(f"[ENTRY MANAGER] Added (from:'{s_from}', '{severity}', '{comment}', body:{body})",
                     color=defaults["CC"]["ENTRY_MANAGER"])
        if is_new:
            print_format(f"[ENTRY MANAGER] Added new server '{s_from}' ({known_list[s_from][2]})",
                         color=defaults["CC"]["ENTRY_MANAGER"])


def log_internal(severity="Information", comment="Not Specified", body=None):
    """Adds an entry log onto the server, explicitly as being internal"""
    log_add(s_from=defaults["INTERNAL"]["SERVER_NAME"], severity=severity, comment=comment, body=body, internal=True)
    entry_list[-1].flavor["user_shade"] = defaults["UI"]["ACCENT"]


def log_uncaught_exception(exc, body_json):
    """Adds an entry log onto the server, explicitly as being internal and reporting an unhandled exception"""
    log_internal(severity="Critical", comment=f"Uncaught exception: '{exc}'", body=body_json)


class LogEntry:
    def __init__(self, s_from="Unknown", severity="Information", comm="Not Specified", body=None):
        global global_id
        self.msg_id = global_id
        self.log_from = s_from + nickname(s_from)
        self.severity = severity
        self.comment = comm
        self.timestamp = datetime.now().strftime("%H:%M:%S.%f - %d/%m/%Y")
        self.body = body
        self.flavor = {  # Cosmetic hints
            "severity": severity_flavor_keys(severity),
            "user_shade": user_shade_flavor_keys(s_from)
        }
        global_id += 1

    # Returns the whole entry as a JSON object to be used when rendering the page
    def json(self):
        out = {
            "id": self.msg_id,
            "from": self.log_from,
            "severity": self.severity,
            "comment": self.comment,
            "timestamp": self.timestamp,
            "body": self.body,
            "flavor": self.flavor
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
        usr = user_shade.lower()
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
            return "( " + known_list[url][2] + " )"
    except KeyError:
        log_internal(severity="Error", comment="Known server list's 'url' key is missing!")
    except Exception as exc:
        log_uncaught_exception(str(exc), request.json)
    return ""
