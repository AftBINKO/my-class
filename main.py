from shutil import make_archive
from tempfile import TemporaryFile

import qrcode

from os import path, remove
from string import ascii_letters, punctuation

from datetime import datetime
from pytz import timezone

from flask import Flask, render_template, redirect, url_for, abort, jsonify, current_app, send_from_directory, request, \
    send_file
from flask_login import LoginManager, current_user, login_user, login_required, logout_user
from waitress import serve
from xlsxwriter import Workbook

from data.config import Config
from data.db_session import create_session, global_init
from data.forms import LoginForm, LoginKeyForm, FinishRegisterForm, ChangeFullnameForm, ChangeLoginForm, \
    ChangePasswordForm, EditSchoolForm, EditClassForm
from data.functions import all_permissions, allowed_permission, delete_login_data
from data.functions import delete_classes, delete_schools
from data.functions import delete_user as del_user
from data.models import *

app = Flask(__name__)
app.config.from_object(Config)

login_manager = LoginManager()
login_manager.init_app(app)

global_init("db/data.sqlite3")
RUSSIAN_ALPHABET = "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдеёжзийклмнопрстуфхцчшщъыьэюя"


@login_manager.user_loader
def load_user(user_id):
    db_sess = create_session()

    user = db_sess.query(User).get(user_id)
    permission = db_sess.query(Permission).filter(Permission.title == "login").first()  # noqa

    db_sess.close()

    if isinstance(user, User):
        if allowed_permission(user, permission):
            return user


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route('/')
@login_required
def home():
    if not current_user.is_registered:
        return redirect(url_for("finish_register"))

    db_sess = create_session()
    permission = db_sess.query(Permission).filter(Permission.title == "access_admin_panel").first()  # noqa
    status = max(list(map(int, current_user.statuses.split(", "))))
    db_sess.close()

    if allowed_permission(current_user, permission):
        return redirect(url_for("admin_panel"))

    if not current_user.school_id:
        abort(403)

    if status in [1, 3]:
        if current_user.class_id:
            return redirect(url_for("class_info", school_id=current_user.school_id, class_id=current_user.class_id))

    return redirect(url_for("school_info", school_id=current_user.school_id))


@app.route('/admin_panel/download_db', methods=['GET', 'POST'])
@login_required
def download_db():
    db_sess = create_session()
    permission = db_sess.query(Permission).filter(Permission.title == "access_admin_panel").first()  # noqa
    db_sess.close()

    if not allowed_permission(current_user, permission):
        abort(403)

    uploads = path.join(current_app.root_path, "db/")
    return send_from_directory(directory=uploads, path="data.sqlite3")


@app.route('/admin_panel/download_files', methods=['GET', 'POST'])
@login_required
def download_files():
    db_sess = create_session()
    permission = db_sess.query(Permission).filter(Permission.title == "access_admin_panel").first()  # noqa
    db_sess.close()

    if not allowed_permission(current_user, permission):
        abort(403)

    uploads = path.join(current_app.root_path, "static/files")
    tmp = path.join(current_app.root_path, "static/tmp")
    archive = path.join(tmp, "files")
    if path.exists(archive):
        remove(archive)
    make_archive(archive, 'zip', uploads)
    return send_from_directory(directory=tmp, path="files.zip")


@app.route('/admin_panel')
@login_required
def admin_panel():
    if not current_user.is_registered:
        return redirect(url_for("finish_register"))

    db_sess = create_session()

    permission = db_sess.query(Permission).filter(Permission.title == "access_admin_panel").first()  # noqa
    if not allowed_permission(current_user, permission):
        abort(403)

    schools = db_sess.query(School).all()

    db_sess.close()

    data = {
        "schools": schools
    }

    return render_template("admin_panel.html", **data)


