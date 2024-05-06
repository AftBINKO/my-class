from os import path

from app.data.functions import check_permission as cp, get_max_role
from app.data.db_session import create_session
from app.data.models import Permission, User


def allowed_image(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg'}


def add_image(user, current_user, image, image_path, check_permission=True):
    if not allowed_image(image.filename):
        return 415

    if not (isinstance(user, (User, int)) and isinstance(current_user, (User, int))):  # noqa
        raise TypeError

    db_sess = create_session()

    if isinstance(current_user, int):
        current_user = db_sess.query(User).get(current_user)

    if isinstance(user, int):
        user = db_sess.query(User).get(user)

    current_user: User  # noqa
    user: User

    if check_permission:
        permission1 = db_sess.query(Permission).filter_by(title="upload_image_school").first()
        permission2 = db_sess.query(Permission).filter_by(title="upload_self_image").first()
        permission3 = db_sess.query(Permission).filter_by(title="upload_image_group").first()
        permission4 = db_sess.query(Permission).filter_by(title="upload_image").first()

        if user.id == current_user.id:
            if not cp(current_user, permission2):
                db_sess.close()
                return 403
        else:

            if cp(current_user, permission4) or (cp(
                    current_user, permission1
            ) and current_user.school_id is not None and current_user.school_id == user.school_id) or \
                    (cp(
                        current_user, permission3
                    ) and current_user.group_id is not None and current_user.group_id == user.group_id):

                if get_max_role(user).priority >= get_max_role(current_user).priority:
                    db_sess.close()
                    return 403
            else:
                db_sess.close()
                return 403

    filename = f"image_{user.id}.{image.filename.split('.')[-1]}"
    image.save(path.join(image_path, filename))

    u = db_sess.query(User).get(user.id)
    u.image = filename

    db_sess.commit()
    db_sess.close()


def delete_image(user, current_user, check_permission=True):
    if not (isinstance(user, (User, int)) and isinstance(current_user, (User, int))):  # noqa
        raise TypeError

    db_sess = create_session()

    if isinstance(current_user, int):
        current_user = db_sess.query(User).get(current_user)

    if isinstance(user, int):
        user = db_sess.query(User).get(user)

    if (not user) or (not current_user):
        return 404

    current_user: User  # noqa
    user: User

    if check_permission:
        permission1 = db_sess.query(Permission).filter_by(title="upload_image_school").first()
        permission2 = db_sess.query(Permission).filter_by(title="upload_self_image").first()
        permission3 = db_sess.query(Permission).filter_by(title="upload_image_group").first()
        permission4 = db_sess.query(Permission).filter_by(title="upload_image").first()

        if user.id == current_user.id:
            if not cp(current_user, permission2):
                db_sess.close()
                return 403
        else:

            if cp(current_user, permission4) or (cp(
                    current_user, permission1
            ) and current_user.school_id is not None and current_user.school_id == user.school_id) or \
                    (cp(
                        current_user, permission3
                    ) and current_user.group_id is not None and current_user.group_id == user.group_id):

                if get_max_role(user).priority >= get_max_role(current_user).priority:
                    db_sess.close()
                    return 403
            else:
                db_sess.close()
                return 403

    u = db_sess.query(User).get(user.id)
    u.image = None

    db_sess.commit()
    db_sess.close()


def delete_user(user, current_user=None, check_permission=True):  # TODO: перепроверить, исправить
    if not isinstance(user, (User, int)):
        raise TypeError

    db_sess = create_session()
    if isinstance(user, int):
        user = db_sess.query(User).get(user)

    if not user:
        return 404
    if user.id == current_user.id:
        return 403

    if check_permission and current_user is not None:  # noqa
        max_role_id = get_max_role(user).id
        if max_role_id == 1:
            permission1 = db_sess.query(Permission).filter_by(title="editing_self_group").first()
            permission2 = db_sess.query(Permission).filter_by(title="editing_groups").first()
            permission3 = db_sess.query(Permission).filter_by(title="editing_school").first()

            if not ((cp(current_user, permission2) or (
                    cp(current_user, permission1) and current_user.group_id == user.group_id)) and (
                            current_user.school_id == user.school_id or cp(current_user, permission3))):
                db_sess.close()
                return 403
        elif max_role_id in [2, 3, 4]:
            permission1 = db_sess.query(Permission).filter_by(title="editing_self_school").first()
            permission2 = db_sess.query(Permission).filter_by(title="editing_school").first()

            if not (cp(current_user, permission2) or (
                    cp(current_user, permission1) and current_user.school_id == user.school_id)):
                db_sess.close()
                return 403

    db_sess.delete(user)
    db_sess.commit()
    db_sess.close()

    return True


def delete_login_data(user, current_user=None, check_permission=True):
    if not isinstance(user, (User, int)):
        raise TypeError

    db_sess = create_session()
    if isinstance(user, int):
        user = db_sess.query(User).get(user)

    if not user:
        return 404

    if check_permission and current_user is not None:  # noqa
        max_role_id = get_max_role(user).id
        if max_role_id == 1:
            permission1 = db_sess.query(Permission).filter_by(title="editing_self_group").first()
            permission2 = db_sess.query(Permission).filter_by(title="editing_groups").first()
            permission3 = db_sess.query(Permission).filter_by(title="editing_school").first()

            if not ((cp(current_user, permission2) or (
                    cp(current_user, permission1) and current_user.group_id == user.group_id)) and (
                            current_user.school_id == user.school_id or cp(current_user, permission3))):
                db_sess.close()
                return 403
        elif max_role_id in [2, 3, 4]:
            permission1 = db_sess.query(Permission).filter_by(title="editing_self_school").first()
            permission2 = db_sess.query(Permission).filter_by(title="editing_school").first()

            if not (cp(current_user, permission2) or (
                    cp(current_user, permission1) and current_user.school_id == user.school_id)):
                db_sess.close()
                return 403

    user.login = None
    user.hashed_password = None
    user.is_registered = False
    user.generate_key()

    db_sess.commit()
    db_sess.close()

    return True
