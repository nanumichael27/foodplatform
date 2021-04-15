import functools
from flask import (
    Blueprint,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for
)
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import login_user, logout_user, current_user
# from karma.db import get_db
from karma import db
from .models import User
import json

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        fullname = request.form['fullname']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        password2 = request.form['password2']
        error = None

        if not username:
            error = 'Username is required.'
        elif not fullname:
            error = 'Fullname required'
        elif not password:
            error = 'Password is required.'
        elif not email:
            error = 'Email is required.'
        elif not password == password2:
            error = 'Passwords don\'t match'
        elif not phone:
            error = 'Phone number is required.'
        elif db.session.query(
                User.query.filter_by(username=username).exists()
        ).scalar():
            error = 'User {} is already registered'.format(username)
        elif db.session.query(
                User.query.filter_by(email=email).exists()
        ).scalar():
            error = 'Email {} is already registered'.format(email)

        if error is None:
            user = User(username=username,
                        password=password,
                        fullname=fullname,
                        email=email,
                        phone=phone,
                        )
            db.session.add(user)
            db.session.commit()
            user.createCart()
            return redirect(url_for('auth.login'))

        flash(error)

    return render_template('auth/register.html')


@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        usernameoremail = request.form['usernameoremail']
        password = request.form['password']
        error = None
        user = User.query.filter_by(username=usernameoremail).first()
        if user is None:
            user = User.query.filter_by(email=usernameoremail).first()

        if user is None:
            error = 'Incorrect Username or Email'
        elif not user.check_password(password):
            error = 'Incorrect Password'

        if error is None:
            login_user(user)
            return redirect(url_for('index'))

        flash(error)

    return render_template('auth/login.html')


# @bp.before_app_request
# def load_logged_in_user():
#     user_id = session.get('user_id')
#     g.user = User.query.get(user_id) if user_id is not None else None


@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


# def login_required(view):
#     @functools.wraps(view)
#     def wrapped_view(**kwargs):
#         if g.user is None:
#             return redirect(url_for('auth.login'))

#         return view(**kwargs)

#     return wrapped_view


def admin_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if current_user.is_anonymous or not current_user.is_admin:
            return redirect(url_for('admin.login'))

        return view(**kwargs)

    return wrapped_view

def admin_guest(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if not current_user.is_anonymous:
            if current_user.is_admin:
                return redirect(url_for('admin.dashboard'))

        return view(**kwargs)

    return wrapped_view