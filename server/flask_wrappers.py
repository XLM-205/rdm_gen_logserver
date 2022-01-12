import flask_login


def authenticated_user_is():
    """
    Returns the current authenticated user
    :return: An user object if the user not defined and if it's active / authenticated and None if isn't
    """
    if flask_login.current_user is None or flask_login.current_user.is_active is False:
        return None
    else:
        return flask_login.current_user
