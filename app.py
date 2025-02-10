# app.py
import os
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Order, CustomerContact
from flask_migrate import Migrate
import config
import chardet


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI
app.config[
    'SQLALCHEMY_TRACK_MODIFICATIONS'] = config.SQLALCHEMY_TRACK_MODIFICATIONS
app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['UPLOAD_FOLDER'] = "uploads"

db.init_app(app)
migrate = Migrate(app, db)

ALLOWED_EXTENSIONS = {'csv', 'xlsx'}

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def detect_encoding(file_path):
    """Detekce kódování CSV souboru"""
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
    return result['encoding']

def vlozeni_kontaktu(shipment_numbers):
    """Simulace vkládání kontaktů (může se rozšířit)"""
    for shipment in shipment_numbers:
        contact = CustomerContact(
            customer=shipment,
            address="Dummy Address",
            phone_number="123456789",
            email="example@email.com"
        )
        db.session.add(contact)
    db.session.commit()


@app.route('/upload_orders', methods=['GET', 'POST'])
def upload_orders():
    """Nahrání a zpracování CSV souboru se zakázkami"""
    if request.method == 'POST':
        file = request.files['file']
        if not file:
            flash("Nebyl vybrán žádný soubor.", "danger")
            return redirect(url_for('upload_orders'))

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Detekce kódování
        encoding = detect_encoding(filepath)

        try:
            data = pd.read_csv(filepath, encoding=encoding, sep=';', engine='python', on_bad_lines='skip')
        except Exception as e:
            flash(f"Chyba při načítání souboru: {e}", "danger")
            return redirect(url_for('upload_orders'))

        # 📌 ROZHODOVÁNÍ O ZAŘAZENÍ ZAKÁZKY
        orders = []
        confirmation_orders = []  # Seznam zakázek k potvrzení

        for _, row in data.iterrows():
            try:
                order_number = str(row['Císlo zakázky ']).strip().replace('=',
                                                                          '').replace(
                    '"', '')
                note = row.get('Poznámka mandanta',
                               '')  # ✅ Získání poznámky mandanta

                print(f"Zpracováváme zakázku: {order_number}")

                created_date = None
                delivery_date = None

                if not pd.isna(row['Erfassungstermin']):
                    created_date = pd.to_datetime(row['Erfassungstermin'],
                                                  format='%d.%m.%Y',
                                                  dayfirst=True).strftime(
                        '%Y-%m-%d')

                if not pd.isna(row['Avizovaný termín']):
                    delivery_date = pd.to_datetime(row['Avizovaný termín'],
                                                   format='%d.%m.%Y',
                                                   dayfirst=True).strftime(
                        '%Y-%m-%d')

                order_data = {
                    'client': row['Mandant'],
                    'order_number': order_number,
                    'customer_name': row['Príjmení'],
                    'city': row['PSC'],
                    'created': created_date,
                    'delivery': delivery_date,
                    'note': note  # ✅ Přidáme poznámku mandanta
                }

                # ❓ Pokud zakázka končí `R` nebo `R"`, přidáme na seznam k potvrzení
                if order_number.endswith('R') or order_number.endswith('R"'):
                    print(
                        f"⚠ Zakázka {order_number} by měla jít k potvrzení s poznámkou: {note}")
                    confirmation_orders.append(order_data)

            except KeyError as e:
                print(f"❌ Chybějící sloupec: {e}")
            except Exception as e:
                print(f"❌ Chyba při zpracování řádku: {e}")

        # 📌 Uložíme zakázky k potvrzení do session
        if confirmation_orders:
            session['confirmation_orders'] = confirmation_orders
            return redirect(url_for('confirm_orders'))

        # 📌 Uložíme automatické zakázky
        if orders:
            try:
                db.session.add_all(orders)
                db.session.commit()
                flash(f"Do databáze bylo přidáno {len(orders)} zakázek.", "success")
            except Exception as e:
                db.session.rollback()
                flash(f"Chyba při ukládání do databáze: {e}", "danger")
            finally:
                db.session.close()

        return redirect(url_for('superuser'))  # ✅ Po nahrání přesměrujeme na superuser panel

    return render_template('upload_orders.html')


@app.route('/confirm_orders', methods=['GET', 'POST'])
def confirm_orders():
    confirmation_orders = session.get('confirmation_orders', [])

    print(f"Načítáme {len(confirmation_orders)} zakázek k potvrzení")  # DEBUG

    if request.method == 'POST':
        selected_orders = [order.strip().replace('=', '').replace('"', '') for order in request.form.getlist('selected_orders')]

        if selected_orders:
            orders_to_add = []
            for order in confirmation_orders:
                if order['order_number'] in selected_orders:
                    order['created'] = order['created'] if order['created'] else None  # ✅ Upravíme formát data
                    order['delivery'] = order['delivery'] if order['delivery'] else None
                    clean_order = {key: value for key, value in order.items()
                                   if key != 'note'}
                    orders_to_add.append(Order(**clean_order))

            if orders_to_add:
                try:
                    db.session.add_all(orders_to_add)
                    db.session.commit()
                    flash(f"Přidáno {len(orders_to_add)} zakázek.", "success")
                except Exception as e:
                    db.session.rollback()
                    flash(f"Chyba při ukládání do databáze: {e}", "danger")

        session.pop('confirmation_orders', None)
        return redirect(url_for('superuser'))  # ✅ Po potvrzení přesměrujeme na superuser panel

    return render_template('confirm_orders.html', orders=confirmation_orders)


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
    app.run()
