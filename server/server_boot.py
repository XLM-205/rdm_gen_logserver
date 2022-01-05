import os
import routes
from flask_login import LoginManager
from flask_sslify import SSLify
from flask import Flask

from classes import fetch_db, db, Users, known_list
from server_config import log_config, print_format, defaults, private_info_fill
from entry_manager import log_uncaught_exception, log_internal


def server_init(is_pre_init: bool):
    """
    Executes all of the server's pre and post initialization tasks defined (if any)

    :param is_pre_init: If True, then we're executing the pre initialization. If False, then it's post
    """
    init_set = log_config["PRE_INIT"] if is_pre_init else log_config["POST_INIT"]
    order = "Pre" if is_pre_init else "Post"
    if log_config["VERBOSE"]:
        print_format(f"[SERVER BOOT] {order} Initialization starting...", color=defaults["CC"]["SERVER_BOOT"])
        if not init_set:
            print_format(f"[SERVER BOOT] {order} Initialization skipped (No task)", color=defaults["CC"]["SERVER_BOOT"])
            return
    for func in init_set:
        try:
            if func is None:
                log_internal(severity="Warning", comment=f"Empty argument passed to {order} Initialization was ignored")
                continue
            elif type(func) is tuple:
                if type(func[1]) is tuple:
                    func[0](*func[1])
                else:
                    func[0](func[1])
            else:
                func()
        except IndexError:
            log_internal(severity="Error", body=func,
                         comment=f"Error during {order} Initialization of {func[0]}({func[1]})")
        except TypeError:
            log_internal(severity="Error", body=func,
                         comment=f"Error during {order} Initialization of {func[0]}({func[1]})")
        except Exception as exc:
            log_uncaught_exception(str(exc), func)
    if log_config["CLEAR_INIT"]:
        init_set.clear()
    if log_config["VERBOSE"]:
        print_format(f"[SERVER BOOT] {order} Initialization complete", color=defaults["CC"]["SERVER_BOOT"])


def create_app():
    """Starts, initializes the server and connects the database"""
    app = Flask(__name__)
    # Pre initialization phase
    with app.app_context():
        if log_config["LOAD_PRIVATE"]:
            private_info_fill()
        server_init(is_pre_init=True)

    db_uri = os.environ.get("DATABASE_URL", defaults["FALLBACK"]["DB_URL"])
    # Fixing deprecated convention Heroku still uses
    if db_uri is None:
        db_uri = ""
    db_uri = db_uri.replace("postgres://", "postgresql://", 1)

    if 'DYNO' in os.environ:  # Only invoke SSL if on Heroku (not local)
        SSLify(app)
    else:
        if db_uri is None or db_uri == "":
            db_uri = defaults["FALLBACK"]["DB_URL"]
        # app.debug = True
        # app.config["DEBUG"] = True  # If local, allow debug
        log_config["POST_INIT"].append((log_internal, ("Attention", "Log Server running on DEBUG mode")))
    app.config["SECRET_KEY"] = os.environ.get("SKEY", os.urandom(32).hex())  # For encrypting passwords during execution
    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    app.register_blueprint(routes.auth)
    app.register_blueprint(routes.main)

    with app.app_context():
        if db_uri is not None and db_uri != "":
            db.init_app(app)
            login_manager = LoginManager()
            login_manager.login_view = 'auth.login'
            login_manager.init_app(app)

            @login_manager.user_loader
            def load_user(user_id):
                return Users.query.get(int(user_id))
            fetch_db()
        else:
            log_config["POST_INIT"].append((log_internal, ("Attention", "Log Server running WITHOUT Database support")))
            log_config["LOGIN"] = False     # If we don't have a database, we can't login

        # Final checks and warnings
        if log_config["LOGIN"] is False:
            login_mode_msg = "Log Server DON'T REQUIRE Login"
            app.config["LOGIN_DISABLED"] = True
            if log_config["VERBOSE"]:
                print_format(f"[SERVER BOOT] {login_mode_msg}", color=defaults["CC"]["SERVER_BOOT"])
            log_config["POST_INIT"].append((log_internal, ("Warning", login_mode_msg)))

        if log_config["PUBLIC"] is True:
            public_mode_msg = "Log Server IS Public"
            if log_config["VERBOSE"]:
                print_format(f"[SERVER BOOT] {public_mode_msg}", color=defaults["CC"]["SERVER_BOOT"])
            log_config["POST_INIT"].append((log_internal, ("Warning", public_mode_msg)))

        log_config["POST_INIT"].append((log_internal, ("Success", "Log Server Started successfully")))
        server_init(is_pre_init=False)
        known_list["LogServer"] = defaults["INTERNAL"]["SERVER_NAME"]   # Add the server as an filter option

    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", defaults["FALLBACK"]["PORT"])), use_reloader=False)
