from flask import redirect, url_for, abort, render_template
from flask_login import login_required, current_user

from app.modules.schools.school.classes.school_class.students import bp
from app.data.models import User, Permission, School, Class
from app.data.functions import allowed_permission
from app.data.db_session import create_session
from app.data.forms import ChangeFullnameForm
from app import RUSSIAN_ALPHABET


@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_student(school_id, class_id):
    school_id, class_id = int(school_id), int(class_id)  # noqa

    if not current_user.is_registered:
        return redirect(url_for("auth.finish_register"))

    db_sess = create_session()

    school = db_sess.query(School).filter(School.id == school_id).first()  # noqa
    school_class = db_sess.query(Class).filter(Class.id == class_id).first()  # noqa

    permission1 = db_sess.query(Permission).filter(Permission.title == "editing_self_class").first()  # noqa
    permission2 = db_sess.query(Permission).filter(Permission.title == "editing_classes").first()  # noqa
    permission3 = db_sess.query(Permission).filter(Permission.title == "editing_school").first()  # noqa

    if not ((allowed_permission(current_user, permission2) or (
            allowed_permission(current_user, permission1) and current_user.class_id == class_id)) and (
                    current_user.school_id == school_id or allowed_permission(current_user, permission3))):
        db_sess.close()
        abort(403)

    title = f"Создать ученика в {school_class.class_number} "
    if school_class.letter:
        title += f'"{school_class.letter}" '
    title += f"класс {school.name}"

    form = ChangeFullnameForm()
    data = {
        'title': title,
        'form': form,
        'message': None
    }

    if form.validate_on_submit():
        student = User()

        if not all([symbol in RUSSIAN_ALPHABET + ' ' for symbol in form.fullname.data]):
            data['message'] = "Поле заполнено неверно. Используйте только буквы русского алфавита"
        else:
            student.fullname = ' '.join(list(map(lambda name: name.lower().capitalize(), form.fullname.data.split())))
            student.school_id = school_id
            student.class_id = class_id
            student.statuses = 1
            student.generate_key()

            db_sess.add(student)
            db_sess.commit()
            db_sess.close()

            return redirect(url_for("schools.school.classes.school_class.class_info",
                                    school_id=school_id, class_id=class_id))

    db_sess.close()

    return render_template('add_student.html', **data)  # noqa
