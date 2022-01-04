import os
import routes
from flask_login import LoginManager
from flask_sslify import SSLify
from flask import Flask

from classes import fetch_db, db, severities, known_list, Users
from server_config import log_config, print_format, defaults
from entry_manager import log_uncaught_exception, log_internal
from utils import fill_simulate


def server_init(is_pre_init: bool):
    init_set = log_config["PRE_INIT"] if is_pre_init else log_config["POST_INIT"]
    order = "Pre" if is_pre_init else "Post"
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
        print_format(f"[INIT] {order} Initialization complete", color=defaults["CC"]["INIT"])


def create_app():
    app = Flask(__name__)
    # Pre initialization phase
    with app.app_context():
        server_init(is_pre_init=True)

    db_uri = os.environ.get("DATABASE_URL", defaults["FALLBACK"]["DB_URL"])
    # Fixing deprecated convention Heroku still uses
    if db_uri is None:
        db_uri = ""
    db_uri = db_uri.replace("postgres://", "postgresql://", 1)

    if 'DYNO' in os.environ:  # Only invoke SSL if on Heroku (not local)
        SSLify(app)
    else:
        db_uri = defaults["FALLBACK"]["DB_URL"]
        app.config["DEBUG"] = True  # If local, allow debug
        log_config["POST_INIT"].append((log_internal, ("Attention", "Log Server running on DEBUG mode")))
    app.config["SECRET_KEY"] = os.environ.get("SKEY", os.urandom(32).hex())  # For encrypting passwords during execution
    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return Users.query.get(int(user_id))

    app.register_blueprint(routes.auth)
    app.register_blueprint(routes.main)
    with app.app_context():
        if db_uri is not None and db_uri != "":
            fetch_db()
        else:
            log_config["POST_INIT"].append((log_internal, ("Attention", "Log Server running WITHOUT Database support")))

        log_config["POST_INIT"].append((log_internal, ("Success", "Log Server Started successfully")))
        server_init(is_pre_init=False)

    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", defaults["FALLBACK"]["PORT"])), use_reloader=False)


if __name__ == "__main__":
    log_config["VERBOSE"] = True
    # log_config["POST_INIT"].append((fill_simulate, (100, severities, known_list)))
    create_app()
