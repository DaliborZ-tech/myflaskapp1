# models.py
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_superuser = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<User {self.username}>"

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    client = db.Column(db.String(255), nullable=False)
    order_number = db.Column(db.String(40), nullable=False)
    customer_name = db.Column(db.String(50), nullable=False)
    city = db.Column(db.String(30), nullable=False)
    created = db.Column(db.Date, nullable=False)
    delivery = db.Column(db.Date)
    first_contact = db.Column(db.Date)
    procesed_by = db.Column(db.Integer, db.ForeignKey('employees.id'))
    type_of_completion = db.Column(db.String(50))
    team_1 = db.Column(db.Integer, db.ForeignKey('teams.id'))
    team_2 = db.Column(db.Integer, db.ForeignKey('teams.id'))
    term_of_assembly = db.Column(db.Date)
    time_of_assembly = db.Column(db.String(20))
    status_of_assembly = db.Column(db.String(30))

class CustomerContact(db.Model):
    __tablename__ = 'contacts'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    customer = db.Column(db.Integer, db.ForeignKey('orders.id'))
    address = db.Column(db.String(50), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(50), nullable=False)

class Employee(db.Model):
    __tablename__ = 'employees'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    login = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='active')

class Team(db.Model):
    __tablename__ = 'teams'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    region = db.Column(db.String(50), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(50), nullable=False)
    website = db.Column(db.String(50))
    price_per_hour = db.Column(db.Integer)
    price_per_km = db.Column(db.Integer)
    working_region = db.Column(db.String(50))
    terms = db.Column(db.String(80))
    notes = db.Column(db.String(100))
    status = db.Column(db.String(50), nullable=False, default='active')

class Products(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'))
    products = db.Column(db.String(100), nullable=False)
    value = db.Column(db.Integer, nullable=False)
    value_of_assembly = db.Column(db.Integer)
    cost_of_assembly = db.Column(db.Integer)
