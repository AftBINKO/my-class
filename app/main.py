from flask_login import current_user, login_required
from flask import redirect, url_for, abort

from app import app, SERVICE_MODE

from .data.functions import check_permission, check_role
from .data.db_session import create_session
from .data.models import *


@app.before_request
def check_access():
    if SERVICE_MODE and current_user.is_authenticated and not check_role(current_user, "Администратор"):
        abort(503)


@app.route('/')
@login_required
def home():
    if not current_user.is_registered:
        abort(401)

    match current_user.home_page:
        case "control_panel":
            db_sess = create_session()
            permission = db_sess.query(Permission).filter_by(title="access_control_panel").first()
            db_sess.close()

            if check_permission(current_user, permission):
                return redirect(url_for("control_panel.schools_list"))

        case "my_school":
            if current_user.school_id:
                return redirect(url_for("schools.school.classes_list", school_id=current_user.school_id))

        case "my_class":
            if current_user.class_id:
                return redirect(url_for("schools.school.classes.school_class.class_info",
                                        school_id=current_user.school_id, class_id=current_user.class_id))

    return redirect(url_for("profile.profile"))
