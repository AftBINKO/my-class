from datetime import datetime, timedelta
from pytz import timezone
from json import load
from os import path

from flask import request, render_template, abort, redirect, url_for, current_app, send_file
from flask_login import login_required, current_user
from xlsxwriter import Workbook

from app.data.functions import all_permissions, check_permission, check_role
from app.modules.schools.school.excel.forms import GenerateForm
from app.data.models import School, Group, Permission, User
from app.modules.schools.school.excel import bp
from app.data.db_session import create_session
from app import CONFIG_PATH, app


@bp.route('/generate', methods=['GET', 'POST'])
@login_required
def generate(school_id):
    db_sess = create_session()
    school = db_sess.query(School).get(school_id)
    permissions = set(map(lambda permission: permission.title, all_permissions(current_user)))

    data = {
        'school': school,
        'permissions': permissions
    }

    form = GenerateForm()

    group_id = request.args.get("group_id")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    if group_id:
        group_id = int(group_id)
    if start_date:
        start_date = datetime.strptime(start_date, "%d.%m.%y").date()
        if not form.start_date.data:
            form.start_date.data = start_date
    if end_date:
        end_date = datetime.strptime(end_date, "%d.%m.%y").date()
        if not form.end_date.data:
            form.end_date.data = end_date

    permission1 = db_sess.query(Permission).filter_by(title="editing_self_school").first()
    permission2 = db_sess.query(Permission).filter_by(title="editing_school").first()
    permission3 = db_sess.query(Permission).filter_by(title="editing_groups").first()
    permission4 = db_sess.query(Permission).filter_by(title="editing_self_group").first()

    if not ((check_permission(current_user, permission2) or (
            check_permission(current_user, permission1) and current_user.school_id == school_id)) and
            check_permission(current_user, permission3)):
        if not check_permission(current_user, permission4):
            db_sess.close()
            abort(403)
        if not group_id:
            return redirect(url_for(".generate", school_id=school_id, group_id=current_user.group_id))
        if current_user.group_id != group_id:
            abort(403)

    groups = db_sess.query(Group).filter_by(school_id=school_id).all()

    choices = []
    for i, c in enumerate(groups):
        if c.id == group_id:
            data['group_index'] = i
        title = str(c.name)
        choices.append((c.id, title))
    form.groups.choices = choices

    data['form'] = form

    if form.validate_on_submit():
        if not ((check_permission(current_user, permission2) or (
                check_permission(current_user, permission1) and current_user.school_id == school_id)) and
                check_permission(current_user, permission3)):
            selected_groups = [db_sess.query(Group).get(current_user.group_id)]
        elif not form.groups.data:
            selected_groups = groups
        else:
            selected_groups = db_sess.query(Group).filter(Group.id.in_(form.groups.data)).all()  # noqa

        start_date = form.start_date.data
        end_date = form.end_date.data

        with open(CONFIG_PATH) as json:
            config_start_date = datetime.strptime(load(json)["clear_times"], "%Y-%m-%d %H:%M:%S.%f").date()
        today = datetime.now().astimezone(timezone("Europe/Moscow")).date()

        if not start_date or start_date <= config_start_date:
            start_date = config_start_date
        if not end_date or end_date >= today:
            end_date = today
        if start_date <= end_date:
            table_path = path.join(current_app.root_path,
                                   path.join(app.config["UPLOAD_FOLDER"], path.join("tables", "table.xlsx")))

            with Workbook(table_path) as workbook:
                k = 1.5  # примерная длина символов

                for group in selected_groups:
                    worksheet = workbook.add_worksheet(f"{group.name}")

                    students = sorted([user for user in db_sess.query(User).filter_by(group_id=group.id).all() if
                                       check_role(user, "Ученик")], key=lambda user: user.fullname.split()[0])

                    header_row_format = workbook.add_format({
                        'bold': True,
                        'align': 'center',
                        'valign': 'vcenter'
                    })
                    worksheet.set_row(0, None, header_row_format)
                    worksheet.set_row(1, None, header_row_format)

                    header_text = "ФИО"
                    worksheet.set_column(0, 0, len(header_text))
                    worksheet.merge_range(0, 0, 1, 0, header_text)

                    header_text = "Время явки за дату"
                    worksheet.write(0, 1, header_text)

                    dates = []
                    current_date = start_date
                    while current_date <= end_date:
                        dates.append(current_date)
                        current_date += timedelta(days=1)

                    for row, student in enumerate(students, start=2):
                        worksheet.write(row, 0, student.fullname)
                        worksheet.set_column(row, 0, len(student.fullname) * k)

                        for col, current_date in enumerate(dates, start=1):
                            time = student.arrival_time_for(current_date)
                            if time:
                                worksheet.write(row, col, time.strftime("%H:%M"))

                    if len(dates) == 1:
                        worksheet.set_column(0, 1, len(header_text) * k)
                    else:
                        worksheet.merge_range(0, 1, 0, col, header_text)

                    for col, current_date in enumerate(dates, start=1):
                        text = current_date.strftime("%d.%m.%Y")

                        worksheet.set_column(1, col, len(text) * k)
                        worksheet.write(1, col, text)

            return send_file(table_path, as_attachment=True, download_name=f"{school.name}.xlsx")

        else:
            data['message'] = "Начальная дата не должна превышать конечную."

    db_sess.close()
    return render_template("generate.html", **data)  # noqa
