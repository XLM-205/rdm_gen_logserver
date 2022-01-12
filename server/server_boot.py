import os
import routes
from flask_login import LoginManager
from flask_sslify import SSLify
from flask import Flask

from db_models import fetch_db, db, Users
from server_config import logger_config, defaults, print_verbose
from entry_manager import servers_list, log_uncaught_exception, log_internal


def server_init(is_pre_init: bool):
    """
    Executes all of the server's pre and post initialization tasks defined (if any)

    :param is_pre_init: If True, then we're executing the pre initialization. If False, then it's post
    """
    init_set = logger_config["PRE_INIT"] if is_pre_init else logger_config["POST_INIT"]
    order = "Pre" if is_pre_init else "Post"
    print_verbose(sender=__name__,
                  message=f"{order} Initialization starting...")
    if not init_set:
        print_verbose(sender=__name__,
                      message=f"{order} Initialization skipped (No task)")
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
            log_uncaught_exception(str(exc), func, __name__)
    if logger_config["CLEAR_INIT"]:
        init_set.clear()
    print_verbose(sender=__name__,
                  message=f"{order} Initialization complete")


def create_app():
    """Starts, initializes the server and connects the database"""
    app = Flask(__name__)
    # Pre initialization phase
    # logger_config["PRE_INIT"].append((log_internal, ("Information", "Log Server is initializing...")))
    with app.app_context():
        if logger_config["LOAD_PRIVATE"]:
            private_info_fill()
            db_uri = defaults["FALLBACK"]["DB_URL"]
        else:
            db_uri = os.environ.get("DATABASE_URL", defaults["FALLBACK"]["DB_URL"])
        server_init(is_pre_init=True)

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
        logger_config["POST_INIT"].append((log_internal, ("Attention", "Log Server running on DEBUG mode")))
    app.config["SECRET_KEY"] = os.environ.get("SKEY", os.urandom(32).hex())  # For encrypting passwords during execution
    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    app.register_blueprint(routes.auth)
    app.register_blueprint(routes.main)

    servers_list["LogServer"] = defaults["INTERNAL"]["SERVER_NAME"]  # Add the server as an filter option
    print_verbose(sender=__name__, message="Initializing Database...")
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return Users.query.get(int(user_id))

    with app.app_context():
        if db_uri is not None and db_uri != "" and logger_config["USE_DB"] is True:
            db.init_app(app)

            fetch_db()
            print_verbose(sender=__name__, message="Database Initialized")
        else:
            db_msg = "Log Server running WITHOUT Database support"
            print_verbose(sender=__name__, message=db_msg)
            logger_config["POST_INIT"].append((log_internal, ("Attention", db_msg)))
            logger_config["LOGIN"] = False     # If we don't have a database, we can't login

        # Final checks and warnings
        if logger_config["LOGIN"] is False:
            login_mode_msg = "Log Server DON'T REQUIRE Login"
            app.config["LOGIN_DISABLED"] = True
            print_verbose(sender=__name__,
                          message=login_mode_msg)
            logger_config["POST_INIT"].append((log_internal, ("Warning", login_mode_msg)))

        if logger_config["PUBLIC"] is True:
            public_mode_msg = "Log Server IS Public"
            print_verbose(sender=__name__,
                          message=public_mode_msg)
            logger_config["POST_INIT"].append((log_internal, ("Warning", public_mode_msg)))

        logger_config["POST_INIT"].append((log_internal, ("Success", "Log Server Started successfully")))
        print_verbose(sender=__name__, message="Server Initialization complete", underline=True)
        server_init(is_pre_init=False)

    return app


def private_info_fill():
    """If you have sensitive data, insert it here. Should reference files ignored by your VCS and local to the deploy.
       \nThis method is custom tailored for each use case and invoking and using it is OPTIONAL."""
    from os import path
    import importlib
    try:
        print_verbose(sender=__name__,
                      message=f"Loading private resources...",
                      underline=True)
        confidential_path = "../private_resources/conf_res"
        import_path = "private_resources.conf_res"
        # Grabbing a local DB url
        if path.exists(confidential_path + ".py"):
            conf_res = importlib.import_module(import_path)
            defaults["FALLBACK"]["DB_URL"] = conf_res.local_db_url
            print_verbose(sender=__name__,
                          message=f"Local Database url set to '{defaults['FALLBACK']['DB_URL']}",
                          underline=True)
        else:
            print_verbose(sender=__name__,
                          message=f"'{import_path}' module was not found. Loading aborted",
                          underline=True)
    except Exception as ecp:
        print_verbose(sender=__name__,
                      message=f"Failed to fetch private resources, {str(ecp)}",
                      underline=True)
        return
    print_verbose(sender=__name__,
                  message="Private resources loaded successfully",
                  underline=True)