@app.route('/login', methods=['GET', 'POST'])
@app.route('/enter_to_class/<class_id>/login', methods=['GET', 'POST'])
def login(class_id=None):
    if current_user.is_authenticated:
        if not current_user.is_registered:
            return redirect(url_for("finish_register"))
        return redirect(url_for("profile"))

    form = LoginForm()
    data = {
        "form": form,
        "message": None,
        "class_id": class_id
    }

    if form.validate_on_submit():
        db_sess = create_session()
        user = db_sess.query(User).filter(User.login == form.login.data.lower()).first()
        db_sess.close()

        if user:
            if user.check_password(form.password.data):  # noqa
                login_user(user, remember=form.remember_me.data)
                if class_id:
                    return redirect(url_for("enter_to_class", class_id=class_id))
                return redirect(url_for("home"))

            data["message"] = "Неверный пароль"

        else:
            data["message"] = "Неверный логин"
    return render_template("login.html", **data)


@app.route('/login_key', methods=['GET', 'POST'])
@app.route('/enter_to_class/<class_id>/login_key', methods=['GET', 'POST'])
def login_with_key(class_id=None):
    if current_user.is_authenticated:
        if not current_user.is_registered:
            return redirect(url_for("finish_register"))
        return redirect(url_for("profile"))

    form = LoginKeyForm()
    data = {
        "form": form,
        "message": None,
    }

    if form.validate_on_submit():
        db_sess = create_session()
        user = db_sess.query(User).filter(User.key == form.key.data).first()
        db_sess.close()

        if user is not None:
            login_user(user, remember=True)
            return redirect(url_for("finish_register", class_id=class_id))
        else:
            data["message"] = "Неверный ключ"
    return render_template("login_key.html", **data)


@app.route('/finish_register', methods=['GET', 'POST'])
@app.route('/enter_to_class/<class_id>/finish_register', methods=['GET', 'POST'])
@login_required
def finish_register(class_id=None):
    form = FinishRegisterForm()
    data = {
        "form": form,
        "message": None
    }

    if form.validate_on_submit():
        db_sess = create_session()
        user = db_sess.query(User).filter(User.id == current_user.id).first()

        user_login = form.login.data.lower()
        user_password = form.password.data
        user_password_again = form.password_again.data

        if not all([symbol in ascii_letters + digits for symbol in user_login]):
            data['message'] = "Логин содержит некорректные символы"
        elif not all(
                [symbol in ascii_letters + digits + punctuation for symbol in user_password]):
            data['message'] = "Пароль содержит некорректные символы."
        elif user_password != user_password_again:
            data['message'] = "Пароли не совпадают"
        else:
            user.login = user_login
            user.set_password(user_password)  # noqa
            user.is_registered = True
            user.delete_key()  # noqa

            db_sess.commit()
            db_sess.close()

            if class_id:
                return redirect(url_for("enter_to_class", class_id=class_id))

            return redirect(url_for("home"))
        db_sess.close()
    return render_template("finish_register.html", **data)


@app.route('/my')
@login_required
def profile():
    if not current_user.is_registered:
        return redirect(url_for("finish_register"))
    return redirect(url_for("profile_user", user_id=current_user.id))


@app.route('/profile/<user_id>')
@login_required
def profile_user(user_id):
    if not current_user.is_registered:
        return redirect(url_for("finish_register"))
    db_sess = create_session()
    user = db_sess.query(User).filter(User.id == user_id).first()
    statuses = list(sorted(db_sess.query(Status).filter(Status.id.in_(user.statuses.split(", "))).all(),  # noqa
                           key=lambda status: status.id, reverse=True))
    permissions = None
    permission3 = db_sess.query(Permission).filter(Permission.title == "access_admin_panel").first()  # noqa
    if current_user.id == int(user_id):
        permissions = set(map(lambda permission: permission.title, all_permissions(user)))
    else:
        if max(list(map(int, user.statuses.split(", ")))) == 1:
            permission1 = db_sess.query(Permission).filter(Permission.title == "editing_self_class").first()  # noqa
            permission2 = db_sess.query(Permission).filter(Permission.title == "editing_classes").first()  # noqa
            permission3 = db_sess.query(Permission).filter(Permission.title == "editing_school").first()  # noqa

            if not ((allowed_permission(current_user, permission2) or (
                    allowed_permission(current_user, permission1) and current_user.class_id == user.class_id)) and (
                            current_user.school_id == user.school_id or allowed_permission(current_user, permission3))):
                db_sess.close()
                abort(403)
        elif max(list(map(int, user.statuses.split(", ")))) in [2, 3, 4]:
            permission1 = db_sess.query(Permission).filter(Permission.title == "editing_self_school").first()  # noqa
            permission2 = db_sess.query(Permission).filter(Permission.title == "editing_school").first()  # noqa

            if not (allowed_permission(current_user, permission2) or (
                    allowed_permission(current_user, permission1) and current_user.school_id == user.school_id)):
                db_sess.close()
                abort(403)

    db_sess.close()

    data = {
        "statuses": statuses,
        "permissions": permissions,
        "user": user,
        "admin": allowed_permission(current_user, permission3),
        "class_name": ""  # TODO: дописать
    }

    return render_template("profile.html", **data)


