# app.py
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User
import config

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI
app.config[
    'SQLALCHEMY_TRACK_MODIFICATIONS'] = config.SQLALCHEMY_TRACK_MODIFICATIONS
app.config['SECRET_KEY'] = config.SECRET_KEY

db.init_app(app)


@app.before_first_request
def create_tables():
    # Při prvním requestu vytvoří tabulky (pokud neexistují)
    db.create_all()


# ---------------------------------------------------------
# Pomocné funkce
# ---------------------------------------------------------
def is_logged_in():
    """Zda je uživatel přihlášen jako běžný user."""
    return 'user_id' in session and session.get('is_superuser') == False


def is_superuser_logged_in():
    """Zda je přihlášen superuser."""
    return 'user_id' in session and session.get('is_superuser') == True


# ---------------------------------------------------------
# Hlavní routa (domovská/login)
# ---------------------------------------------------------
@app.route('/', methods=['GET', 'POST'])
def index():
    """
    - Pokud NENÍ nikdo přihlášen, zobrazí formulář pro login.
    - Pokud je přihlášen běžný user, zobrazí uvítání.
    - Pokud je přihlášen superuser, přesměruje ho na /superuser.
    """
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if user:
            if check_password_hash(user.password_hash, password):
                # Úspěšné heslo
                session['user_id'] = user.id
                session['username'] = user.username
                session['is_superuser'] = user.is_superuser
                if user.is_superuser:
                    return redirect(url_for('superuser'))
                else:
                    return redirect(url_for('dashboard'))
            else:
                return render_template('login.html', error="Nesprávné heslo!")
        else:
            return render_template('login.html', error="Uživatel neexistuje!")
    else:
        # GET: Je už někdo přihlášen?
        if is_logged_in():
            return redirect(url_for('dashboard'))
        elif is_superuser_logged_in():
            return redirect(url_for('superuser'))
        else:
            return render_template('login.html')


# ---------------------------------------------------------
# Dashboard pro běžného uživatele
# ---------------------------------------------------------
@app.route('/dashboard')
def dashboard():
    """
    Pokud je přihlášen běžný uživatel, zobrazíme uvítací obrazovku,
    s možností odhlášení.
    """
    if is_logged_in():
        username = session['username']
        return render_template('dashboard.html', username=username)
    else:
        return redirect(url_for('index'))


# ---------------------------------------------------------
# Superuser sekce
# ---------------------------------------------------------
@app.route('/superuser', methods=['GET', 'POST'])
def superuser():
    """
    Pokud je přihlášen superuser, ukáže seznam uživatelů a formulář
    pro přidání nového uživatele.
    """
    if not is_superuser_logged_in():
        return redirect(url_for('index'))

    users = User.query.all()

    if request.method == 'POST':
        # Při odeslání formuláře - přidat nového uživatele
        new_username = request.form.get('new_username')
        new_password = request.form.get('new_password')
        # Check existuje?
        if User.query.filter_by(username=new_username).first():
            return render_template('superuser.html',
                                   users=users,
                                   error="Uživatel už existuje!")
        # Vytvořit
        pw_hash = generate_password_hash(new_password)
        new_user = User(username=new_username, password_hash=pw_hash,
                        is_superuser=False)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('superuser'))
    else:
        return render_template('superuser.html', users=users)


@app.route('/delete_user/<int:user_id>')
def delete_user(user_id):
    """
    Smazání uživatele (jen superuser).
    """
    if not is_superuser_logged_in():
        return redirect(url_for('index'))

    user_to_delete = User.query.get(user_id)
    if user_to_delete:
        db.session.delete(user_to_delete)
        db.session.commit()
    return redirect(url_for('superuser'))


@app.route('/change_password/<int:user_id>', methods=['GET', 'POST'])
def change_password(user_id):
    """
    Změna hesla vybranému uživateli (jen superuser).
    """
    if not is_superuser_logged_in():
        return redirect(url_for('index'))

    user_to_update = User.query.get(user_id)
    if not user_to_update:
        return redirect(url_for('superuser'))

    if request.method == 'POST':
        new_password = request.form.get('new_password')
        user_to_update.password_hash = generate_password_hash(new_password)
        db.session.commit()
        return redirect(url_for('superuser'))
    else:
        return render_template('change_password.html', user=user_to_update)


# ---------------------------------------------------------
# Logout
# ---------------------------------------------------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


# ---------------------------------------------------------
# Inicializační superuser (pokud byste chtěli ručně)
# ---------------------------------------------------------
@app.cli.command("createsuperuser")
def create_superuser():
    """
    Volitelné: ručně spustitelné z terminálu:
    python -m flask createsuperuser
    """
    su_name = "DaliborZ"
    su_pass = "D@libor654X"
    if User.query.filter_by(username=su_name).first():
        print("Superuser už existuje.")
    else:
        pw_hash = generate_password_hash(su_pass)
        superuser = User(username=su_name, password_hash=pw_hash,
                         is_superuser=True)
        db.session.add(superuser)
        db.session.commit()
        print("Superuser vytvořen.")

@app.cli.command("initdb")
def init_db():
    """Vytvoří všechny tabulky v DB (db.create_all())."""
    db.create_all()
    print("Database tables created.")


if __name__ == '__main__':
    app.run(debug=True)
