from .db_session import create_session
from .models import User, Status, Permission


def all_status_permissions(status):
    db_sess = create_session()
    all_perms = db_sess.query(Permission).all()

    if isinstance(status, (int, str)):
        status = db_sess.query(Status).filter(
            Status.id == status if isinstance(status, int) else Status.title == status).first()  # noqa
    status: Status
    db_sess.commit()

    permissions = {perm for perm in all_perms if allowed_status_permission(status, perm)}

    return permissions


def allowed_status_permission(status, permission, allow_default=True):
    if not (isinstance(status, (Status, (int, str))) or isinstance(permission, (Permission, int, str))):
        raise TypeError

    db_sess = create_session()
    if isinstance(status, (int, str)):
        status = db_sess.query(Status).filter(
            Status.id == status if isinstance(status, int) else Status.title == status).first()  # noqa
    status: Status

    if isinstance(permission, (int, str)):
        permission = db_sess.query(Permission).filter(
            Permission.id == permission if isinstance(permission, int) else Permission.title == permission  # noqa
        ).first()
    permission: Permission

    inherited_status = status.inheritance
    allowed_for_inherited_status = None
    if inherited_status is not None:
        allowed_for_inherited_status = allowed_status_permission(inherited_status, permission, allow_default=False)

    allowed_id_perms = {}
    if status.allowed_permissions:
        allowed_id_perms = set(status.allowed_permissions.split(", "))

    banned_id_perms = {}
    if status.banned_permissions:
        banned_id_perms = set(status.banned_permissions.split(", "))

    all_id_perms = set(map(lambda p: p.id, db_sess.query(Permission).all()))

    db_sess.commit()

    if "*" in allowed_id_perms:
        allowed_id_perms = all_id_perms
    if "*" in banned_id_perms:
        banned_id_perms = all_id_perms

    allowed_id_perms = set(map(int, allowed_id_perms))
    banned_id_perms = set(map(int, banned_id_perms))

    if permission.id in banned_id_perms:
        return False
    elif permission.id in allowed_id_perms:
        return True
    elif allowed_for_inherited_status is not None:
        return allowed_for_inherited_status
    elif allow_default:
        return permission.is_allowed_default
    return


def all_permissions(user):
    if not isinstance(user, (User, int)):
        raise TypeError

    db_sess = create_session()  # noqa
    if isinstance(user, int):
        user = db_sess.query(User).filter(User.id == user).first()  # noqa
    user: User

    statuses = db_sess.query(Status).filter(Status.id.in_(user.statuses.split(", "))).all()  # noqa
    db_sess.commit()

    permissions = set()

    for status in statuses:
        permissions = permissions | all_status_permissions(status)  # noqa

    return permissions


def allowed_permission(user, permission, allow_default=True):
    if not (isinstance(user, (User, int)) or isinstance(permission, (Permission, int, str))):
        raise TypeError

    db_sess = create_session()  # noqa
    if isinstance(user, int):
        user = db_sess.query(User).filter(User.id == user).first()  # noqa
    user: User

    statuses = db_sess.query(Status).filter(Status.id.in_(user.statuses.split(", "))).all()  # noqa
    db_sess.commit()

    for status in statuses:
        if allowed_status_permission(status, permission, allow_default=allow_default):
            return True

    if allow_default:
        return False
    return
