from flask import redirect, url_for, abort, render_template
from flask_login import login_required, current_user

from app.data.functions import check_permission, check_role, add_role
from app.data.models import Permission, School, User, Role
from app.data.forms import ChangeFullnameForm, SelectUser
from app.data.db_session import create_session
from app.modules.control_panel import bp
from app import RUSSIAN_ALPHABET


@bp.before_request
@login_required
def check_permissions():
    if not current_user.is_registered:
        abort(401)

    db_sess = create_session()

    permission = db_sess.query(Permission).filter_by(title="access_control_panel").first()
    if not check_permission(current_user, permission):
        db_sess.close()
        abort(403)

    db_sess.close()


@bp.route('/')
def control_panel():
    db_sess = create_session()

    schools = db_sess.query(School).all()
    admins = [user for user in db_sess.query(User).all() if check_role(user, "Администратор")]

    db_sess.close()

    data = {
        "schools": schools,
        "admins": admins
    }

    return render_template("control_panel.html", **data)  # noqa


@bp.route('/admins/add', methods=['GET', 'POST'])
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
            admin.roles = 5
            admin.generate_key()

            db_sess = create_session()
            db_sess.add(admin)
            db_sess.commit()
            db_sess.close()

            return redirect(url_for(".control_panel"))

    return render_template('add_admin.html', **data)  # noqa


@bp.route('/admins/add_existing', methods=['GET', 'POST'])
def add_existing_admin():
    form = SelectUser()

    db_sess = create_session()
    form.select.choices = [(0, "Выбрать...")] + [
        (us.id, us.fullname) for us in db_sess.query(User).all() if not check_role(us, "Администратор")
    ]
    db_sess.close()

    data = {
        'form': form,
        'title': "Выбрать администратора",
        'message': None
    }

    if form.validate_on_submit():
        user_id = int(form.select.data)
        if user_id:
            add_role(user_id, "Администратор")
            return redirect(url_for(".control_panel"))

        data["message"] = "Вы не выбрали пользователя"

    db_sess.close()

    return render_template('add_existing_admin.html', **data)  # noqa
