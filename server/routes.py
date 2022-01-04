import datetime
import json

import flask
import sqlalchemy
from flask_login import login_required, login_user, logout_user
from werkzeug.exceptions import BadRequest
from werkzeug.utils import redirect
from flask import Blueprint, request, flash, render_template, url_for

from entry_manager import log_count, log_purge, log_add, log_get, log_get_filtered, filters_available
from paging import prepare_page, serve_page
from classes import Users
from server_config import defaults, print_format, log_config
from utils import injection_guard, InjectionToken

auth = Blueprint("auth", __name__)
main = Blueprint("main", __name__)

# Holds all ips that tried to connect "{IP}": [tries: int, locked: bool, lock_until: datetime]
login_attempts = {}


def try_login(log_in, wp):
    try:
        injection_guard([log_in, wp])
        user = Users.authenticate(log_in, wp)
    except InjectionToken:
        # Probable SQL Injection attack!
        # log_critical(f"SQL Injection identified from {flask.request.remote_addr} !", {"log_in": log_in, "wp": wp})
        flash("Login information had invalid characters")
        return None
    except sqlalchemy.exc.ProgrammingError:
        # Probable SQL Injection attack!
        # log_critical(f"SQL Injection identified from {flask.request.remote_addr} !", {"log_in": log_in, "wp": wp})
        flash("Login information had invalid characters")
        return None
    except (sqlalchemy.exc.NoSuchColumnError, AttributeError, TypeError):
        flash("Invalid Login Attempt")
        return None
    return user


def attempt_login(log_in, wp, ip_addrss, remember=False):
    # Safeguarding against brute force
    # 403 -> Known IP
    if ip_addrss in login_attempts:     # User is known
        if login_attempts[ip_addrss][1] is False:
            # User not locked. Attempt login
            user = try_login(log_in, wp)
        elif login_attempts[ip_addrss][2] <= datetime.datetime.now():
            # User is locked, but his lock have expired
            login_attempts[ip_addrss][0] = 0
            login_attempts[ip_addrss][1] = False
            user = try_login(log_in, wp)
        else:
            if log_config["VERBOSE"]:
                print_format(f"[ROUTES] IP {ip_addrss} is still locked until {login_attempts[ip_addrss][2]}",
                             color=defaults["CC"]["ROUTES"])
            return redirect("/login"), 403
    else:   # User is unknown
        login_attempts[ip_addrss] = [0, False, None]
        user = try_login(log_in, wp)

    # Attempting login
    if user is None:
        login_attempts[ip_addrss][0] += 1
        if login_attempts[ip_addrss][0] >= defaults["SECURITY"]["LOGIN"]["MAX_TRIES"]:  # Lock user
            lockout = datetime.datetime.now() + datetime.timedelta(seconds=defaults["SECURITY"]["LOGIN"]["LOCKOUT"])
            login_attempts[ip_addrss][1] = True
            login_attempts[ip_addrss][2] = lockout
            if log_config["VERBOSE"]:
                print_format(f"[ROUTES] IP {ip_addrss} is locked until {login_attempts[ip_addrss][2]}",
                             color=defaults["CC"]["ROUTES"])
        flash("Invalid Login")
        if log_config["VERBOSE"]:
            print_format(f"[ROUTES] IP {ip_addrss} failed to login (Attempt {login_attempts[ip_addrss][0]})",
                         color=defaults["CC"]["ROUTES"])
        return redirect("login"), 406
    login_attempts[ip_addrss][0] = 0
    login_attempts[ip_addrss][1] = False
    if log_config["VERBOSE"]:
        print_format(f"[ROUTES] IP {ip_addrss} logged in successfully",
                     color=defaults["CC"]["ROUTES"])
    login_user(user, remember=remember)
    return redirect("/"), 200


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
        req_from = "Unknown"
        req_comm = "Not Specified"
        req_body = {}
        inputs = 4
        try:
            req_severity = req["severity"]
        except KeyError:
            inputs -= 1
        try:
            req_from = req["from"]
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


@main.route("/")
@login_required
def home_page():
    return redirect("/log")


@main.route('/log', methods=['GET'])
@login_required
def show_recent_entries():
    # handle_log_services() # Disabled on this version
    out, cur_page, max_page, per_page = prepare_page()
    try:
        fltr = request.args.get("f")
        fltr_tgt = request.args.get("ftgt")
        if (fltr is not None and fltr in filters_available) and fltr_tgt is not None:
            rev = log_get_filtered(fltr, fltr_tgt)[::-1]
        else:
            rev = log_get()[::-1]
    except ValueError:
        rev = log_get()[::-1]

    for entry in rev[(cur_page - 1) * per_page:]:
        out["entries"].append(entry.json())
        if len(out["entries"]) == per_page:
            break
    return serve_page(out, 200)


@main.route('/log/old', methods=['GET'])
@login_required
def show_entries():
    # handle_log_services() # Disabled on this version
    out, cur_page, max_page, per_page = prepare_page()
    try:
        fltr = request.args.get("f")
        fltr_tgt = request.args.get("ftgt")
        if (fltr is not None and fltr in filters_available) and fltr_tgt is not None:
            rev = log_get_filtered(fltr, fltr_tgt)[(cur_page - 1) * per_page:]
        else:
            rev = log_get()[(cur_page - 1) * per_page:]
    except ValueError:
        rev = log_get()[(cur_page - 1) * per_page:]

    for entry in rev:
        out["entries"].append(entry.json())
        if len(out["entries"]) == per_page:
            break
    return serve_page(out, 200)


# noinspection PyBroadException
# @main.route('/info', methods=['POST'])
# def set_info():
#    global secondary_servers
#    try:
#        if "secondary_servers" in request.json:
#            secondary_servers = request.json["secondary_servers"]
#    except ValueError:
#        internal_log(severity="Attention", comment="Invalid value received when setting data", body=request.json)
#    except TypeError:
#        internal_log(severity="Error", comment="Request have an invalid type", body=request.json)
#    except Exception as exc:
#        log_uncaught_exception(str(exc), request.json)


@main.route('/info', methods=['GET'])
def info():
    out = {
        "note": "Wrong server for that, pal ;)",
        "componente": "Log Server",
        "versao": "1.2.0",
        "descricao": "Provides a public, standardized and easy to use visual log interface",
        "ponto_de_acesso": "https://sd-log-server.herokuapp.com",
        "status": "Always up",
        "identificacao": -1,
        "lider": 0,
        "eleicao": "All of them ;)",
        "sobre": ["Fully coded, back & front by Ramon Darwich de Menezes", "https://github.com/XLM-205",
                  "http://lattes.cnpq.br/2510824092604238"],
        "databases": {
            "servers": {
                "known_servers": None,
                # "secondary_servers": secondary_servers
            }
        }
    }
    return json.dumps(out), 418


@auth.route("/login", methods=["GET"])
def login():
    return render_template("login.html")


@auth.route("/login", methods=["POST"])
def login_post():
    log_in = request.form.get("log_in")
    wp = request.form.get("password")
    remember = True if request.form.get("remember") else False
    return attempt_login(log_in, wp, flask.request.remote_addr, remember=remember)


@auth.route("/login/cli", methods=["POST"])
def login_post_cli():
    try:
        req = request.json
        usr = "Unknown"
        wp = "Unknown"
        remember = False
        inputs = 2
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


@auth.route("/logout", methods=["GET"])
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
