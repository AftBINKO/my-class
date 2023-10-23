from flask import redirect, url_for, abort, render_template
from flask_login import login_required, current_user

from app.modules.schools.school.classes.school_class.class_teacher import bp
from app.data.models import User, Permission, School, Class, Status
from app.data.forms import ChangeFullnameForm, SelectUser
from app.data.functions import allowed_permission, add_status
from app.data.db_session import create_session
from app import RUSSIAN_ALPHABET


@bp.url_value_preprocessor
def check_permissions(endpoint, values):
    school_id = values['school_id']  # noqa

    db_sess = create_session()

    permission1 = db_sess.query(Permission).filter_by(title="editing_self_school").first()
    permission2 = db_sess.query(Permission).filter_by(title="editing_school").first()

    if not (allowed_permission(current_user, permission2) or (
            allowed_permission(current_user, permission1) and current_user.school_id == school_id)):
        db_sess.close()
        abort(403)


@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_class_teacher(school_id, class_id):
    db_sess = create_session()

    school = db_sess.query(School).get(school_id)
    school_class = db_sess.query(Class).get(class_id)

    form = ChangeFullnameForm()

    title = f"Создать классного руководителя в {school_class.class_number} "
    if school_class.letter:
        title += f'"{school_class.letter}" '
    title += f"класс {school.name}"

    data = {
        'form': form,
        'title': title,
        'school': school,
        'class': school_class,
        'message': None
    }

    if form.validate_on_submit():
        teacher = User()

        if not all([symbol in RUSSIAN_ALPHABET + ' ' for symbol in form.fullname.data]):
            data['message'] = "Поле заполнено неверно. Используйте только буквы русского алфавита"
        else:
            teacher.fullname = ' '.join(list(map(lambda name: name.lower().capitalize(), form.fullname.data.split())))
            teacher.school_id = school_id
            teacher.class_id = class_id
            teacher.statuses = 3
            teacher.generate_key()

            db_sess.add(teacher)
            db_sess.commit()
            db_sess.close()

            return redirect(
                url_for("schools.school.classes.school_class.class_info",
                        school_id=school_id, class_id=class_id))

    db_sess.close()

    return render_template('add_class_teacher.html', **data)  # noqa


@bp.route('/add_existing', methods=['GET', 'POST'])
@login_required
def add_existing_class_teacher(school_id, class_id):
    db_sess = create_session()

    school = db_sess.query(School).get(school_id)
    school_class = db_sess.query(Class).get(class_id)

    form = SelectUser()  # noqa

    school_users = db_sess.query(User).filter_by(school_id=school_id).all()
    users = [(0, "Выбрать...")]
    for us in school_users:
        statuses = db_sess.query(Status).filter(Status.id.in_(us.statuses.split(", "))).all()  # noqa
        status = list(sorted(statuses, key=lambda s: s.id, reverse=True))[0]
        if status.title in ["Модератор", "Учитель"] and "Классный руководитель" not in list(
                map(lambda s: s.title, statuses)):
            users.append((us.id, us.fullname))

    form.select.choices = users

    title = f"Выбрать классного руководителя в {school_class.class_number} "
    if school_class.letter:
        title += f'"{school_class.letter}" '
    title += f"класс {school.name}"

    data = {
        'form': form,
        'school': school,
        'title': title,
        'message': None
    }

    if form.validate_on_submit():
        user_id = int(form.select.data)
        if user_id:
            user = db_sess.query(User).get(user_id)
            add_status(user, "Классный руководитель")
            user.class_id = class_id

            db_sess.commit()
            db_sess.close()

            return redirect(
                url_for("schools.school.classes.school_class.class_info",
                        school_id=school_id, class_id=class_id))
        data["message"] = "Вы не выбрали пользователя"

    db_sess.close()

    return render_template('add_existing.html', **data)
