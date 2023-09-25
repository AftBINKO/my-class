from flask import redirect, url_for, abort, render_template
from flask_login import login_required, current_user

from app.data.functions import allowed_permission, check_status
from app.data.models import Permission, School, User, Status
from app.data.forms import ChangeFullnameForm, SelectUser
from app.data.db_session import create_session
from app.modules.admin_tools import bp
from app import RUSSIAN_ALPHABET


@bp.before_request
@login_required
def check_permissions():
    if not current_user.is_registered:
        abort(401)

    db_sess = create_session()

    permission = db_sess.query(Permission).filter_by(title="access_admin_panel").first()
    if not allowed_permission(current_user, permission):
        db_sess.close()
        abort(403)

    db_sess.close()


@bp.route('/admin_panel')
def admin_panel():
    db_sess = create_session()

    schools = db_sess.query(School).all()
    admins = [user for user in db_sess.query(User).all() if check_status(user, "Администратор")]

    db_sess.close()

    data = {
        "schools": schools,
        "admins": admins
    }

    return render_template("admin_panel.html", **data)  # noqa


@bp.route('/admin_panel/admins/add', methods=['GET', 'POST'])
def add_admin():
    form = ChangeFullnameForm()
    data = {
        'form': form,
        'title': 'Создать администратора',
        'message': None
    }

    if form.validate_on_submit():
        if not all([symbol in RUSSIAN_ALPHABET + ' ' for symbol in form.fullname.data]):
            data['message'] = "Поле заполнено неверно. Используйте только буквы русского алфавита"
        else:
            admin = User()
            admin.fullname = ' '.join(list(map(lambda name: name.lower().capitalize(), form.fullname.data.split())))
            admin.statuses = 5
            admin.generate_key()

            db_sess = create_session()
            db_sess.add(admin)
            db_sess.commit()
            db_sess.close()

            return redirect(url_for(".admin_panel"))

    return render_template('add_admin.html', **data)  # noqa


@bp.route('/admin_panel/admins/add_existing', methods=['GET', 'POST'])
def add_existing_admin():
    db_sess = create_session()

    form = SelectUser()
    form.select.choices = [(0, "Выбрать...")] + [
        (us.id, us.fullname) for us in db_sess.query(User).all() if not check_status(us, "Администратор")
    ]

    data = {
        'form': form,
        'title': "Выбрать администратора",
        'message': None
    }

    if form.validate_on_submit():
        user_id = int(form.select.data)
        if user_id:
            user = db_sess.query(User).get(user_id)
            user.statuses = ", ".join(list(map(str, (list(sorted(list(map(int, user.statuses.split(", "))) + [
                db_sess.query(Status).filter_by(title="Администратор").first().id]))))))

            db_sess.commit()
            db_sess.close()

            return redirect(url_for(".admin_panel"))

        data["message"] = "Вы не выбрали пользователя"

    db_sess.close()

    return render_template('add_existing_admin.html', **data)  # noqa
