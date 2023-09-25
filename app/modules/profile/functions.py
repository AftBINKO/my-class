from app.data.functions import allowed_permission
from app.data.db_session import create_session
from app.data.models import Permission, User


def delete_user(user, current_user=None, check_permission=True):
    if not isinstance(user, (User, int)):  # noqa
        raise TypeError

    db_sess = create_session()
    if isinstance(user, int):
        user = db_sess.query(User).get(user)

    if not user:
        return 404

    if check_permission and current_user is not None:
        if max(list(map(int, user.statuses.split(", ")))) == 1:
            permission1 = db_sess.query(Permission).filter_by(title="editing_self_class").first()
            permission2 = db_sess.query(Permission).filter_by(title="editing_classes").first()
            permission3 = db_sess.query(Permission).filter_by(title="editing_school").first()

            if not ((allowed_permission(current_user, permission2) or (
                    allowed_permission(current_user, permission1) and current_user.class_id == user.class_id)) and (
                            current_user.school_id == user.school_id or allowed_permission(current_user, permission3))):
                db_sess.close()
                return 403
        elif max(list(map(int, user.statuses.split(", ")))) in [2, 3, 4]:
            permission1 = db_sess.query(Permission).filter_by(title="editing_self_school").first()
            permission2 = db_sess.query(Permission).filter_by(title="editing_school").first()

            if not (allowed_permission(current_user, permission2) or (
                    allowed_permission(current_user, permission1) and current_user.school_id == user.school_id)):
                db_sess.close()
                return 403

    db_sess.delete(user)
    db_sess.commit()
    db_sess.close()

    return True


def delete_login_data(user, current_user=None, check_permission=True):
    if not isinstance(user, (User, int)):  # noqa
        raise TypeError

    db_sess = create_session()
    if isinstance(user, int):
        user = db_sess.query(User).get(user)

    if not user:
        return 404

    if check_permission and current_user is not None:
        if max(list(map(int, user.statuses.split(", ")))) == 1:
            permission1 = db_sess.query(Permission).filter_by(title="editing_self_class").first()
            permission2 = db_sess.query(Permission).filter_by(title="editing_classes").first()
            permission3 = db_sess.query(Permission).filter_by(title="editing_school").first()

            if not ((allowed_permission(current_user, permission2) or (
                    allowed_permission(current_user, permission1) and current_user.class_id == user.class_id)) and (
                            current_user.school_id == user.school_id or allowed_permission(current_user, permission3))):
                db_sess.close()
                return 403
        elif max(list(map(int, user.statuses.split(", ")))) in [2, 3, 4]:
            permission1 = db_sess.query(Permission).filter_by(title="editing_self_school").first()
            permission2 = db_sess.query(Permission).filter_by(title="editing_school").first()

            if not (allowed_permission(current_user, permission2) or (
                    allowed_permission(current_user, permission1) and current_user.school_id == user.school_id)):
                db_sess.close()
                return 403

    user.login = None
    user.hashed_password = None
    user.generate_key()

    db_sess.commit()
    db_sess.close()

    return True
