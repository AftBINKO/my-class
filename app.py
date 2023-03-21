from flask import Flask, render_template, redirect, url_for
from flask_login import LoginManager, current_user
from data.config import Config
from data.forms import LoginForm

app = Flask(__name__)
app.config.from_object(Config)

# login_manager = LoginManager()
# login_manager.init_app(data)


@app.route('/')
def home():
    # if not current_user.is_authenticated:
    #     return redirect(url_for("login"))
    return render_template("home.html")


@app.route('/login')
def login():
    form = LoginForm()
    return render_template("login.html", form=form)


if __name__ == '__main__':
    app.run(debug=True)
