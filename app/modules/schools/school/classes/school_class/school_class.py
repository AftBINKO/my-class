from os import path

from flask import redirect, url_for, abort, render_template, send_file
from flask_login import login_required, current_user

from xlsxwriter import Workbook

from app.modules.schools.school.classes.school_class.functions import delete_classes
from app.data.functions import allowed_permission, check_status, all_permissions
from app.modules.schools.school.classes.school_class.forms import EditClassForm
from app.data.models import User, Permission, School, Class, Status
from app.modules.schools.school.classes.school_class import bp
from app.data.db_session import create_session


@bp.route('/', methods=['GET', 'POST'])
@login_required
def class_info(school_id, class_id):
    school_id, class_id = int(school_id), int(class_id)  # noqa

    if not current_user.is_registered:
        return redirect(url_for("auth.finish_register"))

    db_sess = create_session()
    permissions = set(map(lambda permission: permission.title, all_permissions(current_user)))
    school = db_sess.query(School).filter(School.id == school_id).first()  # noqa

    permission1 = db_sess.query(Permission).filter(Permission.title == "view_self_details_class").first()  # noqa
    permission2 = db_sess.query(Permission).filter(Permission.title == "view_details_classes").first()  # noqa
    permission3 = db_sess.query(Permission).filter(Permission.title == "view_schools").first()  # noqa
    permission4 = db_sess.query(Permission).filter(Permission.title == "editing_classes").first()  # noqa

    if not ((allowed_permission(current_user, permission2) or (  # noqa
            allowed_permission(current_user, permission1) and current_user.class_id == class_id)) and (
                    current_user.school_id == school_id or allowed_permission(current_user, permission3))):
        db_sess.close()
        abort(403)

    school = db_sess.query(School).filter(School.id == school_id).first()  # noqa
    school_class = db_sess.query(Class).filter(Class.id == class_id).first()  # noqa

    students = []
    class_teacher = None

    for user in db_sess.query(User).filter(User.class_id == class_id).all():  # noqa
        if check_status(user, "Ученик"):
            students.append(user)
        elif check_status(user, "Классный руководитель"):
            class_teacher = user

    students.sort(key=lambda st: st.fullname.split()[0])

    data = {
        "school": school,
        "permissions": permissions,
        "students": students,
        "class_teacher": class_teacher,
        "class": school_class,
    }

    db_sess.close()
    return render_template("class_info.html", **data)


@bp.route('/edit', methods=['GET', 'POST'])
@login_required
def edit_class(school_id, class_id):
    school_id, class_id = int(school_id), int(class_id)  # noqa  # TODO: преобразовать URL к int

    db_sess = create_session()

    if not current_user.is_registered:
        return redirect(url_for("auth.finish_register"))

    permission1 = db_sess.query(Permission).filter(Permission.title == "editing_self_class").first()  # noqa
    permission2 = db_sess.query(Permission).filter(Permission.title == "editing_classes").first()  # noqa
    permission3 = db_sess.query(Permission).filter(Permission.title == "editing_school").first()  # noqa
    permission4 = db_sess.query(Permission).filter(Permission.title == "deleting_classes").first()  # noqa
    permission5 = db_sess.query(Permission).filter(Permission.title == "deleting_self_class").first()  # noqa

    is_deleting_class = allowed_permission(current_user, permission4) or (
            allowed_permission(current_user, permission5) and current_user.class_id == class_id)

    if not ((allowed_permission(current_user, permission2) or (
            allowed_permission(current_user, permission1) and current_user.class_id == class_id)) and (
                    current_user.school_id == school_id or allowed_permission(current_user, permission3))):
        db_sess.close()
        abort(403)

    form = EditClassForm()
    school = db_sess.query(School).filter(School.id == school_id).first()  # noqa
    school_class = db_sess.query(Class).filter(Class.id == class_id).first()  # noqa
    data = {
        'form': form,
        'school': school,
        'class': school_class,
        'is_deleting_class': is_deleting_class
    }

    if form.validate_on_submit():
        school_class.class_number = form.class_number.data
        school_class.letter = form.letter.data

        db_sess.commit()
        db_sess.close()

        return redirect(
            url_for(".class_info", school_id=school_id, class_id=class_id))

    db_sess.close()

    return render_template('edit_class.html', **data)


@bp.route('/delete', methods=['GET', 'POST'])
@login_required
def delete_class(school_id, class_id):
    if not current_user.is_registered:
        return redirect(url_for("auth.finish_register"))

    if delete_classes(int(school_id), int(class_id), current_user) == 405:
        abort(403)

    return redirect(url_for("schools.school.school_info", school_id=school_id))


@bp.route('/download_excel', methods=['GET', 'POST'])
@login_required
def download_excel(school_id, class_id):
    school_id, class_id = int(school_id), int(class_id)  # noqa

    db_sess = create_session()

    school_class = db_sess.query(Class).filter(Class.id == class_id).first()  # noqa

    permission1 = db_sess.query(Permission).filter(Permission.title == "editing_self_class").first()  # noqa
    permission2 = db_sess.query(Permission).filter(Permission.title == "editing_classes").first()  # noqa
    permission3 = db_sess.query(Permission).filter(Permission.title == "editing_school").first()  # noqa

    if not ((allowed_permission(current_user, permission2) or (
            allowed_permission(current_user, permission1) and current_user.class_id == class_id)) and (
                    current_user.school_id == school_id or allowed_permission(current_user, permission3))):
        db_sess.close()
        abort(403)

    tmp_path = path.abspath("app/static/tmp/table.xlsx")
    students = [user for user in db_sess.query(User).filter(User.class_id == class_id).all() if  # noqa
                db_sess.query(Status).filter(Status.title == "Ученик").first().id in set(  # noqa
                    map(int, user.statuses.split(", ")))]

    with Workbook(tmp_path) as workbook:
        worksheet = workbook.add_worksheet(f"{school_class.class_number}{school_class.letter}")

        header_row_format = workbook.add_format({'bold': True})  # noqa
        worksheet.set_row(0, None, header_row_format)

        headers = ["ФИО", "В школе?", "Дата и время прибытия"]

        for col, header in enumerate(headers):
            worksheet.write(0, col, header)

        for row, student in enumerate(students, start=1):
            worksheet.write(row, 0, student.fullname)
            if student.is_arrived:
                worksheet.write(row, 1, "Да")
            elif student.is_arrived is not None:
                worksheet.write(row, 1, "Нет")
            if student.arrival_time:
                worksheet.write(row, 2, student.arrival_time.strftime("%d.%m.%Y %H:%M"))

    return send_file(tmp_path, as_attachment=True,
                     download_name=f"{school_class.class_number}{school_class.letter}.xlsx")
