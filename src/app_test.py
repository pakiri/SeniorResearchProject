from flask import Flask, request, redirect, Response, flash, render_template, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import requests
import re

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///SRdata.db'
app.config['SECRET_KEY'] = 'your_secret_key'  # added to enable flashing messages

db = SQLAlchemy(app)
migrate = Migrate(app, db)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)

@app.route('/')
def index():
    return render_template('index_test.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm = request.form['confirm']
        hashedPassword = generate_password_hash(password, method='pbkdf2:sha256')

        if password != confirm:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
            flash('Username or email already exists!', 'danger')
            return redirect(url_for('register'))
        
        newUser = User(username=username, email=email, password=hashedPassword)
        db.session.add(newUser)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            session['GCuser_id'] = user.id
            session['GCusername'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
            # return redirect(url_for('dashboard'), username=username)
            # return render_template('dashboard.html', username=username)
        else:
            flash('Invalid username or password.', 'danger')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'GCuser_id' not in session:
        flash('You must log in first.', 'warning')
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/logout')
def logout():
    session.pop('GCuser_id', None)
    session.pop('GCusername', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

with app.app_context():
    db.create_all()

app.debug = True
app.run()
