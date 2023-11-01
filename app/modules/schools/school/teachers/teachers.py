from flask import redirect, url_for, abort, render_template
from flask_login import login_required, current_user

from app.data.models import User, Permission, School, Role
from app.data.forms import ChangeFullnameForm, SelectUser
from app.data.functions import check_permission, add_role, get_roles, get_max_role
from app.data.db_session import create_session
from app.modules.schools.school.teachers import bp
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
def add_teacher(school_id):
    db_sess = create_session()  # noqa

    school = db_sess.query(School).get(school_id)

    form = ChangeFullnameForm()
    data = {
        'title': f'Создать учителя в {school.name}',
        'form': form,
        'school': school,
        'message': None
    }

    if form.validate_on_submit():
        teacher = User()

        if not all([symbol in RUSSIAN_ALPHABET + ' ' for symbol in form.fullname.data]):
            data['message'] = "Поле заполнено неверно. Используйте только буквы русского алфавита"
        else:
            teacher.fullname = ' '.join(list(map(lambda name: name.lower().capitalize(), form.fullname.data.split())))
            teacher.school_id = school_id
            teacher.roles = 2
            teacher.generate_key()

            db_sess.add(teacher)
            db_sess.commit()
            db_sess.close()

            return redirect(url_for("schools.school.users", school_id=school_id))

    db_sess.close()

    return render_template('add_teacher.html', **data)  # noqa


@bp.route('/add_existing', methods=['GET', 'POST'])
@login_required
def add_existing_teacher(school_id):
    db_sess = create_session()  # noqa

    school = db_sess.query(School).get(school_id)

    form = SelectUser()

    school_users = db_sess.query(User).filter_by(school_id=school_id).all()
    users = [(0, "Выбрать...")]
    for us in school_users:  # noqa
        roles = get_roles(us)
        role = get_max_role(us)
        if role.title in ["Модератор", "Классный руководитель"] and "Учитель" not in list(
                map(lambda s: s.title, roles)):
            users.append((us.id, us.fullname))

    form.select.choices = users

    data = {
        'form': form,
        'school': school,
        'title': f"Выбрать учителя в {school.name}",
        'message': None
    }

    if form.validate_on_submit():
        user_id = int(form.select.data)
        if user_id:
            add_role(user_id, "Учитель")
            db_sess.close()

            return redirect(url_for("schools.school.users", school_id=school_id))
        data["message"] = "Вы не выбрали пользователя"

    db_sess.close()

    return render_template('add_existing_teacher.html', **data)  # noqa