@app.route('/profile/<user_id>/edit_fullname', methods=['GET', 'POST'])
@login_required
def change_fullname(user_id):
    if not current_user.is_registered:
        return redirect(url_for("finish_register"))

    db_sess = create_session()

    user = db_sess.query(User).filter(User.id == user_id).first()
    if current_user.id == int(user_id):
        permission = db_sess.query(Permission).filter(Permission.title == "changing_fullname").first()  # noqa
        if not allowed_permission(user, permission):
            db_sess.close()
            abort(405)
    else:
        permission1 = db_sess.query(Permission).filter(Permission.title == "editing_self_class").first()  # noqa
        permission2 = db_sess.query(Permission).filter(Permission.title == "editing_classes").first()  # noqa
        permission3 = db_sess.query(Permission).filter(Permission.title == "editing_school").first()  # noqa

        if not ((allowed_permission(current_user, permission2) or (
                allowed_permission(current_user, permission1) and current_user.class_id == user.class_id)) and (
                        current_user.school_id == user.school_id or allowed_permission(current_user, permission3))):
            db_sess.close()
            abort(403)

    form = ChangeFullnameForm()
    data = {
        'form': form,
        'message': None
    }

    if form.validate_on_submit():
        fullname = form.fullname.data

        if not all([symbol in RUSSIAN_ALPHABET + ' ' for symbol in fullname]):
            data['message'] = "Поле заполнено неверно. Используйте только буквы русского алфавита"
        else:
            user.fullname = ' '.join(list(map(lambda name: name.lower().capitalize(), fullname.split())))

            db_sess.commit()
            db_sess.close()
            return redirect(url_for("profile_user", user_id=user_id))
    db_sess.close()
    return render_template('change_fullname.html', **data)


@app.route('/profile/<user_id>/edit_login', methods=['GET', 'POST'])
@login_required
def change_login(user_id):
    if not current_user.is_registered:
        return redirect(url_for("finish_register"))

    db_sess = create_session()

    user = db_sess.query(User).filter(User.id == user_id).first()
    if current_user.id == int(user_id):
        permission = db_sess.query(Permission).filter(Permission.title == "changing_login").first()  # noqa
    else:
        permission = db_sess.query(Permission).filter(Permission.title == "editing_user").first()  # noqa
    if not allowed_permission(current_user, permission):
        db_sess.close()
        abort(403)

    form = ChangeLoginForm()
    data = {
        'form': form,
        'message': None
    }

    if form.validate_on_submit():
        user_login = form.login.data

        if not all([symbol in ascii_letters + digits for symbol in user_login]):
            data['message'] = "Логин содержит некорректные символы"
        else:
            user.login = user_login.lower()

            db_sess.commit()
            db_sess.close()
            return redirect(url_for("profile_user", user_id=user_id))

    db_sess.close()

    return render_template('change_login.html', **data)


