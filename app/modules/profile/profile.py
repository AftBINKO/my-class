from string import ascii_letters, digits, punctuation

from flask import redirect, url_for, abort, render_template, request, session
from flask_login import login_required, current_user

from app.data.functions import all_permissions, check_permission, get_max_role, get_titles_roles
from app.data.models import User, Permission, School
from app.data.db_session import create_session
from app.data.forms import ChangeFullnameForm
from app import RUSSIAN_ALPHABET

from app.modules.profile.forms import ChangeLoginForm, ChangePasswordForm
from app.modules.profile.functions import delete_user as del_user
from app.modules.profile.functions import delete_login_data
from app.modules.profile import bp


@bp.before_request
@login_required
def check_register():
    if not current_user.is_registered:
        abort(401)


@bp.route('/')
@bp.route('/my')
@bp.route('/<int:user_id>')
@login_required
def profile(user_id=None):
    db_sess = create_session()

    if not user_id:
        user_id = current_user.id

    user = db_sess.query(User).get(user_id)
    if not user:
        abort(404)

    school = db_sess.query(School).filter_by(id=user.school_id).first()
    roles_titles = get_titles_roles(user)

    permissions = None
    permission3 = db_sess.query(Permission).filter_by(title="access_control_panel").first()
    if current_user.id == user_id:
        permissions = set(map(lambda permission: permission.title, all_permissions(user)))
    else:
        max_role_id = get_max_role(user).id
        if max_role_id == 1:
            permission1 = db_sess.query(Permission).filter_by(title="editing_self_group").first()  # noqa
            permission2 = db_sess.query(Permission).filter_by(title="editing_groups").first()
            permission3 = db_sess.query(Permission).filter_by(title="editing_school").first()

            if not ((check_permission(current_user, permission2) or (
                    check_permission(current_user, permission1) and current_user.group_id == user.group_id)) and (
                            current_user.school_id == user.school_id or check_permission(current_user, permission3))):
                db_sess.close()
                abort(403)
        elif max_role_id in [2, 3, 4]:
            permission1 = db_sess.query(Permission).filter_by(title="editing_self_school").first()
            permission2 = db_sess.query(Permission).filter_by(title="editing_school").first()

            if not (check_permission(current_user, permission2) or (
                    check_permission(current_user, permission1) and current_user.school_id == user.school_id)):
                db_sess.close()
                abort(403)

    db_sess.close()

    data = {
        "roles_titles": roles_titles,
        "permissions": permissions,
        "user": user,
        "admin": check_permission(current_user, permission3),
        "school": school
    }

    return render_template("profile.html", **data)  # noqa


@bp.route('/<int:user_id>/change_home_page/<page>', methods=['GET', 'POST'])
@bp.route('/my/change_home_page/<page>', methods=['GET', 'POST'])
@bp.route('/change_home_page/<page>', methods=['GET', 'POST'])
@login_required
def change_home_page(page, user_id=None):
    db_sess = create_session()

    if not user_id:
        user_id = current_user.id

    user = db_sess.query(User).get(user_id)

    if not current_user.id == user_id:
        db_sess.close()
        abort(403)

    match page:
        case "control_panel":
            permission = db_sess.query(Permission).filter_by(title="access_control_panel").first()
            if not check_permission(current_user, permission):
                db_sess.close()
                abort(401)

            user.home_page = "control_panel"

        case "my_school":
            if not current_user.school_id:
                abort(401)

            user.home_page = "my_school"

        case "my_group":
            if not current_user.group_id:
                abort(401)

            user.home_page = "my_group"

        case "profile":
            user.home_page = "profile"

        case _:
            abort(404)

    db_sess.commit()
    return redirect(session.pop('url', url_for("home")))


