from .db_session import create_session
from .models import User, Status, Permission

from json import loads


def all_status_permissions(status):  # TODO: запихать все функции в модели
    db_sess = create_session()
    all_perms = db_sess.query(Permission).all()

    if isinstance(status, (int, str)):
        status = db_sess.query(Status).filter(
            Status.id == status if isinstance(status, int) else Status.title == status).first()  # noqa
    status: Status

    permissions = set()

    inherited_status = status.inheritance
    inherited_permissions = set()
    if inherited_status is not None:
        inherited_permissions = set(
            map(lambda p: db_sess.query(Permission).filter(Permission.title == p).first().id, all_status_permissions(
                inherited_status)))  # noqa

    allowed_perms = inherited_permissions
    if status.allowed_permissions:
        allowed_perms = allowed_perms | set(status.allowed_permissions.split(", "))

    banned_perms = None
    if status.banned_permissions:
        banned_perms = set(status.banned_permissions.split(", "))

    if "*" in allowed_perms:
        if banned_perms:
            if "*" not in banned_perms:
                permissions = {perm.title for perm in all_perms if perm.id not in banned_perms}
        else:
            permissions = set(map(lambda p: p.title, all_perms))
    else:
        if banned_perms:
            if "*" not in permissions:
                permissions = {perm.title for perm in all_perms if
                               perm.id in allowed_perms and perm.id not in banned_perms}
        else:
            permissions = {perm.title for perm in all_perms if perm.id in allowed_perms}

    return permissions


def all_permissions(user):
    if not isinstance(user, (User, int)):
        raise TypeError

    db_sess = create_session()
    if isinstance(user, int):
        user = db_sess.query(User).filter(User.id == user).first()  # noqa

    statuses = db_sess.query(Status).filter(Status.id.in_(loads(user.statuses))).all()  # noqa
    permissions = set()

    for status in statuses:
        permissions = permissions | all_status_permissions(status)  # noqa

    return permissions


def allowed_permission(user, permission, method=2):
    if not (isinstance(user, (User, int)) or isinstance(permission, (Permission, int, str))):
        raise TypeError

    db_sess = create_session()
    if isinstance(user, int):
        user = db_sess.query(User).filter(User.id == user).first()  # noqa

    user_perms = all_permissions(user)

    if isinstance(permission, str):
        return permission in user_perms

    if isinstance(permission, int):
        permission = db_sess.query(Permission).filter(Permission.id == permission).first()  # noqa

    return permission.title in user_perms
