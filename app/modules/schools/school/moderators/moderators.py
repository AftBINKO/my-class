from flask import redirect, url_for, abort, render_template, session
from flask_login import login_required, current_user

from app.data.functions import check_permission, add_role, get_max_role
from app.data.forms import ChangeFullnameForm, SelectUser
from app.data.models import User, Permission, School
from app.modules.schools.school.moderators import bp
from app.data.db_session import create_session
from app import RUSSIAN_ALPHABET


@bp.url_value_preprocessor
@login_required
def check_permissions(endpoint, values):
    school_id = values['school_id']  # noqa

    db_sess = create_session()

    permission1 = db_sess.query(Permission).filter_by(title="editing_self_school").first()
    permission2 = db_sess.query(Permission).filter_by(title="editing_school").first()

    if not (check_permission(current_user, permission2) or (
            check_permission(current_user, permission1) and current_user.school_id == school_id)):
        db_sess.close()
        abort(403)

    db_sess.close()


@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_moderator(school_id):
    db_sess = create_session()  # noqa

    school = db_sess.query(School).get(school_id)

    form = ChangeFullnameForm()
    data = {
        'title': f'Создать модератора в {school.name}',
        'form': form,
        'message': None
    }

    if form.validate_on_submit():
        moder = User()

        if not all([symbol in RUSSIAN_ALPHABET + ' ' for symbol in form.fullname.data]):
            data['message'] = "Поле заполнено неверно. Используйте только буквы русского алфавита"
        else:
            moder.fullname = ' '.join(list(map(lambda name: name.lower().capitalize(), form.fullname.data.split())))
            moder.school_id = school_id
            moder.roles = '[4]'
            moder.generate_key()

            db_sess.add(moder)
            db_sess.commit()
            db_sess.close()

            return redirect(session.pop('url', url_for("schools.school.users", school_id=school_id)))

    db_sess.close()

    return render_template('add_moderator.html', **data)  # noqa


@bp.route('/add_existing', methods=['GET', 'POST'])
@login_required
def add_existing_moderator(school_id):
    db_sess = create_session()  # noqa

    school = db_sess.query(School).get(school_id)

    form = SelectUser()

    school_users = db_sess.query(User).filter_by(school_id=school_id).all()
    users = [(0, "Выбрать...")] + [
        (us.id, us.fullname) for us in school_users if get_max_role(us).title in ["Учитель", "Лидер"]
    ]

    form.select.choices = users

    data = {
        'form': form,
        'school': school,
        'title': f"Выбрать модератора в {school.name}",
        'message': None
    }

    if form.validate_on_submit():
        user_id = int(form.select.data)
        if user_id:
            add_role(user_id, "Модератор")
            db_sess.close()

            return redirect(session.pop('url', url_for("schools.school.users", school_id=school_id)))
        data["message"] = "Вы не выбрали пользователя"

    db_sess.close()

    return render_template('add_existing_moderator.html', **data)  # noqa
