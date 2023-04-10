from string import ascii_letters, digits, punctuation

from flask import Flask, render_template, redirect, url_for, abort, request
from flask_login import LoginManager, current_user, login_user, login_required, logout_user
from data.config import Config
from data.db_session import create_session, global_init
from data.forms import LoginForm, LoginKeyForm, FinishRegisterForm, ChangeFullnameForm, ChangeLoginForm, \
    ChangePasswordForm
from data.functions import all_permissions, allowed_permission
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
    if allowed_permission(current_user, permission):
        return redirect(url_for("admin_panel"))

    return render_template("home.html")


@app.route('/admin_panel', methods=['GET', 'POST'])
def admin_panel():
    db_sess = create_session()
    permission = db_sess.query(Permission).filter(Permission.title == "access_admin_panel").first()  # noqa
    if not allowed_permission(current_user, permission):
        return redirect(url_for("home"))

    schools = db_sess.query(School).all()

    data = {
        "schools": schools
    }

    if request.method == "POST":
        school_id = int(request.form.get("school_id"))
        return redirect(url_for("school_info", school_id=school_id))

    return render_template("admin_panel.html", **data)


@app.route('/school/<school_id>', methods=['GET', 'POST'])
def school_info(school_id):
    db_sess = create_session()

    school = db_sess.query(School).filter(School.id == school_id).first()

    data = {
        "school": school
    }

    return render_template("school_info.html", **data)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("profile"))

    form = LoginForm()
    data = {
        "form": form,
        "message": None
    }

    if form.validate_on_submit():
        db_sess = create_session()
        user = db_sess.query(User).filter(User.login == form.login.data.lower()).first()

        if user:
            if user.check_password(form.password.data):  # noqa
                login_user(user, remember=form.remember_me.data)
                return redirect(url_for("home"))

            data["message"] = "Неверный пароль"

        else:
            data["message"] = "Неверный логин"
    return render_template("login.html", **data)


@app.route('/login_key', methods=['GET', 'POST'])
def login_with_key():
    db_sess = create_session()
    if current_user.is_authenticated:
        return redirect(url_for("profile"))

    form = LoginKeyForm()
    data = {
        "form": form,
        "message": None
    }

    if form.validate_on_submit():
        user = db_sess.query(User).filter(User.key == form.key.data).first()

        if user is not None:
            login_user(user, remember=True)
            return redirect(url_for("home"))
        else:
            data["message"] = "Неверный ключ"
    return render_template("login_key.html", **data)


@app.route('/finish_register', methods=['GET', 'POST'])
@login_required
def finish_register():
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
            return redirect(url_for("home"))
    return render_template("finish_register.html", **data)


@app.route('/my')
@login_required
def profile():
    db_sess = create_session()
    statuses = list(sorted(db_sess.query(Status).filter(Status.id.in_(current_user.statuses.split(", "))).all(),  # noqa
                           key=lambda status: status.id, reverse=True))
    permissions = all_permissions(current_user)
    data = {
        "statuses": statuses,
        "permissions": permissions,
        "class_name": ""  # TODO: дописать
    }

    return render_template("profile.html", **data)


@app.route('/my/edit_fullname', methods=['GET', 'POST'])
@login_required
def change_fullname():
    db_sess = create_session()

    permission = db_sess.query(Permission).filter(Permission.title == "changing_fullname").first()  # noqa
    if not allowed_permission(current_user, permission):
        abort(404)

    form = ChangeFullnameForm()
    data = {
        'form': form,
        'message': None
    }

    if form.validate_on_submit():
        user = db_sess.query(User).filter(User.id == current_user.id).first()
        fullname = form.fullname.data

        if not all([symbol in RUSSIAN_ALPHABET + ' ' for symbol in fullname]):
            data['message'] = "Поле заполнено неверно. Используйте только буквы русского алфавита"
        else:
            user.fullname = ' '.join(list(map(lambda name: name.lower().capitalize(), fullname.split())))

            db_sess.commit()
            return redirect(url_for("profile"))

    return render_template('change_fullname.html', **data)


@app.route('/my/edit_login', methods=['GET', 'POST'])
@login_required
def change_login():
    db_sess = create_session()

    permission = db_sess.query(Permission).filter(Permission.title == "changing_login").first()  # noqa
    if not allowed_permission(current_user, permission):
        abort(404)

    form = ChangeLoginForm()
    data = {
        'form': form,
        'message': None
    }

    if form.validate_on_submit():
        user = db_sess.query(User).filter(User.id == current_user.id).first()
        user_login = form.login.data

        if not all([symbol in ascii_letters + digits for symbol in user_login]):
            data['message'] = "Логин содержит некорректные символы"
        else:
            user.login = user_login.lower()

            db_sess.commit()
            return redirect(url_for("profile"))

    return render_template('change_login.html', **data)


@app.route('/my/edit_password', methods=['GET', 'POST'])
@login_required
def change_password():
    db_sess = create_session()

    permission = db_sess.query(Permission).filter(Permission.title == "changing_password").first()  # noqa
    if not allowed_permission(current_user, permission):
        abort(404)

    form = ChangePasswordForm()
    data = {
        'form': form,
        'message': None
    }

    if form.validate_on_submit():
        user = db_sess.query(User).filter(User.id == current_user.id).first()
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
            return redirect(url_for("profile"))

    return render_template('change_password.html', **data)


if __name__ == '__main__':
    app.run(debug=True)
