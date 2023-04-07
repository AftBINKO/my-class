from .db_session import create_session
from .models import User, Status, Permission

from json import loads


def all_status_permissions(status):
    db_sess = create_session()
    all_perms = db_sess.query(Permission).all()

    if isinstance(status, (int, str)):
        status = db_sess.query(Status).filter(
            Status.id == status if isinstance(status, int) else Status.title == status).first()  # noqa

    status_perms = loads(status.permissions)

    permissions = set()

    inherited_status = status_perms["inheritance"]
    inherited_permissions = set()
    if isinstance(inherited_status, (int, str)):
        inherited_permissions = set(
            map(lambda p: db_sess.query(Permission).filter(Permission.title == p).first().id, all_status_permissions(
                inherited_status)))  # noqa

    allowed_perms = inherited_permissions | set(status_perms["allowed"])
    banned_perms = set(status_perms["banned"])

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


def all_permissions(user: User):
    db_sess = create_session()
    status = db_sess.query(Status).filter(Status.id == user.status).first()  # noqa

    return all_status_permissions(status)


def allowed_permission(user: User, permission, method=2):
    if not isinstance(permission, (Permission, int, str)):
        raise TypeError

    user_perms = all_permissions(user)

    if isinstance(permission, str):
        return permission in user_perms

    if isinstance(permission, int):
        db_sess = create_session()
        permission = db_sess.query(Permission).filter(
            Permission.id == permission).first()  # noqa

    return permission.title in user_perms
