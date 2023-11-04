import calendar

from datetime import datetime, timedelta
from json import load

from flask_login import login_required, current_user
from flask import abort, render_template
from pytz import timezone

from app.modules.schools.school.classes.school_class.schedule import bp
from app.data.functions import check_permission, check_role
from app.data.models import User, Permission, School, Class
from app.data.db_session import create_session
from app import WEEKDAYS, CONFIG_PATH


@bp.url_value_preprocessor
def check_permissions(endpoint, values):
    school_id = values['school_id']
    class_id = values['class_id']

    db_sess = create_session()

    permission1 = db_sess.query(Permission).filter_by(title="view_self_arrival_times").first()
    permission2 = db_sess.query(Permission).filter_by(title="editing_classes").first()  # noqa
    permission3 = db_sess.query(Permission).filter_by(title="editing_school").first()

    if not ((check_permission(current_user, permission2) or (
            check_permission(current_user, permission1) and current_user.class_id == class_id)) and (
                    current_user.school_id == school_id or check_permission(current_user, permission3))):
        db_sess.close()
        abort(403)


@bp.route('/week')
@bp.route('/week/current')
@bp.route('/week/<int:week>')
@login_required
def weekly_schedule(school_id, class_id, week=None):
    with open(CONFIG_PATH) as json:
        start_date = datetime.strptime(load(json)["clear_times"], "%Y-%m-%d %H:%M:%S.%f").date()
        monday_start_date = start_date - timedelta(days=start_date.weekday())

    today = datetime.now().astimezone(timezone("Europe/Moscow")).date()
    now_monday = today - timedelta(days=today.weekday())
    now_saturday = now_monday + timedelta(days=5)

    today_week = int((now_monday - monday_start_date).days / 7)

    if week is None:
        week = today_week
    else:
        week -= 1

    monday = monday_start_date + timedelta(days=7 * week)
    saturday = monday + timedelta(days=5)

    if not (saturday <= now_saturday and monday >= monday_start_date):
        abort(404)

    db_sess = create_session()  # noqa

    school = db_sess.query(School).get(school_id)
    school_class = db_sess.query(Class).get(class_id)

    students = list(sorted([user for user in db_sess.query(User).filter_by(class_id=class_id).all() if
                            check_role(user, "Ученик")], key=lambda st: st.fullname.split()[0]))

    dates = []
    date = monday
    for i in range(6):
        dates.append(date)
        date += timedelta(days=1)

    weekdays = [(w, dates[i]) for i, w in enumerate(WEEKDAYS)]

    presence = {}
    total_presence = 0
    for w in WEEKDAYS:
        presence[w] = 0

    schedule = {}
    for student in students:
        student: User
        schedule[student.fullname] = {}
        for wd in WEEKDAYS:
            schedule[student.fullname][wd] = None

        for w, dt in enumerate(dates):
            arrival_time = student.arrival_time_for(dt)
            if arrival_time:
                schedule[student.fullname][WEEKDAYS[w]] = arrival_time.strftime("%H:%M")
                presence[WEEKDAYS[w]] += 1
                total_presence += 1

    permission = db_sess.query(Permission).filter_by(title="editing_self_class").first()
    generate_table = check_permission(current_user, permission)

    data = {
        "school": school,
        "students": students,
        "monday": monday,
        "saturday": saturday,
        "class": school_class,
        "weekdays": weekdays,
        "schedule": schedule,
        "presence": presence,
        "today": today,
        "today_week": today_week,
        "generate_table": generate_table,
        "week": week,
        "total_presence": total_presence
    }

    db_sess.close()
    return render_template("weekly_schedule.html", **data)  # noqa


@bp.route('/')
@bp.route('/annual')
@bp.route('/annual/current')
@bp.route('/annual/<date>')
@login_required
def annual_schedule(school_id, class_id, date=None):
    with open(CONFIG_PATH) as json:
        start_date = datetime.strptime(load(json)["clear_times"], "%Y-%m-%d %H:%M:%S.%f").date()
    today = datetime.now().astimezone(timezone("Europe/Moscow")).date()

    if date is None:
        date = today
    else:
        date = datetime.strptime(date, "%d.%m.%y").date()

    if not (start_date <= date <= today):
        abort(404)

    db_sess = create_session()  # noqa

    school = db_sess.query(School).get(school_id)
    school_class = db_sess.query(Class).get(class_id)

    students = list(sorted([user for user in db_sess.query(User).filter_by(class_id=class_id).all() if
                            check_role(user, "Ученик")], key=lambda st: st.fullname.split()[0]))

    presence = 0
    schedule = {}
    for student in students:
        student: User
        schedule[student.fullname] = {}
        schedule[student.fullname]["is_arrived"] = False

        arrival_time = student.arrival_time_for(date)
        if arrival_time:
            schedule[student.fullname]["is_arrived"] = True
            presence += 1
            schedule[student.fullname]["arrival_time"] = arrival_time.strftime("%H:%M")

    d1 = date
    d2 = date

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

    permission = db_sess.query(Permission).filter_by(title="editing_self_class").first()
    generate_table = check_permission(current_user, permission)

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
        "generate_table": generate_table,
        "previous": date - timedelta(days=1),
        "next": date + timedelta(days=1),
    }

    db_sess.close()
    return render_template("annual_schedule.html", **data)  # noqa


