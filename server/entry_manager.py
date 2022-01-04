from datetime import datetime
import flask

from flask import request
from server_config import defaults, log_config, print_format
from classes import severities, known_list, add_known_list

filters_available = {"from", "severity"}
entry_list = []     # All of our entries
global_id = 0       # Global Entry Identifier


def log_count():
    return len(entry_list)


def log_purge():
    entry_list.clear()


def log_get_filtered(filter_by: str, target: str):
    """ Returns a list of entries based on the filter
    :param filter_by: 'from', 'severity' will filter by whom sent the entry or the severity of the entry (default 'from')
    :param target: The value to match against
    """
    if filter_by is not None:
        if filter_by == 'severity':      # Filter by severity
            return [entry for entry in entry_list if entry.severity.casefold() == target.casefold()]
        else:                            # Filter by name
            return [entry for entry in entry_list if (target in entry.log_from)]
    return []


def log_get():
    return entry_list


def log_add(s_from="Unknown", severity="Information", comment="Not Specified", body=None, internal=False):
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
    log_add(s_from="Internal", severity=severity, comment=comment, body=body, internal=True)
    entry_list[-1].flavor["user_shade"] = defaults["UI"]["ACCENT"]


def log_uncaught_exception(exc, body_json):
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
    try:
        if url in known_list:
            return "( " + known_list[url][2] + " )"
    except KeyError:
        log_internal(severity="Error", comment="Known server list's 'url' key is missing!")
    except Exception as exc:
        log_uncaught_exception(str(exc), request.json)
    return ""
