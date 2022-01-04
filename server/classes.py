from flask import request
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

from server_config import defaults

db = SQLAlchemy()
# Severities classes (FG Color, BG Color). The key is the severity
severities = defaults["SEVERITIES"]
known_list = {}                                # User list with proper name, expected URL and color
db_entries = []                                # DB Fetched past entries


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
def add_known_list(url, fore_color, backcolor, name):
    known_list[url] = (fore_color, backcolor, name)


# noinspection PyUnresolvedReferences
def fetch_db():
    # Fetching Severities classes, since they are atomic
    global severities
    db_sev = {}
    table_sev = "severities"
    table_usr = "users"
    try:
        stmt = text(f"SELECT * FROM {table_sev};")
        for sev in Severity.query.from_statement(stmt):
            db_sev[sev.name] = (sev.forecolor, sev.backcolor)
    except sqlalchemy.exc.ProgrammingError:
        db_sev.clear()
        internal_log(severity="attention", comment=f"The table {table_sev} does not exist")
    except Exception as exc:
        db_sev.clear()
        log_server.log_uncaught_exception(str(exc), request.json)
    finally:
        if len(db_sev) == 0:
            internal_log(severity="warning", comment=f"The table {table_sev} does not contains labels for severity."
                                                     f" Using default values")
        else:
            severities = db_sev
    # Fetching users and their colors
    global known_list
    try:
        stmt = text(f"SELECT * FROM {table_usr};")
        for usr in Users.query.from_statement(stmt):
            add_known_list(usr.url, usr.forecolor, usr.backcolor, usr.name)
    except sqlalchemy.exc.ProgrammingError:
        internal_log(severity="attention", comment=f"The table {table_usr} does not exist")
    except Exception as exc:
        db_sev.clear()
        log_server.log_uncaught_exception(str(exc), request.json)
    # Fetch past entries
