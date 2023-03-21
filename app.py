from flask import Flask, render_template, redirect, url_for
from flask_login import LoginManager, current_user, login_user, login_required
from data.config import Config
from data.db_session import create_session, global_init
from data.forms import LoginForm, LoginKeyForm
from data.models import User

app = Flask(__name__)
app.config.from_object(Config)

login_manager = LoginManager()
login_manager.init_app(app)

global_init("db/data.sqlite3")


@login_manager.user_loader
def load_user(user_id):
    db_sess = create_session()
    return db_sess.query(User).get(user_id)


@app.route('/')
def home():
    if not current_user.is_authenticated:
        return redirect(url_for("login"))
    return render_template("home.html")


@app.route('/login')
def login():
    if current_user.is_authenticated:
        return redirect(url_for("profile"))

    form = LoginForm()
    return render_template("login.html", form=form)


@app.route('/login_key')
def login_with_key():
    if current_user.is_authenticated:
        return redirect(url_for("profile"))

    form = LoginKeyForm()

    if form.validate_on_submit():
        db_sess = create_session()
        user = db_sess.query(User).filter(User.key == form.key.data).first()

        if user is not None:
            login_user(user, remember=True)
            return redirect("")
    return render_template("login_key.html", form=form)  # TODO: Дописать сообщения об ошибках


@app.route('/finish_register')
@login_required
def finish_register():
    pass


if __name__ == '__main__':
    app.run(debug=True)
