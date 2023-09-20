from datetime import datetime, timedelta
from json import load

from flask import redirect, url_for, abort, render_template
from flask_login import login_required, current_user
from pytz import timezone

from app.modules.schools.school.classes.school_class.schedule import bp
from app.data.functions import allowed_permission, check_status
from app.data.models import User, Permission, School, Class
from app.data.db_session import create_session
from app import WEEKDAYS, CONFIG_PATH


@bp.route('/week', methods=['GET', 'POST'])
@login_required
def weekly_schedule(school_id, class_id):
    school_id, class_id = int(school_id), int(class_id)  # noqa

    if not current_user.is_registered:
        return redirect(url_for("auth.finish_register"))

    db_sess = create_session()
    school = db_sess.query(School).filter(School.id == school_id).first()  # noqa

    permission1 = db_sess.query(Permission).filter(Permission.title == "editing_self_class").first()  # noqa
    permission2 = db_sess.query(Permission).filter(Permission.title == "editing_classes").first()  # noqa
    permission3 = db_sess.query(Permission).filter(Permission.title == "editing_school").first()  # noqa

    if not ((allowed_permission(current_user, permission2) or (
            allowed_permission(current_user, permission1) and current_user.class_id == class_id)) and (
                    current_user.school_id == school_id or allowed_permission(current_user, permission3))):
        db_sess.close()
        abort(403)

    school = db_sess.query(School).filter(School.id == school_id).first()  # noqa
    school_class = db_sess.query(Class).filter(Class.id == class_id).first()  # noqa

    students = list(sorted([user for user in db_sess.query(User).filter(User.class_id == class_id).all() if  # noqa
                            check_status(user, "Ученик")], key=lambda st: st.fullname.split()[0]))

    today = datetime.now().astimezone(timezone("Europe/Moscow"))
    weekday = today.weekday()

    dates = []
    date = today - timedelta(days=weekday)
    for i in range(weekday + 1):
        if date.weekday() != 6:
            dates.append(date.date())
        date += timedelta(days=1)

    presence = {}
    total_presence = 0
    for w in WEEKDAYS:
        presence[w] = 0

    schedule = {}
    for student in students:
        schedule[student.fullname] = {}
        for wd in WEEKDAYS:
            schedule[student.fullname][wd] = None

        for w, dt in enumerate(dates):
            arrival_time = student.arrival_time_for(dt)
            if arrival_time:
                schedule[student.fullname][WEEKDAYS[w]] = arrival_time.strftime("%H:%M")
                presence[WEEKDAYS[w]] += 1
                total_presence += 1

    data = {
        "school": school,
        "students": students,
        "class": school_class,
        "wd": weekday,
        "weekdays": WEEKDAYS,
        "schedule": schedule,
        "presence": presence,
        "total_presence": total_presence
    }

    db_sess.close()
    return render_template("weekly_schedule.html", **data)


@bp.route('/')
@bp.route('/annual')
@bp.route('/annual/current')
@login_required
def current_annual_schedule(school_id, class_id):
    current_date = datetime.now().astimezone(timezone("Europe/Moscow")).strftime("%d.%m.%y")
    return redirect(url_for(".annual_schedule", school_id=school_id, class_id=class_id, date=current_date))


@bp.route('/annual/<date>', methods=['GET', 'POST'])
@login_required
def annual_schedule(school_id, class_id, date):
    school_id, class_id = int(school_id), int(class_id)  # noqa

    if not current_user.is_registered:
        return redirect(url_for("auth.finish_register"))

    db_sess = create_session()
    school = db_sess.query(School).filter(School.id == school_id).first()  # noqa

    permission1 = db_sess.query(Permission).filter(Permission.title == "editing_self_class").first()  # noqa
    permission2 = db_sess.query(Permission).filter(Permission.title == "editing_classes").first()  # noqa
    permission3 = db_sess.query(Permission).filter(Permission.title == "editing_school").first()  # noqa

    if not ((allowed_permission(current_user, permission2) or (
            allowed_permission(current_user, permission1) and current_user.class_id == class_id)) and (
                    current_user.school_id == school_id or allowed_permission(current_user, permission3))):
        db_sess.close()
        abort(403)

    school = db_sess.query(School).filter(School.id == school_id).first()  # noqa
    school_class = db_sess.query(Class).filter(Class.id == class_id).first()  # noqa

    students = list(sorted([user for user in db_sess.query(User).filter(User.class_id == class_id).all() if  # noqa
                            check_status(user, "Ученик")], key=lambda st: st.fullname.split()[0]))

    date = datetime.strptime(date, "%d.%m.%y").date()

    presence = 0
    schedule = {}
    for student in students:
        schedule[student.fullname] = {}
        schedule[student.fullname]["is_arrived"] = False

        arrival_time = student.arrival_time_for(date)
        if arrival_time:
            schedule[student.fullname]["is_arrived"] = True
            presence += 1
            schedule[student.fullname]["arrival_time"] = arrival_time.strftime("%H:%M")

    d1 = date
    d2 = date
    with open(CONFIG_PATH) as json:
        start_date = datetime.strptime(load(json)["clear_times"], "%Y-%m-%d %H:%M:%S.%f").date()
    today = datetime.now().date()
    pagination = [d1.strftime("%d.%m.%y")]
    n, m, f1, f2 = 1, 5, True, True
    while n < m:
        if f1 and d1 - timedelta(days=1) >= start_date:
            d1 -= timedelta(days=1)
            pagination.insert(0, d1.strftime("%d.%m.%y"))
            n += 1
        else:
            f1 = False
        if f2 and n < m and d2 + timedelta(days=1) <= today:
            d2 += timedelta(days=1)
            pagination.append(d2.strftime("%d.%m.%y"))
            n += 1
        else:
            f2 = False

        if not f1 and not f2:
            break

    data = {
        "school": school,
        "students": students,
        "class": school_class,
        "date": date,
        "schedule": schedule,
        "presence": presence,
        "pagination": pagination,
        "start_date": start_date,
        "today": today,
        "previous": date - timedelta(days=1),
        "next": date + timedelta(days=1),
    }

    db_sess.close()
    return render_template("annual_schedule.html", **data)
