from flask import request, render_template
import datetime
from typing import Tuple

from classes import severities, known_list
from server_config import defaults
from entry_manager import log_count, filters_available, log_get, log_get_filtered


def get_page_format() -> Tuple[int, int, int, int, str, str]:
    """Returns the page, max page and epp based on the url arguments"""
    try:
        fltr = request.args.get("f")
        fltr_tgt = request.args.get("ftgt")
        if (fltr is not None and fltr in filters_available) and fltr_tgt is not None:
            entry_count = len(log_get_filtered(fltr, fltr_tgt))
        else:
            fltr = "off"
            fltr_tgt = None
            entry_count = len(log_get())
    except ValueError:  # Field 'epp=" was too big
        entry_count = len(log_get())
        fltr = "off"
        fltr_tgt = None
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
    return cur_page, max_page, per_page, entry_count, fltr, fltr_tgt


def prepare_page() -> Tuple[dict, int, int, int]:
    """ Compute and prepares the variables used when rendering the page.
    :returns:
    dict: A tuple containing the information from the server in a dict, including current page, maximum amount of
          pages, Entries Per Page, the count of entries stored, the last update time and the entry list
    int: The current page being served
    int: The farthest page that can be reached
    int: Amount of entries displayed per page
    """
    cur_page, max_page, per_page, entries_count, fltr, fltr_tgt = get_page_format()
    entries_total = log_count()
    out = {
        "page": (cur_page if entries_count > 0 else 0),
        "page_max": max_page,
        "epp": per_page,
        "count": entries_count,
        "total": entries_total,
        "last_update": datetime.datetime.now().strftime("%H:%M:%S - %d/%m/%Y"),
        "entries": [],
        "filter": fltr,
        "filter_target": fltr_tgt,
        "severities": severities,
        "servers": known_list
    }
    return out, cur_page, max_page, per_page


def serve_page(json_data, return_code):
    return render_template("log_table_flask.html", data=json_data), return_code
