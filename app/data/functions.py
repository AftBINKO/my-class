from json import load, loads, dump, dumps
from datetime import datetime
from os import path

from qrcode.image.styledpil import StyledPilImage
from qrcode.constants import ERROR_CORRECT_H
from qrcode.main import QRCode

from flask import url_for
from pytz import timezone

from .models import User, Role, Permission, Group
from .db_session import create_session


def all_role_permissions(role):
    db_sess = create_session()
    all_perms = db_sess.query(Permission).all()

    if isinstance(role, (int, str)):
        role = db_sess.query(Role).filter(
            Role.id == role if isinstance(role, int) else Role.title == role).first()  # noqa
    role: Role
    db_sess.close()

    permissions = {perm for perm in all_perms if check_role_permission(role, perm)}

    return permissions


def check_role_permission(role, permission, allow_default=True):
    if not (isinstance(role, (Role, (int, str))) or isinstance(permission, (Permission, int, str))):
        raise TypeError

    db_sess = create_session()
    if isinstance(role, (int, str)):
        role = db_sess.query(Role).filter(
            Role.id == role if isinstance(role, int) else Role.title == role).first()  # noqa
    role: Role

    if isinstance(permission, (int, str)):
        permission = db_sess.query(Permission).filter(
            Permission.id == permission if isinstance(permission, int) else Permission.title == permission  # noqa
        ).first()
    permission: Permission

    inherited_role = role.inheritance
    allowed_for_inherited_role = None
    if inherited_role is not None:
        allowed_for_inherited_role = check_role_permission(inherited_role, permission, allow_default=False)

    allowed_id_perms = {}
    if role.allowed_permissions:
        allowed_id_perms = set(role.allowed_permissions.split(", "))

    banned_id_perms = {}
    if role.banned_permissions:
        banned_id_perms = set(role.banned_permissions.split(", "))

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
    elif allowed_for_inherited_role is not None:
        return allowed_for_inherited_role
    elif allow_default:
        return permission.is_allowed_default
    return


def get_roles(user):
    if not isinstance(user, (User, int)):  # noqa
        raise TypeError

    db_sess = create_session()

    if isinstance(user, int):
        user = db_sess.query(User).get(user)

    roles = db_sess.query(Role).filter(Role.id.in_(loads(user.roles))).all()  # noqa
    roles: list

    db_sess.close()

    return roles


def all_permissions(user):
    if not isinstance(user, (User, int)):
        raise TypeError

    db_sess = create_session()  # noqa

    if isinstance(user, int):  # noqa
        user = db_sess.query(User).get(user)
    user: User

    roles = get_roles(user)

    permissions = set()

    for role in roles:
        permissions = permissions | all_role_permissions(role)  # noqa

    return permissions


def check_permission(user, permission, allow_default=True):
    if not (isinstance(user, (User, int)) or isinstance(permission, (Permission, int, str))):  # noqa
        raise TypeError

    db_sess = create_session()  # noqa
    if isinstance(user, int):
        user = db_sess.query(User).get(user)
    user: User

    roles = get_roles(user)
    db_sess.close()

    for role in roles:
        if check_role_permission(role, permission, allow_default=allow_default):
            return True

    if allow_default:
        return False


def get_titles_roles(user):
    if not isinstance(user, (User, int)):  # noqa
        raise TypeError

    db_sess = create_session()

    if isinstance(user, int):
        user = db_sess.query(User).get(user)

    roles = list(sorted(get_roles(user), key=lambda r: r.priority, reverse=True))

    roles_titles = []
    for role in roles:
        if role.title in ["Лидер", "Ученик", "Староста"]:
            if user.group_id:
                group = db_sess.query(Group).get(user.group_id)
                title = f"{role.title} группы {group.name}"
                roles_titles.append(title)
                continue

        roles_titles.append(role.title)
    db_sess.close()
    return roles_titles


def get_max_role(user):
    return sorted(get_roles(user), key=lambda role: role.priority)[-1]


def get_min_role(user):
    return sorted(get_roles(user), key=lambda role: role.priority)[0]


def check_role(user, role):
    if not (isinstance(user, (User, int)) and isinstance(role, (Role, str, int))):  # noqa
        raise TypeError

    db_sess = create_session()

    if isinstance(user, int):
        user = db_sess.query(User).get(user)

    if isinstance(role, str):
        role = db_sess.query(Role).filter_by(title=role).first().id
    elif isinstance(role, Role):
        role = role.id

    db_sess.close()

    return role in loads(user.roles)


