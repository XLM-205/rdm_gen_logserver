import json
import flask
from flask_login import login_required, logout_user
from werkzeug.exceptions import BadRequest
from flask import Blueprint, request, render_template, url_for, redirect

from server_config import defaults, logger_config
from entry_manager import log_count, log_purge, log_add, log_get, log_internal, log_uncaught_exception, \
                          add_severity, add_known_list
from paging import prepare_page, serve_page
from security import attempt_login

auth = Blueprint("auth", __name__)
main = Blueprint("main", __name__)


@main.route('/server/status', methods=["GET"])   # Used to fetch data
@login_required
def server_fetch():
    internal = {
        "entry_count": log_count(),
        # "services_timedout": is_service_locked
    }
    return json.dumps(internal), 200


@main.route('/log/clear', methods=["POST"])
@login_required
def clear_logs():
    try:
        req = request.json
        try:
            req_from = req["from"]
        except KeyError:
            return "The 'from' field MUST be filled before clearing the logs", 403
        try:
            req_comm = req["comment"]
        except KeyError:
            req_comm = "Log Clear Request"
        log_purge()
        log_add(s_from=req_from, severity="Information", comment=req_comm)
        return show_recent_entries()
    except BadRequest:
        return "Bad Request Ignored", 400


@main.route('/log', methods=["POST"])
@login_required
def add_entry():
    try:
        req = request.json
        req_severity = "Unknown"
        req_comm = "Not Specified"
        req_body = {}
        inputs = 3
        try:
            req_from = req["from"]
            if req_from is None or req_from == "":
                return "Bad Entry Ignored", 400
        except KeyError:
            return "Bad Entry Ignored", 400
        try:
            req_severity = req["severity"]
        except KeyError:
            inputs -= 1
        try:
            req_comm = req["comment"]
        except KeyError:
            inputs -= 1
        try:
            req_body = req["body"]
        except KeyError:
            inputs -= 1
        if inputs > 0:
            log_add(s_from=req_from, severity=req_severity, comment=req_comm, body=req_body)
            return show_recent_entries()
        else:
            return "Empty Entry Ignored", 400
    except BadRequest:
        return "Bad Entry Ignored", 400


@main.route('/')
@login_required
def home_page():
    return redirect(url_for("main.show_recent_entries"))


@main.route('/log', methods=['GET'])
@login_required
def show_recent_entries():
    # handle_log_services() # Disabled on this version
    filter_type = None if request.args.get("f") == "None" else request.args.get("f")
    filter_target = None if request.args.get("ftgt") == "None" else request.args.get("ftgt")
    entries = log_get(filter_type, filter_target)[::-1]

    out, cur_page, max_page, per_page = prepare_page(len(entries), filter_type, filter_target)

    for entry in entries[(cur_page - 1) * per_page:]:
        out["entries"].append(entry.json())
        if len(out["entries"]) == per_page:
            break
    return serve_page(out, 200)


@main.route('/log/old', methods=['GET'])
@login_required
def show_entries():
    # handle_log_services() # Disabled on this version
    filter_type = None if request.args.get("f") == "None" else request.args.get("f")
    filter_target = None if request.args.get("ftgt") == "None" else request.args.get("ftgt")
    entries = log_get(filter_type, filter_target)

    out, cur_page, max_page, per_page = prepare_page(len(entries), filter_type, filter_target)

    for entry in entries[(cur_page - 1) * per_page:]:
        out["entries"].append(entry.json())
        if len(out) == per_page:
            break
    return serve_page(out, 200)


@main.route('/set', methods=['POST'])
def set_info():
    try:
        req = request.json
        key_name = "name"
        key_color = "color"
        key_backcolor = "backcolor"
        key_url = "url"
        try:
            req_type = req["type"].lower()
        except KeyError:
            return redirect(url_for("main.show_recent_entries"))
        try:
            if req_type == "severity":
                add_severity(req[key_name].lower(), req[key_color], req[key_backcolor], allow_replace=True)
            elif req_type == "server":
                add_known_list(req[key_url], req[key_color], req[key_backcolor], req[key_name], allow_replace=True)
                log_internal(severity="Success", comment=f"Added a new server '{req[key_url]}' ({req[key_name]})")
        except KeyError:
            return redirect(url_for("main.show_recent_entries"))
    except ValueError:
        log_internal(severity="Attention", comment="Invalid value received when setting data", body=request.json)
    except TypeError:
        log_internal(severity="Error", comment="Request have an invalid type", body=request.json)
    except Exception as exc:
        log_uncaught_exception(str(exc), request.json)
    finally:
        return redirect(url_for("main.show_recent_entries"))


@main.route('/info', methods=['GET'])
def info():
    out = {
        "component": "General Purpose Log Server",
        "version": defaults["INTERNAL"]["VERSION"],
        "description": "Provides a public, standardized and easy to use visual log interface",
        "access_point": defaults["INTERNAL"]["ACCESS_POINT"],
        "about": ["Fully coded, back & front by Ramon Darwich de Menezes", "https://github.com/XLM-205",
                  "http://lattes.cnpq.br/2510824092604238"],
        # "databases": {
        #    "servers": {
        #        "known_servers": None,
        #        "secondary_servers": secondary_servers
        #    }
        # }
    }
    return json.dumps(out), 418


@auth.route("/login", methods=["GET"])
def login():
    if logger_config["LOGIN"] is True:
        return render_template("login.html")
    else:
        return redirect(url_for("main.show_recent_entries"))


@auth.route("/login", methods=["POST"])
def login_post():
    if logger_config["LOGIN"] is True:
        log_in = request.form.get("log_in")
        wp = request.form.get("password")
        remember = True if request.form.get("remember") else False
        return attempt_login(log_in, wp, flask.request.remote_addr, remember=remember)
    else:
        return redirect(url_for("main.show_recent_entries"))


@auth.route("/login/cli", methods=["POST"])
def login_post_cli():
    if logger_config["LOGIN"] is True:
        try:
            req = request.json
            remember = False
            try:
                usr = req["user"]
            except KeyError:
                return "Bad Login", 400
            try:
                wp = req["webpass"]
            except KeyError:
                return "Bad Login", 400
            try:
                remember = req["remember"]
            except KeyError:
                pass    # Just ignore
            return attempt_login(usr, wp, flask.request.remote_addr, remember)
        except BadRequest:
            return "Bad Login", 400
    else:
        return redirect(url_for("main.show_recent_entries"))


@auth.route("/logout", methods=["GET"])
def logout():
    if logger_config["LOGIN"] is True:
        logout_user()
        return redirect(url_for("auth.login"))
    else:
        return redirect(url_for("main.show_recent_entries"))
