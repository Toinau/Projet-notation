from functools import wraps
from flask import session, redirect, url_for, flash
from .models import User

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Veuillez vous connecter pour accéder à cette page.', 'warning')
            return redirect(url_for('main.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Veuillez vous connecter pour accéder à cette page.', 'warning')
            return redirect(url_for('main.login'))
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin():
            flash('Accès interdit. Privilèges administrateur requis.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def coureur_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Veuillez vous connecter pour accéder à cette page.', 'warning')
            return redirect(url_for('main.login'))
        user = User.query.get(session['user_id'])
        if not user or not user.is_coureur():
            flash('Accès réservé aux coureurs.', 'warning')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function 