@bp.route('/<int:user_id>/edit_fullname', methods=['GET', 'POST'])
@bp.route('/my/edit_fullname', methods=['GET', 'POST'])
@bp.route('/edit_fullname', methods=['GET', 'POST'])
@login_required
def change_fullname(user_id=None):
    db_sess = create_session()

    if not user_id:
        user_id = current_user.id

    user = db_sess.query(User).get(user_id)
    if not user:
        abort(404)

    if current_user.id == user_id:
        permission = db_sess.query(Permission).filter_by(title="changing_fullname").first()
        if not check_permission(user, permission):
            db_sess.close()
            abort(405)
    else:
        permission1 = db_sess.query(Permission).filter_by(title="editing_self_group").first()  # noqa
        permission2 = db_sess.query(Permission).filter_by(title="editing_groups").first()
        permission3 = db_sess.query(Permission).filter_by(title="editing_school").first()

        if not ((check_permission(current_user, permission2) or (
                check_permission(current_user, permission1) and current_user.group_id == user.group_id)) and (
                        current_user.school_id == user.school_id or check_permission(current_user, permission3))):
            db_sess.close()
            abort(403)

    form = ChangeFullnameForm()
    if not form.fullname.data:
        form.fullname.data = user.fullname

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
            return redirect(session.pop('url', url_for(".profile", user_id=user_id)))
    db_sess.close()
    return render_template('change_fullname.html', **data)  # noqa


@bp.route('/<int:user_id>/edit_login', methods=['GET', 'POST'])
@bp.route('/my/edit_login', methods=['GET', 'POST'])
@bp.route('/edit_login', methods=['GET', 'POST'])
@login_required
def change_login(user_id=None):
    db_sess = create_session()

    if not user_id:
        user_id = current_user.id

    user = db_sess.query(User).get(user_id)

    if not current_user.id == user_id:
        db_sess.close()
        abort(403)

    permission = db_sess.query(Permission).filter_by(title="changing_login").first()
    if not check_permission(current_user, permission):
        db_sess.close()
        abort(403)

    form = ChangeLoginForm()
    if not form.login.data:
        form.login.data = user.login

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
            return redirect(session.pop('url', url_for(".profile", user_id=user_id)))

    db_sess.close()

    return render_template('change_login.html', **data)  # noqa


@bp.route('/<int:user_id>/edit_password', methods=['GET', 'POST'])
@bp.route('/my/edit_password', methods=['GET', 'POST'])
@bp.route('/edit_password', methods=['GET', 'POST'])
@login_required
def change_password(user_id=None):
    db_sess = create_session()

    if not user_id:
        user_id = current_user.id

    user = db_sess.query(User).get(user_id)

    if not current_user.id == user_id:
        db_sess.close()
        abort(403)

    permission = db_sess.query(Permission).filter_by(title="changing_password").first()
    if not check_permission(current_user, permission):
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
        elif not user.check_password(old_password):
            data['message'] = "Неверный пароль"
        elif form.old_password.data == form.new_password.data:
            data['message'] = "Новый пароль совпадает со старым"
        else:
            user.set_password(new_password)

            db_sess.commit()
            db_sess.close()
            return redirect(session.pop('url', url_for(".profile", user_id=user_id)))

    db_sess.close()

    return render_template('change_password.html', **data)  # noqa


@bp.route('/<int:user_id>/delete_login', methods=['GET', 'POST'])
@bp.route('/my/delete_login', methods=['GET', 'POST'])
@bp.route('/delete_login', methods=['GET', 'POST'])
@login_required
def delete_login(user_id=None):
    if not user_id:
        user_id = current_user.id

    role = delete_login_data(user_id, current_user)

    match role:
        case 403:
            abort(403)
        case 404:
            abort(404)

    return redirect(session.pop('url', url_for(".profile", user_id=user_id)))


@bp.route('/<int:user_id>/delete', methods=['GET', 'POST'])
@bp.route('/my/delete', methods=['GET', 'POST'])
@bp.route('/delete_profile', methods=['GET', 'POST'])
@login_required
def delete_user(user_id=None):
    if not user_id:
        user_id = current_user.id

    role = del_user(user_id, current_user)

    match role:
        case 403:
            abort(403)
        case 404:
            abort(404)

    return redirect(session.pop('url', url_for("home")))
