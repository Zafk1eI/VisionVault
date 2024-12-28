from flask import (
    Blueprint,
    request,
    session,
    redirect,
    flash,
    url_for,
    render_template,
)
import re
from sqlalchemy.exc import IntegrityError
from models.models import User
from utils.db_init import db

auth_bp = Blueprint("auth", __name__)


def validate_password(password):
    if len(password) < 6:
        return False
    if not re.search(r"\d", password):
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False
    return True


def validate_email(email):
    email_regex = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
    return re.match(email_regex, email) is not None


@auth_bp.route("/register", methods=["POST", "GET"])
def register_user():
    try:
        if request.method == "POST":
            password = request.form.get("register_password")
            repeat_password = request.form.get("register_repeat_password")
            nickname = request.form.get("register_nickname")
            email = request.form.get("register_email")
            
            if password == repeat_password:
                
                if len(nickname) < 4:
                    flash("Длина имени пользователя должна быть более 4 символов.", "error")
                    return redirect(url_for('auth.register_user'))
                elif not validate_email(email):
                    flash("Неправильный формат email", "error")
                    return redirect(url_for('auth.register_user'))
                elif not validate_password(password):
                    flash("Пароль должен иметь длину не менее 6 символов, содержать цифру, заглавную букву и специальный символ.", "error")
                    return redirect(url_for('auth.register_user'))
                    
                new_user = User(username=nickname, email=email)
                new_user.set_password(password=password)

                db.session.add(new_user)
                db.session.commit()

                flash("Вы успешно зарегистрировались", category="success")
                return redirect(url_for("auth.login"))
            else:
                flash("Пароли не совпадают", category="error")
                return redirect(url_for('auth.register_user'))
    except IntegrityError:
        flash("Пользователь с такой почтой уже есть", category="error")
        return redirect(url_for('auth.register_user'))

    except Exception as e:
        flash(f"ERROR: {e}")
        return redirect(url_for('auth.register_user'))
        
    return render_template("registration.html")


@auth_bp.route("/login", methods=["POST", "GET"])
def login():

    is_auth = "user_id" in session

    if is_auth:
        flash("Вы уже вошли в систему.", category="info")
        return redirect(url_for("routers.index"))

    if request.method == "POST":
        email = request.form.get("login_email")
        password = request.form.get("login_password")

        print(f"Email received: {email}")
        print(f"Password received: {password}")

        if not email or not password:
            flash("Пожалуйста, заполните все поля.", "error")
            return redirect(url_for("auth.login"))

        exists_user = User.query.filter_by(email=email).first()

        if exists_user and exists_user.valid_password_hash(password):
            session["user_id"] = exists_user.user_id
            flash("Вы успешно вошли в аккаунт", category="success")
            return redirect(url_for("routers.index"))
        else:
            flash("Неверный логин или пароль.", category="error")
            return redirect(url_for("auth.login"))

    return render_template("login.html")


@auth_bp.post("/logout")
def logout():
    try:
        session.clear()
        return redirect(url_for("routers.index"))
    except Exception as e:
        print(e)
        return redirect(url_for("routers.login"))
