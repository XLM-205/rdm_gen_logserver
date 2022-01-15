import sqlalchemy
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from typing import Tuple

from entry_manager import add_server, add_severity, log_internal, log_uncaught_exception, log_internal_echo, \
                          lists_count, servers_list, severities
from server_config import defaults, logger_config, print_verbose

db = SQLAlchemy()


# Models ---------------------------------------------------------------------------------------------------------------
class Severity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    forecolor = db.Column(db.String(7))  # Expected to be '#RRGGBB'
    backcolor = db.Column(db.String(7))


class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_user = db.Column(db.Integer)
    severity = db.Column(db.String)
    comm = db.Column(db.String)
    details = db.Column(db.String)


class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True)
    url = db.Column(db.String)
    forecolor = db.Column(db.String(7))    # Expected to be '#RRGGBB'
    backcolor = db.Column(db.String(7))
    webpass = db.Column(db.String(100))

    @classmethod
    def authenticate(cls, identifier, webpass):
        """
        Returns a full user object if the (identifier matches the name OR uid) AND 'webpass' matches
        :param identifier: Either the name or UID of the user
        :param webpass: The password of the web service
        """
        stmt = text(f"SELECT * FROM authenticate('{identifier}', '{webpass}');")
        return cls.query.from_statement(stmt).first()

    def as_tuple(self) -> Tuple[int, str, str, str, str]:
        """
        Return itself as a tuple, following the order of declared fields (webpass is ignored for security reasons)
        :return: (id, name, url, forecolor, backcolor)
        """
        return self.id, self.name, self.url, self.forecolor, self.backcolor


# Methods --------------------------------------------------------------------------------------------------------------
# noinspection PyUnresolvedReferences
def fetch_db(db_uri):
    """
    Fetches from the database all severities and users. If unable, will use default values defined on 'server_config'.
    Called only on 'server_boot', on startup
    """
    db.create_engine(db_uri, {})
    # Fetching Severities classes, since they are atomic
    db_sev = {}
    db_users = {}
    table_sev = "severities"
    table_usr = "users"
    # table_entry = "entries"
    try:
        stmt = text(f"SELECT * FROM {table_sev};")
        for sev in Severity.query.from_statement(stmt):
            if sev.name is not None:
                db_sev[sev.name] = (sev.forecolor, sev.backcolor)
            else:
                log_internal_echo(severity="Error", sender=__name__,
                                  comment=f"Severity id {sev.id} didn't have a valid name and was ignored")
    except sqlalchemy.exc.ProgrammingError:
        log_internal_echo(severity="Attention", sender=__name__,
                          comment=f"The table {table_sev} does not exist or is invalid."
                                  f"Server doesn't have database support. Severities and users using default values")
        logger_config["USE_DB"] = False
        db.engine.dispose()
        return
    except Exception as exc:
        db_sev.clear()
        log_uncaught_exception(str(exc), None, __name__)
    if len(db_sev) == 0 or db_sev == defaults["SEVERITIES"]:
        print_verbose(sender=__name__,
                      message=f"The table {table_sev} did not had valid or new severities labels."
                              f" Keeping default values")
    else:
        for key in list(db_sev.keys()):
            add_severity(key, db_sev[key][0], db_sev[key][1], allow_replace=True, log_suppress=True)
    # Fetching users and their colors
    try:
        stmt = text(f"SELECT * FROM {table_usr};")
        for usr in Users.query.from_statement(stmt):
            if usr.url is not None:
                db_users[usr.url] = (usr.forecolor, usr.backcolor, usr.name if usr.name is not None else usr.url)
            else:
                log_internal_echo(severity="Error", sender=__name__,
                                  comment=f"User id {usr.id} didn't have a valid url and was ignored")
    except sqlalchemy.exc.ProgrammingError:
        log_internal_echo(severity="Attention", sender=__name__,
                          comment=f"The table {table_usr} does not exist or is invalid. "
                                  f"Server doesn't have database support. Severities and users using default values")
        logger_config["USE_DB"] = False
    except Exception as exc:
        log_uncaught_exception(str(exc), None, __name__)
    if len(db_users) == 0 or db_users == defaults["SERVERS"]:
        print_verbose(sender=__name__,
                      message=f"The table {table_usr} did not had valid or new users. Keeping default values")
    else:
        for key in list(db_users.keys()):
            add_server(key, db_users[key][0], db_users[key][1], db_users[key][2],
                       allow_replace=True, log_suppress=True)
    sev, serv, entry = lists_count()
    log_internal(severity="Success", comment=f"Loaded {serv} servers and {sev} severities from the database",
                 body={"servers": servers_list, "severities": severities})
    # Fetch past entries
    db.engine.dispose()