@app.route('/profile/<user_id>/edit_password', methods=['GET', 'POST'])
@login_required
def change_password(user_id):
    if not current_user.is_registered:
        return redirect(url_for("finish_register"))

    db_sess = create_session()

    user = db_sess.query(User).filter(User.id == user_id).first()
    if current_user.id == int(user_id):
        permission = db_sess.query(Permission).filter(Permission.title == "changing_password").first()  # noqa
    else:
        permission = db_sess.query(Permission).filter(Permission.title == "editing_user").first()  # noqa
    if not allowed_permission(current_user, permission):
        db_sess.close()
        abort(403)

    form = ChangePasswordForm()
    data = {
        'form': form,
        'message': None
    }

    if form.validate_on_submit():
        old_password = form.old_password.data
        new_password = form.new_password.data
        new_password_again = form.new_password_again.data

        if not all([symbol in ascii_letters + digits + punctuation for symbol in
                    form.new_password.data]):
            data['message'] = "Пароль содержит некорректные символы"
        elif new_password != new_password_again:
            data['message'] = "Пароли не совпадают"
        elif not user.check_password(old_password):  # noqa
            data['message'] = "Неверный пароль"
        elif form.old_password.data == form.new_password.data:
            data['message'] = "Новый пароль совпадает со старым"
        else:
            user.set_password(new_password)  # noqa

            db_sess.commit()
            db_sess.close()
            return redirect(url_for("profile_user", user_id=user_id))

    db_sess.close()

    return render_template('change_password.html', **data)


@app.route('/profile/<user_id>/delete_login', methods=['GET', 'POST'])
@login_required
def delete_login(user_id):
    if not current_user.is_registered:
        return redirect(url_for("finish_register"))

    if delete_login_data(int(user_id), current_user) == 403:
        abort(403)

    return redirect(url_for("profile_user", user_id=user_id))


