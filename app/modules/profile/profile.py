from string import ascii_letters, digits, punctuation

from flask import redirect, url_for, abort, render_template
from flask_login import login_required, current_user

from app.data.models import User, Class, Permission, Status, School
from app.data.functions import all_permissions, allowed_permission
from app.data.db_session import create_session
from app.data.forms import ChangeFullnameForm
from app import RUSSIAN_ALPHABET

from app.modules.profile.forms import ChangeLoginForm, ChangePasswordForm
from app.modules.profile.functions import delete_user as del_user
from app.modules.profile.functions import delete_login_data
from app.modules.profile import bp


@bp.route('/')
@bp.route('/my')
@login_required
def profile():
    if not current_user.is_registered:
        return redirect(url_for("auth.finish_register"))
    return redirect(url_for(".profile_user", user_id=current_user.id))


@bp.route('/<user_id>')
@login_required
def profile_user(user_id):
    if not current_user.is_registered:
        return redirect(url_for("auth.finish_register"))
    db_sess = create_session()
    user = db_sess.query(User).filter(User.id == user_id).first()
    school_class = db_sess.query(Class).filter(Class.id == user.class_id).first()  # noqa
    school = db_sess.query(School).filter(School.id == user.school_id).first()  # noqa
    statuses = list(sorted(db_sess.query(Status).filter(Status.id.in_(user.statuses.split(", "))).all(),  # noqa
                           key=lambda s: s.id, reverse=True))
    statuses_titles = []
    for status in statuses:
        if status.title in ["Классный руководитель", "Ученик"]:
            if school_class:
                title = f"{status.title} {school_class.class_number}-го"
                if school_class.letter:
                    title += f' "{school_class.letter}" '
                title += " класса"
                statuses_titles.append(title)
                continue

        statuses_titles.append(status.title)
    permissions = None
    permission3 = db_sess.query(Permission).filter(Permission.title == "access_admin_panel").first()  # noqa
    if current_user.id == int(user_id):
        permissions = set(map(lambda permission: permission.title, all_permissions(user)))
    else:
        if max(list(map(int, user.statuses.split(", ")))) == 1:
            permission1 = db_sess.query(Permission).filter(Permission.title == "editing_self_class").first()  # noqa
            permission2 = db_sess.query(Permission).filter(Permission.title == "editing_classes").first()  # noqa
            permission3 = db_sess.query(Permission).filter(Permission.title == "editing_school").first()  # noqa

            if not ((allowed_permission(current_user, permission2) or (
                    allowed_permission(current_user, permission1) and current_user.class_id == user.class_id)) and (
                            current_user.school_id == user.school_id or allowed_permission(current_user, permission3))):
                db_sess.close()
                abort(403)
        elif max(list(map(int, user.statuses.split(", ")))) in [2, 3, 4]:
            permission1 = db_sess.query(Permission).filter(Permission.title == "editing_self_school").first()  # noqa
            permission2 = db_sess.query(Permission).filter(Permission.title == "editing_school").first()  # noqa

            if not (allowed_permission(current_user, permission2) or (
                    allowed_permission(current_user, permission1) and current_user.school_id == user.school_id)):
                db_sess.close()
                abort(403)

    db_sess.close()

    data = {
        "statuses_titles": statuses_titles,
        "permissions": permissions,
        "user": user,
        "admin": allowed_permission(current_user, permission3),
        "school": school
    }

    return render_template("profile.html", **data)  # noqa


