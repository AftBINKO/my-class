from os import path

from flask import redirect, url_for, abort, render_template, send_file
from flask_login import login_required, current_user

from xlsxwriter import Workbook

from app.data.models import School, Permission, User, Status, Class
from app.data.functions import all_permissions, allowed_permission
from app.modules.schools.school.functions import delete_schools
from app.modules.schools.forms import EditSchoolForm
from app.data.db_session import create_session
from app.modules.schools.school import bp


@bp.route('/')  # TODO: Добавить метод, который будет проверять правильность написания id школы
@login_required
def school_info(school_id):
    school_id = int(school_id)

    if not current_user.is_registered:
        return redirect(url_for("auth.finish_register"))

    db_sess = create_session()
    permissions = set(map(lambda permission: permission.title, all_permissions(current_user)))

    permission1 = db_sess.query(Permission).filter(Permission.title == "view_self_school").first()  # noqa
    permission2 = db_sess.query(Permission).filter(Permission.title == "view_schools").first()  # noqa
    if not (allowed_permission(current_user, permission2) or (
            allowed_permission(current_user, permission1) and current_user.school_id == school_id)):
        db_sess.close()
        abort(403)

    school = db_sess.query(School).filter(School.id == school_id).first()  # noqa
    classes = db_sess.query(Class).filter(Class.school_id == school_id).all()  # noqa

    users = db_sess.query(User).filter(User.school_id == school_id).all()  # noqa
    moderators = []
    teachers = []
    for user in users:
        statuses = list(map(int, user.statuses.split(", ")))
        if 4 in statuses:
            moderators.append(user)
        if 2 in statuses:
            teachers.append(user)

    moderators.sort(key=lambda moder: moder.fullname.split()[0])
    teachers.sort(key=lambda teacher: teacher.fullname.split()[0])

    db_sess.close()

    data = {
        "school": school,
        "permissions": permissions,
        "classes": classes,
        "moderators": moderators,
        "teachers": teachers
    }

    return render_template("school_info.html", **data)  # noqa


@bp.route('/download_excel', methods=['GET', 'POST'])
@login_required
def download_school_excel(school_id):
    school_id = int(school_id)

    db_sess = create_session()

    permission1 = db_sess.query(Permission).filter(Permission.title == "view_self_school").first()  # noqa
    permission2 = db_sess.query(Permission).filter(Permission.title == "view_schools").first()  # noqa
    if not (allowed_permission(current_user, permission2) or (
            allowed_permission(current_user, permission1) and current_user.school_id == school_id)):
        db_sess.close()
        abort(403)

    tmp_path = path.abspath("app/static/tmp/table.xlsx")
    school = db_sess.query(School).filter(School.id == school_id).first()  # noqa
    classes = db_sess.query(Class).filter(Class.school_id == school_id).all()  # noqa

    with Workbook(tmp_path) as workbook:
        for school_class in classes:
            worksheet = workbook.add_worksheet(f"{school_class.class_number}{school_class.letter}")

            students = [user for user in db_sess.query(User).filter(User.class_id == school_class.id).all() if  # noqa
                        db_sess.query(Status).filter(Status.title == "Ученик").first().id in set(  # noqa
                            map(int, user.statuses.split(", ")))]

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

    return send_file(tmp_path, as_attachment=True, download_name=f"{school.name}.xlsx")


@bp.route('/edit', methods=['GET', 'POST'])
@login_required
def edit_school(school_id):
    school_id = int(school_id)

    if not current_user.is_registered:
        return redirect(url_for("auth.finish_register"))

    db_sess = create_session()

    permission1 = db_sess.query(Permission).filter(Permission.title == "editing_self_school").first()  # noqa
    permission2 = db_sess.query(Permission).filter(Permission.title == "editing_school").first()  # noqa
    permission3 = db_sess.query(Permission).filter(Permission.title == "deleting_school").first()  # noqa
    permission4 = db_sess.query(Permission).filter(Permission.title == "deleting_self_school").first()  # noqa

    if not (allowed_permission(current_user, permission2) or (
            allowed_permission(current_user, permission1) and current_user.school_id == school_id)):
        db_sess.close()
        abort(403)

    is_deleting_school = allowed_permission(current_user, permission3) or (
            allowed_permission(current_user, permission4) and current_user.school_id == school_id)

    form = EditSchoolForm()
    school = db_sess.query(School).filter(School.id == school_id).first()  # noqa
    data = {
        'form': form,
        'school': school,
        "is_deleting_school": is_deleting_school
    }

    if form.validate_on_submit():
        school.name = form.school.data
        school.fullname = form.fullname.data

        db_sess.commit()

        school_id = school.id

        db_sess.close()

        return redirect(url_for(".school_info", school_id=school_id))

    db_sess.close()

    return render_template('edit_school.html', **data)  # noqa


@bp.route('/delete', methods=['GET', 'POST'])
@login_required
def delete_school(school_id):
    if not current_user.is_registered:
        return redirect(url_for("auth.finish_register"))

    if delete_schools(int(school_id), current_user) == 405:
        abort(403)

    return redirect(url_for("home"))