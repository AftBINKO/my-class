from datetime import datetime
from json import load, dump

from .models import User, Status, Permission
from .db_session import create_session


def all_status_permissions(status):
    db_sess = create_session()
    all_perms = db_sess.query(Permission).all()

    if isinstance(status, (int, str)):
        status = db_sess.query(Status).filter(
            Status.id == status if isinstance(status, int) else Status.title == status).first()  # noqa
    status: Status
    db_sess.close()

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

    db_sess.close()

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

    if isinstance(user, int):  # noqa
        user = db_sess.query(User).get(user)
    user: User

    statuses = db_sess.query(Status).filter(Status.id.in_(user.statuses.split(", "))).all()  # noqa
    db_sess.close()

    permissions = set()

    for status in statuses:
        permissions = permissions | all_status_permissions(status)  # noqa

    return permissions


def allowed_permission(user, permission, allow_default=True):
    if not (isinstance(user, (User, int)) or isinstance(permission, (Permission, int, str))):  # noqa
        raise TypeError

    db_sess = create_session()  # noqa
    if isinstance(user, int):
        user = db_sess.query(User).get(user)
    user: User

    statuses = db_sess.query(Status).filter(Status.id.in_(user.statuses.split(", "))).all()  # noqa
    db_sess.close()

    for status in statuses:
        if allowed_status_permission(status, permission, allow_default=allow_default):
            return True

    if allow_default:
        return False
    return


def check_status(user, status):
    if not (isinstance(user, (User, int)) and isinstance(status, (Status, str, int))):  # noqa
        raise TypeError

    db_sess = create_session()

    if isinstance(user, int):
        user = db_sess.query(User).get(user)

    if isinstance(status, str):
        status = db_sess.query(Status).filter_by(title=status).first().id
    elif isinstance(status, Status):
        status = status.id

    db_sess.close()

    return status in set(map(int, user.statuses.split(", ")))


def add_status(user, status):
    if not (isinstance(user, (User, int)) and isinstance(status, (Status, str, int))):  # noqa
        raise TypeError

    db_sess = create_session()

    if isinstance(user, int):
        user = db_sess.query(User).get(user)

    if isinstance(status, int):
        status = db_sess.query(Status).get(status).title
    elif isinstance(status, Status):
        status = status.title

    user.statuses = ", ".join(list(map(str, (list(sorted(list(map(int, user.statuses.split(", "))) + [
        db_sess.query(Status).filter_by(title=status).first().id]))))))

    db_sess.commit()
    db_sess.close()


def del_status(user, status):
    if not (isinstance(user, (User, int)) and isinstance(status, (Status, str, int))):  # noqa
        raise TypeError

    db_sess = create_session()

    if isinstance(user, int):
        user = db_sess.query(User).get(user)

    if isinstance(status, str):
        status = db_sess.query(Status).filter_by(title=status).first().id
    elif isinstance(status, Status):
        status = status.id

    statuses = list(sorted(list(map(int, user.statuses.split(", ")))))
    if status in statuses:
        statuses.remove(status)
    else:
        return 404
    user.statuses = ", ".join(list(map(str, statuses)))

    db_sess.commit()
    db_sess.close()


def clear_times(config_path, echo=False, all_times=False):
    db_sess = create_session()
    users = db_sess.query(User).all()
    for user in users:
        if check_status(user, "Ученик"):
            user.is_arrived = False
            user.arrival_time = None
            if all_times:
                user.list_times = None
    db_sess.commit()
    db_sess.close()

    with open(config_path, 'r') as config:
        cfg = load(config)
    cfg["update_times"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    if all_times:
        cfg["clear_times"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    with open(config_path, 'w') as config:
        dump(cfg, config)

    if echo:
        print("Время явки учеников обнулено")
        if all_times:
            print("Списки явки учеников очищены")


def check_and_clear_times(config_path, echo=False):
    with open(config_path) as config:
        cfg = load(config)

    all_clear = False
    if "clear_times" in cfg.keys():
        if cfg["clear_times"] is not None:
            if (datetime.now() - datetime.strptime(cfg["clear_times"], "%Y-%m-%d %H:%M:%S.%f")).days >= 365:
                all_clear = True
        else:
            all_clear = True
    else:
        all_clear = True

    if all_clear:
        clear_times(config_path, echo=echo, all_times=True)
    else:
        clear = False
        if "update_times" in cfg.keys():
            if cfg["update_times"] is not None:
                if (datetime.now() - datetime.strptime(cfg["update_times"], "%Y-%m-%d %H:%M:%S.%f")).days >= 1:
                    clear = True
            else:
                clear = True
        else:
            clear = True

        if clear:
            clear_times(config_path, echo=echo)
