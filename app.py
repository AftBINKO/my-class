from string import ascii_letters, digits, punctuation

from flask import Flask, render_template, redirect, url_for
from flask_login import LoginManager, current_user, login_user, login_required, logout_user
from data.config import Config
from data.db_session import create_session, global_init
from data.forms import LoginForm, LoginKeyForm, FinishRegisterForm
from data.models import User
from json import loads, dumps

app = Flask(__name__)
app.config.from_object(Config)

login_manager = LoginManager()
login_manager.init_app(app)

global_init("db/data.sqlite3")


@login_manager.user_loader
def load_user(user_id):
    db_sess = create_session()
    return db_sess.query(User).get(user_id)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route('/')
def home():
    if not current_user.is_authenticated:
        return redirect(url_for("login"))
    elif not bool(loads(current_user.data)):
        return redirect(url_for("finish_register"))
    return render_template("home.html")


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
    if current_user.is_authenticated:
        return redirect(url_for("profile"))

    form = LoginKeyForm()
    data = {
        "form": form,
        "message": None
    }

    if form.validate_on_submit():
        db_sess = create_session()
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
        user_data = loads(user.data)
        user_data['registered'] = True
        user_data = dumps(user_data, ensure_ascii=True)

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
            user.data = user_data
            user.key = None

            db_sess.commit()
            return redirect(url_for("home"))
    return render_template("finish_register.html", **data)


if __name__ == '__main__':
    app.run(debug=True)
