from .db_session import create_session
from .models import User, Status, Permission, Class, School


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
    if isinstance(user, int):
        user = db_sess.query(User).filter(User.id == user).first()  # noqa
    user: User

    statuses = db_sess.query(Status).filter(Status.id.in_(user.statuses.split(", "))).all()  # noqa
    db_sess.close()

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
    db_sess.close()

    for status in statuses:
        if allowed_status_permission(status, permission, allow_default=allow_default):
            return True

    if allow_default:
        return False
    return


def delete_schools(schools, user=None, check_permission=True):
    if not isinstance(schools, (School, int, list)):
        raise TypeError

    db_sess = create_session()

    if isinstance(schools, (School, int)):  # noqa
        if isinstance(schools, School):
            schools = schools.id

        schools = [schools]

    elif isinstance(schools, list):
        ss = []
        for c in schools:
            if isinstance(c, int):
                ss.append(c)
            elif isinstance(c, Class):
                ss.append(c.id)

        schools = ss

    if check_permission and user is not None:
        permission1 = db_sess.query(Permission).filter(Permission.title == "deleting_self_school").first()  # noqa
        permission2 = db_sess.query(Permission).filter(Permission.title == "deleting_school").first()  # noqa
        if not (allowed_permission(user, permission2) or (
                allowed_permission(user, permission1) and user.school_id in schools)):
            db_sess.close()
            return 405

    schools = db_sess.query(School).filter(School.id.in_(schools)).all()  # noqa
    for school in schools:
        classes = db_sess.query(Class).filter(Class.school_id == school.id).all()  # noqa
        delete_classes(school, classes, check_permission=False)
        db_sess.delete(school)

    db_sess.commit()
    db_sess.close()

    return True


def delete_classes(school, classes, user=None, check_permission=True):
    if not (isinstance(school, (School, int)) and isinstance(classes, (Class, int, list))):
        raise TypeError

    db_sess = create_session()
    if isinstance(school, School):
        school = school.id

    if isinstance(classes, (Class, int)):  # noqa
        if isinstance(classes, Class):
            classes = classes.id

        classes = [classes]
    elif isinstance(classes, list):
        cs = []
        for c in classes:
            if isinstance(c, int):
                cs.append(c)
            elif isinstance(c, Class):
                cs.append(c.id)

        classes = cs

    if check_permission and user is not None:
        permission1 = db_sess.query(Permission).filter(Permission.title == "deleting_self_class").first()  # noqa
        permission2 = db_sess.query(Permission).filter(Permission.title == "deleting_classes").first()  # noqa
        permission3 = db_sess.query(Permission).filter(Permission.title == "editing_school").first()  # noqa

        if not ((allowed_permission(user, permission2) or (
                allowed_permission(user, permission1) and user.class_id in classes)) and (
                        user.school_id == school or allowed_permission(user, permission3))):
            db_sess.close()
            return 405

    students = db_sess.query(User).filter(User.class_id.in_(classes)).all()  # noqa
    for student in students:
        student.class_id = None
        student.school_id = None
    db_sess.query(Class).filter(Class.id.in_(classes)).delete()  # noqa
    db_sess.commit()
    db_sess.close()

    return True


def delete_user(user, current_user=None, check_permission=True):
    if not isinstance(user, (User, int)):
        raise TypeError

    db_sess = create_session()
    if isinstance(user, int):
        user = db_sess.query(User).filter(User.id == user).first()  # noqa

    if check_permission and current_user is not None:
        permission1 = db_sess.query(Permission).filter(Permission.title == "editing_self_class").first()  # noqa
        permission2 = db_sess.query(Permission).filter(Permission.title == "editing_classes").first()  # noqa
        permission3 = db_sess.query(Permission).filter(Permission.title == "editing_school").first()  # noqa

        if not ((allowed_permission(current_user, permission2) or (
                allowed_permission(current_user, permission1) and current_user.class_id == user.class_id)) and (
                        current_user.school_id == user.school_id or allowed_permission(current_user, permission3))):
            db_sess.close()
            return 405

    db_sess.delete(user)
    db_sess.commit()
    db_sess.close()

    return True