@bp.route('/<user_id>/edit_fullname', methods=['GET', 'POST'])
@login_required
def change_fullname(user_id):
    if not current_user.is_registered:
        return redirect(url_for("auth.finish_register"))

    db_sess = create_session()

    user = db_sess.query(User).filter(User.id == user_id).first()
    if current_user.id == int(user_id):
        permission = db_sess.query(Permission).filter(Permission.title == "changing_fullname").first()  # noqa
        if not allowed_permission(user, permission):
            db_sess.close()
            abort(405)
    else:
        permission1 = db_sess.query(Permission).filter(Permission.title == "editing_self_class").first()  # noqa
        permission2 = db_sess.query(Permission).filter(Permission.title == "editing_classes").first()  # noqa
        permission3 = db_sess.query(Permission).filter(Permission.title == "editing_school").first()  # noqa

        if not ((allowed_permission(current_user, permission2) or (
                allowed_permission(current_user, permission1) and current_user.class_id == user.class_id)) and (
                        current_user.school_id == user.school_id or allowed_permission(current_user, permission3))):
            db_sess.close()
            abort(403)

    form = ChangeFullnameForm()
    data = {
        'form': form,
        'message': None
    }

    if form.validate_on_submit():
        fullname = form.fullname.data

        if not all([symbol in RUSSIAN_ALPHABET + ' ' for symbol in fullname]):
            data['message'] = "Поле заполнено неверно. Используйте только буквы русского алфавита"
        else:
            user.fullname = ' '.join(list(map(lambda name: name.lower().capitalize(), fullname.split())))

            db_sess.commit()
            db_sess.close()
            return redirect(url_for(".profile_user", user_id=user_id))
    db_sess.close()
    return render_template('change_fullname.html', **data)  # noqa


@bp.route('/<user_id>/edit_login', methods=['GET', 'POST'])
@login_required
def change_login(user_id):
    if not current_user.is_registered:
        return redirect(url_for("auth.finish_register"))

    db_sess = create_session()

    user = db_sess.query(User).filter(User.id == user_id).first()
    if current_user.id == int(user_id):
        permission = db_sess.query(Permission).filter(Permission.title == "changing_login").first()  # noqa
    else:
        permission = db_sess.query(Permission).filter(Permission.title == "editing_user").first()  # noqa
    if not allowed_permission(current_user, permission):
        db_sess.close()
        abort(403)

    form = ChangeLoginForm()
    data = {
        'form': form,
        'message': None
    }

    if form.validate_on_submit():
        user_login = form.login.data

        if not all([symbol in ascii_letters + digits for symbol in user_login]):
            data['message'] = "Логин содержит некорректные символы"
        else:
            user.login = user_login.lower()

            db_sess.commit()
            db_sess.close()
            return redirect(url_for(".profile_user", user_id=user_id))

    db_sess.close()

    return render_template('change_login.html', **data)  # noqa


@bp.route('/<user_id>/edit_password', methods=['GET', 'POST'])
@login_required
def change_password(user_id):
    if not current_user.is_registered:
        return redirect(url_for("auth.finish_register"))

    db_sess = create_session()

    user = db_sess.query(User).filter(User.id == user_id).first()
    if current_user.id == int(user_id):
        permission = db_sess.query(Permission).filter(Permission.title == "changing_password").first()  # noqa
    else:
        permission = db_sess.query(Permission).filter(Permission.title == "editing_user").first()  # noqa
    if not allowed_permission(current_user, permission):
        db_sess.close()
        abort(403)

    form = ChangePasswordForm()
    data = {
        'form': form,
        'message': None
    }

    if form.validate_on_submit():
        old_password = form.old_password.data
        new_password = form.new_password.data
        new_password_again = form.new_password_again.data

        if not all([symbol in ascii_letters + digits + punctuation for symbol in
                    form.new_password.data]):
            data['message'] = "Пароль содержит некорректные символы"
        elif new_password != new_password_again:
            data['message'] = "Пароли не совпадают"
        elif not user.check_password(old_password):  # noqa
            data['message'] = "Неверный пароль"
        elif form.old_password.data == form.new_password.data:
            data['message'] = "Новый пароль совпадает со старым"
        else:
            user.set_password(new_password)  # noqa

            db_sess.commit()
            db_sess.close()
            return redirect(url_for(".profile_user", user_id=user_id))

    db_sess.close()

    return render_template('change_password.html', **data)  # noqa


@bp.route('/<user_id>/delete_login', methods=['GET', 'POST'])
@login_required
def delete_login(user_id):
    if not current_user.is_registered:
        return redirect(url_for("auth.finish_register"))

    if delete_login_data(int(user_id), current_user) == 403:
        abort(403)

    return redirect(url_for(".profile_user", user_id=user_id))


@bp.route('/<user_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_registered:
        return redirect(url_for("auth.finish_register"))

    if del_user(int(user_id), current_user) == 403:
        abort(403)

    return redirect(url_for("home"))