def add_role(user, role):
    if not (isinstance(user, (User, int)) and isinstance(role, (Role, str, int))):  # noqa
        raise TypeError

    db_sess = create_session()

    if isinstance(user, int):
        user = db_sess.query(User).get(user)

    if isinstance(role, int):
        role = db_sess.query(Role).get(role).title
    elif isinstance(role, Role):
        role = role.title

    roles: list = loads(user.roles)
    roles.append(db_sess.query(Role).filter_by(title=role).first().id)
    user.roles = dumps(list(sorted(roles)))

    db_sess.commit()
    db_sess.close()


def del_role(user, role):
    if not (isinstance(user, (User, int)) and isinstance(role, (Role, str, int))):  # noqa
        raise TypeError

    db_sess = create_session()

    if isinstance(user, int):
        user = db_sess.query(User).get(user)

    if isinstance(role, str):
        role = db_sess.query(Role).filter_by(title=role).first().id
    elif isinstance(role, Role):
        role = role.id

    roles = list(sorted(loads(user.roles)))
    if role in roles:
        roles.remove(role)
    else:
        return 404
    user.roles = dumps(roles)

    db_sess.commit()
    db_sess.close()


def admit(user, current_user):
    if not (isinstance(user, (User, int)) and isinstance(current_user, (User, int))):  # noqa
        raise TypeError

    db_sess = create_session()

    if isinstance(user, int):
        user = db_sess.query(User).get(user)

    if isinstance(current_user, int):
        current_user = db_sess.query(User).get(current_user)

    permission1 = db_sess.query(Permission).filter_by(title="admit_school").first()
    permission2 = db_sess.query(Permission).filter_by(title="admit").first()

    if not ((check_permission(current_user, permission2) or (check_permission(
            current_user, permission1
    ) and user.school_id is not None and current_user.school_id == user.school_id)) and get_max_role(
        current_user
    ).priority > get_min_role(user).priority):
        db_sess.close()
        return 403

    if user.is_arrived:
        return

    user.is_arrived = True
    arrival_time = datetime.now().astimezone(timezone("Europe/Moscow"))

    user.arrival_time = arrival_time

    list_times = []
    if user.list_times:
        list_times = user.list_times.split(', ')
    list_times.append(arrival_time.strftime("%Y-%m-%d %H:%M:%S.%f"))

    user.list_times = ", ".join(list_times)

    db_sess.commit()
    db_sess.close()

    return True


def generate_qrs(users, current_user, qrcodes_path, ignore_exists=True):
    if not (isinstance(users, (User, int, list)) and isinstance(current_user, (User, int))):  # noqa
        raise TypeError

    db_sess = create_session()

    if isinstance(current_user, int):
        current_user = db_sess.query(User).get(current_user)

    us = []
    if isinstance(users, int):
        users = db_sess.query(User).get(users)
    if isinstance(users, User):
        users = [users]

    for user in users:
        if not (isinstance(user, (User, int))):
            raise TypeError

        if isinstance(user, int):
            user = db_sess.query(User).get(user)
        us.append(user)

    for user in us:
        user: User

        if user.qr and ignore_exists:
            continue

        permission1 = db_sess.query(Permission).filter_by(title="generate_qr_school").first()
        permission2 = db_sess.query(Permission).filter_by(title="generate_self_qr").first()
        permission3 = db_sess.query(Permission).filter_by(title="generate_qr_group").first()
        permission4 = db_sess.query(Permission).filter_by(title="generate_qr").first()

        if user.id == current_user.id:
            if not check_permission(current_user, permission2):
                db_sess.close()
                return 403
        else:

            if check_permission(current_user, permission4) or (check_permission(
                    current_user, permission1
            ) and current_user.school_id is not None and current_user.school_id == user.school_id) or \
                    (check_permission(
                        current_user, permission3
                    ) and current_user.group_id is not None and current_user.group_id == user.group_id):

                if get_max_role(user).priority >= get_max_role(current_user).priority:
                    db_sess.close()
                    return 403
            else:
                db_sess.close()
                return 403

        name = f"pass_{user.id}.png"
        qr = QRCode(
            version=2,
            error_correction=ERROR_CORRECT_H
        )
        qr.add_data(url_for("qr.admit", user_id=user.id, _external=True))
        img = qr.make_image(image_factory=StyledPilImage,
                            embeded_image_path=f'app/{url_for("static", filename="logos/logo.jpg")}')
        img.save(path.join(qrcodes_path, name))

        u = db_sess.query(User).get(user.id)
        u.qr = name

    db_sess.commit()
    db_sess.close()


def clear_times(config_path, echo=False, all_times=False):
    db_sess = create_session()
    users = db_sess.query(User).all()
    for user in users:
        if check_role(user, "Ученик"):
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
