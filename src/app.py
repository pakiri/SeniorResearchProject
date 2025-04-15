from flask import Flask, request, redirect, Response, flash, render_template, url_for, session
from flask.templating import render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_migrate import Migrate, migrate
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import requests
import re

USER_ZIPCODE = "22312"

categories = [r"\bapples?\b(?!\s*sauce)",
              r"grape(?!fruit)",
              r"onion(?! ring)",
              r"oranges",
              r"tomato(?! )"]

app = Flask(__name__) # creates a new Flask app

# link the database to the Flask app's config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///SRdata.db'
app.config['SECRET_KEY'] = 'your_secret_key'  # added to enable flashing messages

# creates a new database for the app
db = SQLAlchemy(app)

# sets up migration (transfers data from one database to another)
migrate = Migrate(app, db)

class ZipCode(db.Model):
    __tablename__ = "US_Zip_Codes"
    zipcode = db.Column(db.String(5), primary_key=True, nullable=False, unique=True)
    city = db.Column(db.String(50), nullable=False, unique=False)
    state = db.Column(db.String(2), nullable=False, unique=False)

    def __repr__(self):
        return f"Location: {self.zipcode}, {self.city}, {self.state}"

class Stores(db.Model):
    __tablename__ = "Stores"
    store_id = db.Column(db.Integer, primary_key=True, nullable=False, unique=True)
    store_name = db.Column(db.String(20), nullable=False, unique=False)

    def __repr__(self):
        return f"Store Name : {self.store_name}"

class PricingInfo(db.Model):
    __tablename__ = "Pricing_Info"
    id = db.Column(db.Integer, primary_key=True, nullable=False, unique=True)
    product_id = db.Column(db.Integer, unique=False)
    item_name = db.Column(db.String(50), unique=False)
    zipcode = db.Column(db.String(5), unique=False)
    unit = db.Column(db.String(20), unique=False)
    store_id = db.Column(db.Integer, db.ForeignKey('Stores.store_id'))
    price = db.Column(db.Float, unique=False)
    created_date = db.Column(db.String(20), unique=False)
    image_url = db.Column(db.String(75), unique=False)
    pre_price_text = db.Column(db.String(20), unique=False)
    post_price_text = db.Column(db.String(20), unique=False)
    store = relationship('Stores', backref='pricing_items')

    def __repr__(self):
        return f"Product ID: {self.product_id}, Item Name: {self.item_name}, Store ID: {self.store_id}, Zip Code: {self.zipcode}, Price: {self.price}, Unit: {self.unit}, Date of Creation: {self.created_date}, Image URL: {self.image_url}, Pre Price Text: {self.pre_price_text}, Post Price Text: {self.post_price_text}"

class User(db.Model):
    __tablename__ = "Users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(5), nullable=False)

class Refreshes(db.Model):
    __tablename__ = "Refreshes"
    refresh_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.id'))
    store_id = db.Column(db.Integer, db.ForeignKey('Stores.store_id'))
    timestamp = db.Column(db.String(150), nullable=False)
    user = relationship('User', backref='refresh')
    store = relationship('Stores', backref='refresh')

class Alerts(db.Model):
    __tablename__ = "Alerts"
    alert_id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(50), unique=False)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.id'))
    store_id = db.Column(db.Integer, db.ForeignKey('Stores.store_id'))
    zipcode = db.Column(db.String(5), unique=False)
    price_threshold = db.Column(db.Float, unique=False)
    timestamp = db.Column(db.String(150), nullable=False)
    user = relationship('User', backref='alert')
    store = relationship('Stores', backref='alert')

# displayed on the home page
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/test')
def test():
    return render_template('test.html')

@app.route('/zipcode', methods=['GET', 'POST'])
def searchZipCode():
    user_zipcode = request.form.get("user_zipcode") or request.args.get("zipcode")
    item_name = request.form.get("user_itemName") or request.args.get("itemName")
    store_id = request.form.get("user_store") or request.args.get("store_id")
    page = request.args.get("page", 1, type=int)
    per_page = 9
    query = PricingInfo.query
    if user_zipcode:
        if len(user_zipcode) != 5 and user_zipcode.isnumeric():
            flash('Invalid Zip Code', 'danger')
            return redirect('/')
        query = query.filter(PricingInfo.zipcode == user_zipcode)
    if item_name and item_name != "None":
        query = query.filter(PricingInfo.item_name.ilike(f"%{item_name}%"))
    if store_id and store_id != "None":
        query = query.filter(PricingInfo.store_id == store_id)
    pricingInfo = query.paginate(page=page, per_page=per_page)
    zipcode = ZipCode.query.get(user_zipcode) if user_zipcode else None
    stores = Stores.query.all()

    return render_template('index.html', zipcode=zipcode, pricingInfo=pricingInfo, itemName=item_name,stores=stores, selected_store_id=str(store_id))
    # return redirect(url_for('index', zipcode=zipcode, pricingInfo=pricingInfo, itemName=item_name,stores=stores, selected_store_id=str(store_id)))

