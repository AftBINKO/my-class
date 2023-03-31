from .db_session import create_session
from .models import User, Status, Permission

from json import loads


def all_permissions(user: User):
    db_sess = create_session()
    status = db_sess.query(Status).filter(Status.id == user.status).first()  # noqa

    all_perms = db_sess.query(Permission).all()

    user_perms = loads(status.permissions)
    allowed_perms = user_perms["allowed"]
    banned_perms = user_perms["banned"]
    permissions = []

    if allowed_perms == ["*"]:
        if banned_perms:
            if banned_perms != ["*"]:
                permissions = [perm.title for perm in all_perms if perm.id not in banned_perms]
        else:
            permissions = list(map(lambda p: p.title, all_perms))
    else:
        if banned_perms:
            if banned_perms != ["*"]:
                permissions = [perm.title for perm in all_perms if
                               perm.id in allowed_perms and perm.id not in banned_perms]
        else:
            permissions = [perm.title for perm in all_perms if perm.id in allowed_perms]

    return permissions


def allowed_permission(user: User, permission, method=1):
    if not isinstance(permission, (Permission, int, str)):
        raise TypeError

    match method:
        case 1:
            db_sess = create_session()
            status = db_sess.query(Status).filter(Status.id == user.status).first()  # noqa
            user_perms = loads(status.permissions)
            allowed_perms = user_perms["allowed"]
            banned_perms = user_perms["banned"]

            if isinstance(permission, str):
                permission = db_sess.query(Permission).filter(
                    Permission.title == permission).first()  # noqa

            if isinstance(permission, Permission):
                permission = permission.id

            if allowed_perms == ["*"]:
                if banned_perms:
                    if banned_perms != ["*"]:
                        return permission not in banned_perms
                    return False
                return True
            if banned_perms:
                if banned_perms != ["*"]:
                    return permission in allowed_perms and permission not in banned_perms
                return False
            return permission in allowed_perms

        case 2:
            user_perms = all_permissions(user)

            if isinstance(permission, str):
                return permission in user_perms

            if isinstance(permission, int):
                db_sess = create_session()
                permission = db_sess.query(Permission).filter(
                    Permission.id == permission).first()  # noqa

            return permission.title in user_perms
