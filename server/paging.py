from flask import request, render_template
import datetime
from typing import Tuple

from classes import severities, known_list
from server_config import defaults, log_config
from entry_manager import log_count


def prepare_page(entry_count, filter_type, filter_target) -> Tuple[dict, int, int, int]:
    """ Compute and prepares the variables used when rendering the page.
    :returns:
    dict: A tuple containing the information from the server in a dict, including current page, maximum amount of
          pages, Entries Per Page, the count of entries stored, the last update time and the entry list
    int: The current page being served
    int: The farthest page that can be reached
    int: Amount of entries displayed per page
    list: The list of entries, filtered
    """

    try:
        if request.args.get("epp") is not None and 0 < int(request.args.get("epp")) <= entry_count:
            per_page = int(request.args.get("epp"))
        else:
            per_page = defaults["UI"]["EPP"]
    except ValueError:  # Field 'epp=" was too big
        per_page = defaults["UI"]["EPP"]
    div = entry_count % per_page
    if div == 0:
        max_page = int(entry_count / per_page)
    else:
        max_page = int(entry_count / per_page) + 1
    try:
        if request.args.get("p") is not None and max_page >= int(request.args.get("p")) > 0:
            cur_page = int(request.args.get("p"))
        else:
            cur_page = 1
    except ValueError:  # Field 'p=' wasn't an integer
        cur_page = 1

    entries_total = log_count()
    # Page data
    out = {
        "count": entry_count,
        "entries": [],
        "epp": per_page,
        "filter": filter_type,
        "filter_target": filter_target,
        "last_update": datetime.datetime.now().strftime("%H:%M:%S - %d/%m/%Y"),
        "login": log_config["LOGIN"],
        "page": (cur_page if entry_count > 0 else 0),
        "page_max": max_page,
        "public": log_config["PUBLIC"],
        "severities": severities,
        "servers": known_list,
        "total": entries_total,
    }
    return out, cur_page, max_page, per_page


def serve_page(json_data, return_code):
    """Renders a page template"""
    return render_template("log_table_flask.html", data=json_data), return_code
