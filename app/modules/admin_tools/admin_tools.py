from flask import redirect, url_for, abort, render_template
from flask_login import login_required, current_user

from app.data.models import Permission, School, User, Status
from app.data.forms import ChangeFullnameForm, SelectUser
from app.data.functions import allowed_permission
from app.data.db_session import create_session
from app import RUSSIAN_ALPHABET
from app.modules.admin_tools import bp


@bp.route('/admin_panel')
@login_required
def admin_panel():
    if not current_user.is_registered:  # noqa
        return redirect(url_for("auth.finish_register"))

    db_sess = create_session()

    permission = db_sess.query(Permission).filter(Permission.title == "access_admin_panel").first()  # noqa
    if not allowed_permission(current_user, permission):
        db_sess.close()
        abort(403)

    schools = db_sess.query(School).all()
    admins = [user for user in db_sess.query(User).all() if
              max(list(map(int, user.statuses.split(", ")))) == db_sess.query(Status).filter(
                  Status.title == "Администратор").first().id]  # noqa

    db_sess.close()

    data = {
        "schools": schools,
        "admins": admins
    }

    return render_template("admin_panel.html", **data)


@bp.route('/admin_panel/admins/add', methods=['GET', 'POST'])
@login_required
def add_admin():
    if not current_user.is_registered:  # noqa
        return redirect(url_for("auth.finish_register"))

    db_sess = create_session()

    permission = db_sess.query(Permission).filter(Permission.title == "access_admin_panel").first()  # noqa
    if not allowed_permission(current_user, permission):
        db_sess.close()
        abort(403)

    form = ChangeFullnameForm()
    data = {
        'form': form,
        'title': 'Добавить администратора',
        'message': None
    }

    if form.validate_on_submit():
        admin = User()

        if not all([symbol in RUSSIAN_ALPHABET + ' ' for symbol in form.fullname.data]):
            data['message'] = "Поле заполнено неверно. Используйте только буквы русского алфавита"
        else:
            admin.fullname = ' '.join(list(map(lambda name: name.lower().capitalize(), form.fullname.data.split())))
            admin.statuses = 5
            admin.generate_key()

            db_sess.add(admin)
            db_sess.commit()
            db_sess.close()

            return redirect(url_for(".admin_panel"))

    db_sess.close()

    return render_template('add_user.html', **data)


@bp.route('/admin_panel/admins/add_existing', methods=['GET', 'POST'])
@login_required
def add_existing_admin():
    if not current_user.is_registered:  # noqa
        return redirect(url_for("auth.finish_register"))

    db_sess = create_session()

    permission = db_sess.query(Permission).filter(Permission.title == "access_admin_panel").first()  # noqa
    if not allowed_permission(current_user, permission):
        db_sess.close()
        abort(403)

    form = SelectUser()
    form.select.choices = [(0, "Выбрать...")] + [
        (us.id, us.fullname) for us in db_sess.query(User).all() if
        max(list(map(int, us.statuses.split(", ")))) != db_sess.query(Status).filter(
            Status.title == "Администратор").first().id  # noqa
    ]

    data = {
        'form': form,
        'title': "Выбрать администратора",
        'message': None
    }

    if form.validate_on_submit():
        user_id = int(form.select.data)
        if user_id:
            user = db_sess.query(User).filter(User.id == user_id).first()  # noqa
            user.statuses = ", ".join(list(map(str, (list(sorted(list(map(int, user.statuses.split(", "))) + [  # noqa
                db_sess.query(Status).filter(Status.title == "Администратор").first().id]))))))  # noqa

            db_sess.commit()
            db_sess.close()

            return redirect(url_for(".admin_panel"))

        data["message"] = "Вы не выбрали пользователя"

    db_sess.close()

    return render_template('add_existing.html', **data)
