from flask import redirect, url_for, abort, render_template
from flask_login import login_required, current_user

from app.data.models import User, Permission, School, Status
from app.data.forms import ChangeFullnameForm, SelectUser
from app.data.functions import allowed_permission
from app.data.db_session import create_session
from app.modules.schools.school.teachers import bp
from app import RUSSIAN_ALPHABET


@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_teacher(school_id):
    school_id = int(school_id)  # noqa

    if not current_user.is_registered:
        return redirect(url_for("auth.finish_register"))

    db_sess = create_session()

    school = db_sess.query(School).filter(School.id == school_id).first()  # noqa

    permission1 = db_sess.query(Permission).filter(Permission.title == "editing_self_school").first()  # noqa
    permission2 = db_sess.query(Permission).filter(Permission.title == "editing_school").first()  # noqa

    if not (allowed_permission(current_user, permission2) or (
            allowed_permission(current_user, permission1) and current_user.school_id == school_id)):
        db_sess.close()
        abort(403)

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
            teacher.statuses = 2
            teacher.generate_key()

            db_sess.add(teacher)
            db_sess.commit()
            db_sess.close()

            return redirect(url_for("schools.school.school_info", school_id=school_id))

    db_sess.close()

    return render_template('add_teacher.html', **data)  # noqa


@bp.route('/add_existing', methods=['GET', 'POST'])
@login_required
def add_existing_teacher(school_id):
    school_id = int(school_id)  # noqa

    if not current_user.is_registered:
        return redirect(url_for("auth.finish_register"))

    db_sess = create_session()

    school = db_sess.query(School).filter(School.id == school_id).first()  # noqa

    permission1 = db_sess.query(Permission).filter(Permission.title == "editing_self_school").first()  # noqa
    permission2 = db_sess.query(Permission).filter(Permission.title == "editing_school").first()  # noqa

    if not (allowed_permission(current_user, permission2) or (
            allowed_permission(current_user, permission1) and current_user.school_id == school_id)):
        db_sess.close()
        abort(403)

    form = SelectUser()

    school_users = db_sess.query(User).filter(User.school_id == school_id).all()  # noqa
    users = [(0, "Выбрать...")]
    for us in school_users:  # noqa
        statuses = db_sess.query(Status).filter(Status.id.in_(us.statuses.split(", "))).all()  # noqa
        status = list(sorted(statuses, key=lambda s: s.id, reverse=True))[0]
        if status.title in ["Модератор", "Классный руководитель"] and "Учитель" not in list(
                map(lambda s: s.title, statuses)):
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
            user = db_sess.query(User).filter(User.id == user_id).first()  # noqa
            user.statuses = ", ".join(list(map(str, (list(sorted(list(map(int, user.statuses.split(", "))) + [  # noqa
                db_sess.query(Status).filter(Status.title == "Учитель").first().id]))))))  # noqa

            db_sess.commit()
            db_sess.close()

            return redirect(url_for("schools.school.school_info", school_id=school_id))
        data["message"] = "Вы не выбрали пользователя"

    db_sess.close()

    return render_template('add_existing_teacher.html', **data)  # noqa