# main admin page
@app.route('/admin')
def adminPage():
    # user = User.query.filter_by(username=session['GCusername']).first()
    # if user.role == "admin":
    if session['GCuser_role'] == "admin":
        return render_template('admin.html')
    return redirect('/')

# displays store options and refreshes the content of that specific store (i.e. scrapes from that store)
@app.route('/admin/refresh')
def refresh():
    # from models.stores import Stores
    stores = Stores.query.all()
    refreshes = Refreshes.query.order_by(Refreshes.refresh_id.desc()).all() # query refreshes in descending order
    return render_template('refreshList.html', stores=stores, refreshes=refreshes)

@app.route('/admin/refreshInfo', methods=['POST'])
def refreshInfo():
    # 1. image extraction from store url
    store_id = request.form.get("user_store")
    store = Stores.query.get(store_id)

    # 2. data extraction from JSON
    url = f"https://backflipp.wishabi.com/flipp/items/search?locale=en-us&postal_code={USER_ZIPCODE}&q={store.store_name}"
    response = requests.get(url)

    if response.status_code == 200: # if request was successful
        data = response.json()
        items = data["items"]
        PricingInfo.query.filter_by(store_id=store_id, zipcode=USER_ZIPCODE).delete() # delete all instances in the database where the store ID and zip code match
        print(f"Deleted data for {store_id}, {USER_ZIPCODE}")
    else:
        print(f"Error: {response.status_code}")

    # 3. saving data in database
    for item in items:
        if "_L2" in item and item["_L2"] == "Food Items" and item["current_price"]:
            newPricingInfo = PricingInfo()
            newPricingInfo.image_url = item["clean_image_url"]
            newPricingInfo.item_name = item["name"]
            newPricingInfo.store_id = store_id
            newPricingInfo.zipcode = USER_ZIPCODE
            newPricingInfo.price = item["current_price"]
            newPricingInfo.pre_price_text = item["pre_price_text"]
            newPricingInfo.post_price_text = item["post_price_text"]
            newPricingInfo.created_date = datetime.now().strftime("%Y-%m-%d")
            
            for idx, rString in enumerate(categories):
                if re.search(rString, item["name"], re.IGNORECASE):
                    newPricingInfo.product_id = idx+1
            
            db.session.add(newPricingInfo)
    
    refresh = Refreshes(user_id=session['GCuser_id'], store_id=store_id, timestamp=datetime.now().strftime("%Y-%m-%d %I:%M:%S %p"))
    db.session.add(refresh)

    db.session.commit()
    flash(f'Refreshed information for {store.store_name}', 'success')
    return redirect('/admin/refresh')

@app.route('/admin/reports')
def displayReports():
    pricingInfo = PricingInfo.query.all()
    return render_template('reports.html', pricingInfo=pricingInfo)

@app.route('/admin/download')
def download():
    pricingInfo = PricingInfo.query.all()

    # store princingInfo data in a CSV string
    csv_data = "ID,Product ID,Item Name,Store ID,Zip Code,Price,Date of Creation\n"
    for item in pricingInfo:
        csv_data += f"{item.id},{item.product_id},{item.item_name.replace(",", "")},{item.store_id},{item.zipcode},{'%0.2f' % item.price},{item.created_date}\n"
    
    # create a direct download response with the CSV data and appropriate headers
    response = Response(csv_data, content_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=priceInfo.csv"

    return response

@app.route('/admin/users')
def displayUsers():
    users = User.query.all()
    return render_template('users.html', users=users)

@app.route('/admin/users/changeRole', methods=['POST'])
def changeRole():
    id = request.form.get("id")
    user = User.query.get(id)
    user.role = "user" if user.role == "admin" else "admin"
    db.session.commit()
    flash(f'Changed role for {user.username} to {user.role}', 'success')
    return redirect(url_for('displayUsers'))

@app.route('/alerts')
def displayAlerts():
    alerts = Alerts.query.all()
    return render_template('alerts.html', alerts=alerts)

@app.route('/createAlert', methods=['POST'])
def createAlert():
    item_name = request.form.get("item-name")
    zipcode = request.form.get("zip-code")
    price_threshold = request.form.get("price-threshold")
    page = request.form.get("current_page")
    current_item_name = request.form.get("current_item_name")
    store_id = request.form.get("store-id")

    newAlert = Alerts(item_name=item_name, user_id=session['GCuser_id'], store_id=store_id, zipcode=zipcode, price_threshold=price_threshold, timestamp=datetime.now().strftime("%Y-%m-%d %I:%M:%S %p"))
    db.session.add(newAlert)
    db.session.commit()
    flash(f'Added alert for {item_name}', 'success')

    return redirect(url_for('searchZipCode',zipcode=zipcode, page=page, itemName=current_item_name))

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
        
        newUser = User(username=username, email=email, password=hashedPassword, role="user")
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
            session['GCuser_role'] = user.role
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
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
    session.pop('GCuser_role', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

with app.app_context():
    db.create_all()

# if __name__ == "__main__":
app.debug = True # turns on debugger mode
app.run()
