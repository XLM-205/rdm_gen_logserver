import sqlalchemy
from flask import request
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

from entry_manager import add_known_list, add_severity, log_internal, log_uncaught_exception

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


# Methods --------------------------------------------------------------------------------------------------------------
# noinspection PyUnresolvedReferences
def fetch_db():
    """
    Fetches from the database all severities and users. If unable, will use default values defined on 'server_config'.
    Called only on 'server_boot', on startup
    """
    # Fetching Severities classes, since they are atomic
    db_sev = {}
    db_users = {}
    table_sev = "severities"
    table_usr = "users"
    try:
        stmt = text(f"SELECT * FROM {table_sev};")
        for sev in Severity.query.from_statement(stmt):
            db_sev[sev.name] = (sev.forecolor, sev.backcolor)
    except sqlalchemy.exc.ProgrammingError:
        db_sev.clear()
        log_internal(severity="Attention", comment=f"The table {table_sev} does not exist")
    except Exception as exc:
        db_sev.clear()
        log_uncaught_exception(str(exc), request.json)
    finally:
        if len(db_sev) == 0:
            log_internal(severity="Warning", comment=f"The table {table_sev} does not contains labels for severity."
                                                     f" Using default values")
        else:
            for key in list(db_sev.keys()):
                add_severity(key, db_sev[key][0], db_sev[key][1])
            log_internal(severity="Success", comment=f"Loaded {len(db_sev)} severity classes from the database")
    # Fetching users and their colors
    try:
        stmt = text(f"SELECT * FROM {table_usr};")
        for usr in Users.query.from_statement(stmt):
            db_users[usr.url] = (usr.forecolor, usr.backcolor, usr.name)
    except sqlalchemy.exc.ProgrammingError:
        log_internal(severity="Attention", comment=f"The table {table_usr} does not exist. Using default values")
    except Exception as exc:
        log_uncaught_exception(str(exc), request.json)
    finally:
        if len(db_users) == 0:
            log_internal(severity="Warning", comment=f"The table {table_usr} does not contains users."
                                                     f" Using default values")
        else:
            for key in list(db_users.keys()):
                add_known_list(key, db_users[key][0], db_users[key][1], db_users[key][2])
            log_internal(severity="Success", comment=f"Loaded {len(db_users)} users from the database")
    # Fetch past entries