@bp.route('/month')
@bp.route('/month/current')
@bp.route('/month/<month>')
def monthly_schedule(school_id, class_id, month=None):
    with open(CONFIG_PATH) as json:
        start_date = datetime.strptime(load(json)["clear_times"], "%Y-%m-%d %H:%M:%S.%f").date()
    today = datetime.now().astimezone(timezone("Europe/Moscow")).date()

    if month is None:
        date = today
    else:
        date = datetime.strptime(month, "%m.%y").date()

    start_month = datetime(date.year, date.month, 1).date()
    end_month = datetime(date.year, date.month, calendar.monthrange(date.year, date.month)[-1]).date()

    if not (today >= start_month and start_date <= end_month):
        abort(404)

    db_sess = create_session()

    students = list(sorted([user for user in db_sess.query(User).filter_by(class_id=class_id).all() if
                            check_role(user, "Ученик")], key=lambda st: st.fullname.split()[0]))

    list_calendar = calendar.month(date.year, date.month).split('\n')[2:-1]
    cal = []
    for i, c in enumerate(list_calendar):
        c = c.split()

        if i == 0:
            for j in range(len(c), 7):
                c.insert(0, " ")
        elif i == len(list_calendar) - 1:
            for j in range(len(c), 7):
                c.append(" ")

        c = c[:-1]

        ap = False
        for j, num in enumerate(c):
            if num.isdigit():
                ap = True
                day = int(num)
                d = datetime(date.year, date.month, int(num)).strftime("%d.%m.%y")
                presence = 0

                if start_date <= datetime.strptime(d, "%d.%m.%y").date() <= today:
                    for student in students:
                        arrival_time = student.arrival_time_for(datetime.strptime(d, "%d.%m.%y").date())  # noqa
                        if arrival_time:
                            presence += 1
                else:
                    d = None

                c[j] = {
                    'day': day,
                    'date': d,
                    'presence': presence
                }

        if ap:  # на случай, если первый день месяца — воскресение
            cal.append(c)

    d1 = start_month
    d2 = end_month

    pagination = [d1.strftime("%m.%y")]
    n, m, f1, f2 = 1, 5, True, True
    while n < m:
        d1 = d1 - timedelta(days=1)
        d1 = datetime(d1.year, d1.month, 1).date()
        d11 = d1
        d12 = datetime(d1.year, d1.month, calendar.monthrange(d1.year, d1.month)[-1]).date()
        if f1 and today >= d11 and start_date <= d12:
            pagination.insert(0, d1.strftime("%m.%y"))
            n += 1
        else:
            f1 = False

        d2 = d2 + timedelta(days=1)
        d2 = datetime(d2.year, d2.month, calendar.monthrange(d2.year, d2.month)[-1]).date()
        d21 = datetime(d2.year, d2.month, 1).date()
        d22 = d2
        if f2 and today >= d21 and start_date <= d22:
            pagination.append(d2.strftime("%m.%y"))
            n += 1
        else:
            f2 = False

        if not f1 and not f2:
            break

    school = db_sess.query(School).get(school_id)
    school_class = db_sess.query(Class).get(class_id)

    permission = db_sess.query(Permission).filter_by(title="editing_self_class").first()
    generate_table = check_permission(current_user, permission)

    data = {
        'date': date,
        'class': school_class,
        'start_month': start_month,
        'end_month': end_month,
        'school': school,
        'class_id': class_id,
        'school_id': school_id,
        'calendar': cal,
        'pagination': pagination,
        "start_date": start_date,
        "today": today,
        "generate_table": generate_table,
        "previous": start_month - timedelta(days=1),
        "next": end_month + timedelta(days=1)
    }

    return render_template('monthly_schedule.html', **data)  # noqa