@app.route('/profile/<user_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_registered:
        return redirect(url_for("finish_register"))

    if del_user(int(user_id), current_user) == 403:
        abort(403)

    return redirect(url_for("home"))


@app.route('/schools/add', methods=['GET', 'POST'])
@login_required
def add_school():
    if not current_user.is_registered:
        return redirect(url_for("finish_register"))

    db_sess = create_session()

    permission = db_sess.query(Permission).filter(Permission.title == "adding_school").first()  # noqa
    if not allowed_permission(current_user, permission):
        db_sess.close()
        abort(403)

    form = EditSchoolForm()
    data = {
        'form': form
    }

    if form.validate_on_submit():
        school = School()

        school.name = form.school.data
        school.fullname = form.fullname.data

        db_sess.add(school)
        db_sess.commit()

        school_id = school.id

        db_sess.close()

        return redirect(url_for("school_info", school_id=school_id))

    db_sess.close()

    return render_template('add_school.html', **data)


@app.route('/schools/school/<school_id>')
@login_required
def school_info(school_id):
    school_id = int(school_id)

    if not current_user.is_registered:
        return redirect(url_for("finish_register"))

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

    return render_template("school_info.html", **data)


@app.route('/schools/school/<school_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_school(school_id):
    school_id = int(school_id)

    if not current_user.is_registered:
        return redirect(url_for("finish_register"))

    db_sess = create_session()

    permission1 = db_sess.query(Permission).filter(Permission.title == "editing_self_school").first()  # noqa
    permission2 = db_sess.query(Permission).filter(Permission.title == "editing_school").first()  # noqa

    if not (allowed_permission(current_user, permission2) or (
            allowed_permission(current_user, permission1) and current_user.school_id == school_id)):
        db_sess.close()
        abort(403)

    form = EditSchoolForm()
    school = db_sess.query(School).filter(School.id == school_id).first()  # noqa
    data = {
        'form': form,
        'school': school
    }

    if form.validate_on_submit():
        school.name = form.school.data
        school.fullname = form.fullname.data

        db_sess.commit()
        db_sess.close()

        return redirect(url_for("school_info", school_id=school.id))

    db_sess.close()

    return render_template('edit_school.html', **data)


@app.route('/schools/school/<school_id>/moderators/add', methods=['GET', 'POST'])
@login_required
def add_moderator(school_id):
    school_id = int(school_id)  # noqa

    if not current_user.is_registered:
        return redirect(url_for("finish_register"))

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
        'form': form,
        'school': school,
        'message': None
    }

    if form.validate_on_submit():
        moder = User()

        if not all([symbol in RUSSIAN_ALPHABET + ' ' for symbol in form.fullname.data]):
            data['message'] = "Поле заполнено неверно. Используйте только буквы русского алфавита"
        else:
            moder.fullname = ' '.join(list(map(lambda name: name.lower().capitalize(), form.fullname.data.split())))
            moder.school_id = school_id
            moder.statuses = 4
            moder.generate_key()

            db_sess.add(moder)
            db_sess.commit()
            db_sess.close()

            return redirect(url_for("school_info", school_id=school_id))

    db_sess.close()

    return render_template('add_moderator.html', **data)


@app.route('/schools/school/<school_id>/teachers/add', methods=['GET', 'POST'])
@login_required
def add_teacher(school_id):
    school_id = int(school_id)  # noqa

    if not current_user.is_registered:
        return redirect(url_for("finish_register"))

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

            return redirect(url_for("school_info", school_id=school_id))

    db_sess.close()

    return render_template('add_teacher.html', **data)


@app.route('/schools/school/<school_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_school(school_id):
    if not current_user.is_registered:
        return redirect(url_for("finish_register"))

    if delete_schools(int(school_id), current_user) == 405:
        abort(403)

    return redirect(url_for("home"))


@app.route('/schools/school/<school_id>/classes/add', methods=['GET', 'POST'])
@login_required
def add_class(school_id):
    school_id = int(school_id)

    if not current_user.is_registered:
        return redirect(url_for("finish_register"))

    db_sess = create_session()

    school = db_sess.query(School).filter(School.id == school_id).first()  # noqa

    permission1 = db_sess.query(Permission).filter(Permission.title == "adding_classes").first()  # noqa
    permission2 = db_sess.query(Permission).filter(Permission.title == "editing_school").first()  # noqa

    if not (allowed_permission(current_user, permission1) and (
            current_user.school_id == school_id or allowed_permission(current_user, permission2))):
        db_sess.close()
        abort(403)

    form = EditClassForm()
    data = {
        'form': form,
        'school': school
    }

    if form.validate_on_submit():
        school_class = Class()

        school_class.class_number = form.class_number.data
        if form.letter.data:
            school_class.letter = form.letter.data
        school_class.school_id = school_id

        db_sess.add(school_class)
        db_sess.commit()

        class_id = school_class.id

        db_sess.close()

        return redirect(url_for("class_info", school_id=school_id, class_id=class_id))

    db_sess.close()

    return render_template('add_class.html', **data)


@app.route('/schools/school/<school_id>/classes/class/<class_id>', methods=['GET', 'POST'])
@login_required
def class_info(school_id, class_id):
    school_id, class_id = int(school_id), int(class_id)

    if not current_user.is_registered:
        return redirect(url_for("finish_register"))

    db_sess = create_session()
    permissions = set(map(lambda permission: permission.title, all_permissions(current_user)))
    school = db_sess.query(School).filter(School.id == school_id).first()  # noqa

    permission1 = db_sess.query(Permission).filter(Permission.title == "view_self_details_class").first()  # noqa
    permission2 = db_sess.query(Permission).filter(Permission.title == "view_details_classes").first()  # noqa
    permission3 = db_sess.query(Permission).filter(Permission.title == "view_schools").first()  # noqa

    if not ((allowed_permission(current_user, permission2) or (
            allowed_permission(current_user, permission1) and current_user.class_id == class_id)) and (
                    current_user.school_id == school_id or allowed_permission(current_user, permission3))):
        db_sess.close()
        abort(403)

    school = db_sess.query(School).filter(School.id == school_id).first()  # noqa
    school_class = db_sess.query(Class).filter(Class.id == class_id).first()  # noqa

    students = []
    class_teacher = None

    for user in db_sess.query(User).filter(User.class_id == class_id).all():  # noqa
        if db_sess.query(Status).filter(Status.title == "Ученик").first().id in set(  # noqa
                map(int, user.statuses.split(", "))):
            students.append(user)
        elif db_sess.query(Status).filter(Status.title == "Классный руководитель").first().id in set(  # noqa
                map(int, user.statuses.split(", "))):
            class_teacher = user

    students.sort(key=lambda st: st.fullname.split()[0])

    if request.method == "POST":
        for student in students:
            student.is_arrived = False
            student.arrival_time = None
        db_sess.commit()
        db_sess.close()

        return redirect(url_for("class_info", school_id=school_id, class_id=class_id))

    data = {
        "school": school,
        "permissions": permissions,
        "students": students,
        "class_teacher": class_teacher,
        "class": school_class,
    }

    db_sess.close()
    return render_template("class_info.html", **data)


@app.route('/schools/school/<school_id>/classes/class/<class_id>/download_excel', methods=['GET', 'POST'])
@login_required
def download_excel(school_id, class_id):
    school_id, class_id = int(school_id), int(class_id)  # noqa

    db_sess = create_session()

    school_class = db_sess.query(Class).filter(Class.id == class_id).first()  # noqa

    permission1 = db_sess.query(Permission).filter(Permission.title == "view_self_details_class").first()  # noqa
    permission2 = db_sess.query(Permission).filter(Permission.title == "view_details_classes").first()  # noqa
    permission3 = db_sess.query(Permission).filter(Permission.title == "view_schools").first()  # noqa

    if not ((allowed_permission(current_user, permission2) or (
            allowed_permission(current_user, permission1) and current_user.class_id == class_id)) and (
                    current_user.school_id == school_id or allowed_permission(current_user, permission3))):
        db_sess.close()
        abort(403)

    tmp_path = "static/tmp/table.xlsx"
    students = [user for user in db_sess.query(User).filter(User.class_id == 1).all() if  # noqa
                db_sess.query(Status).filter(Status.title == "Ученик").first().id in set(  # noqa
                    map(int, user.statuses.split(", ")))]

    with Workbook(tmp_path) as workbook:
        worksheet = workbook.add_worksheet()

        header_row_format = workbook.add_format({'bold': True})
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


@app.route('/enter_to_class/<class_id>', methods=['GET', 'POST'])
def enter_to_class(class_id):
    if not current_user.is_authenticated:
        return redirect(url_for("login", class_id=class_id))

    class_id = int(class_id)

    db_sess = create_session()

    if not (current_user.class_id == class_id and db_sess.query(Status).filter(
            Status.title == "Ученик").first().id in set(map(int, current_user.statuses.split(", ")))):  # noqa
        db_sess.close()
        abort(403)

    user = db_sess.query(User).filter(User.id == current_user.id).first()
    user.is_arrived = True
    user.arrival_time = datetime.now().astimezone(timezone("Europe/Moscow"))

    db_sess.commit()
    db_sess.close()

    return redirect(url_for("enter_success"))


@app.route('/enter_to_class/success')
def enter_success():
    return render_template("alert.html", title="Успешный вход",
                           message="Можете заходить в класс, вы отмечены, как присутствующий"), {
        "Refresh": f"3; url={url_for('home')}"}


@app.route('/schools/school/<school_id>/classes/class/<class_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_class(school_id, class_id):
    school_id, class_id = int(school_id), int(class_id)  # noqa

    db_sess = create_session()

    if not current_user.is_registered:
        return redirect(url_for("finish_register"))

    permission1 = db_sess.query(Permission).filter(Permission.title == "editing_self_class").first()  # noqa
    permission2 = db_sess.query(Permission).filter(Permission.title == "editing_classes").first()  # noqa
    permission3 = db_sess.query(Permission).filter(Permission.title == "editing_school").first()  # noqa

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
        'class': school_class
    }

    if form.validate_on_submit():
        school_class.class_number = form.class_number.data
        school_class.letter = form.letter.data

        db_sess.commit()
        db_sess.close()

        return redirect(url_for("class_info", school_id=school_id, class_id=class_id))

    db_sess.close()

    return render_template('edit_class.html', **data)


@app.route('/schools/school/<school_id>/classes/class/<class_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_class(school_id, class_id):
    if not current_user.is_registered:
        return redirect(url_for("finish_register"))

    if delete_classes(int(school_id), int(class_id), current_user) == 405:
        abort(403)

    return redirect(url_for("school_info", school_id=school_id))


@app.route('/schools/school/<school_id>/classes/class/<class_id>/students/add', methods=['GET', 'POST'])
@login_required
def add_student(school_id, class_id):
    school_id, class_id = int(school_id), int(class_id)  # noqa

    if not current_user.is_registered:
        return redirect(url_for("finish_register"))

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

    form = ChangeFullnameForm()
    data = {
        'form': form,
        'school': school,
        'class': school_class,
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

            return redirect(url_for("class_info", school_id=school_id, class_id=class_id))

    db_sess.close()

    return render_template('add_student.html', **data)


@app.route('/schools/school/<school_id>/classes/class/<class_id>/class_teacher/add', methods=['GET', 'POST'])
@login_required
def add_class_teacher(school_id, class_id):
    school_id, class_id = int(school_id), int(class_id)  # noqa

    if not current_user.is_registered:
        return redirect(url_for("finish_register"))

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

    form = ChangeFullnameForm()
    data = {
        'form': form,
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

            return redirect(url_for("class_info", school_id=school_id, class_id=class_id))

    db_sess.close()

    return render_template('add_class_teacher.html', **data)


@app.route('/schools/school/<school_id>/classes/class/<class_id>/get_qr', methods=['GET', 'POST'])
@login_required
def generate_qrcode(school_id, class_id):
    school_id, class_id = int(school_id), int(class_id)  # noqa

    if not current_user.is_registered:
        return redirect(url_for("finish_register"))

    db_sess = create_session()

    permission1 = db_sess.query(Permission).filter(Permission.title == "editing_self_class").first()  # noqa
    permission2 = db_sess.query(Permission).filter(Permission.title == "editing_classes").first()  # noqa
    permission3 = db_sess.query(Permission).filter(Permission.title == "editing_school").first()  # noqa

    if not ((allowed_permission(current_user, permission2) or (
            allowed_permission(current_user, permission1) and current_user.class_id == class_id)) and (
                    current_user.school_id == school_id or allowed_permission(current_user, permission3))):
        db_sess.close()
        abort(405)

    uploads = path.join(current_app.root_path, path.join(app.config["UPLOAD_FOLDER"], path.join("qrcodes", "classes")))

    name = f"class_{class_id}.png"
    qr = qrcode.make(url_for("enter_to_class", class_id=class_id, _external=True))
    qr.save(path.join(uploads, name))

    school_class = db_sess.query(Class).filter(Class.id == class_id).first()  # noqa
    school_class.qr = name
    db_sess.commit()

    db_sess.close()

    return redirect(url_for("class_info", school_id=school_id, class_id=class_id))


@app.route('/schools/school/<school_id>/classes/class/<class_id>/qr', methods=['GET', 'POST'])
@login_required
def view_qrcode(school_id, class_id):
    school_id, class_id = int(school_id), int(class_id)  # noqa

    if not current_user.is_registered:
        return redirect(url_for("finish_register"))

    uploads = path.join(current_app.root_path, path.join(app.config["UPLOAD_FOLDER"], path.join("qrcodes", "classes")))

    db_sess = create_session()
    qr = db_sess.query(Class).filter(Class.id == class_id).first().qr  # noqa
    db_sess.close()
    if qr is None:
        abort(404)

    return send_from_directory(directory=uploads, path=qr)


@app.errorhandler(401)
def unauthorized(error):
    return redirect(url_for('login'))


@app.errorhandler(403)
def forbidden(error):
    return render_template("alert.html", title="Недостаточно прав",
                           message="Вам сюда нельзя"), {"Refresh": f"3; url={url_for('home')}"}


@app.errorhandler(404)
def not_found(error):
    return render_template("alert.html", title="Страницы не существует",
                           message="Вы перешли на несуществующую страницу"), {
        "Refresh": f"3; url={url_for('home')}"}


@app.errorhandler(500)
def crash(error):
    return render_template("alert.html", title="Ошибка сервера",
                           message="На сервере произошла ошибка"), {
        "Refresh": f"3; url={url_for('home')}"}


if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=5000)
