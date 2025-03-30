from flask import Flask, request, redirect, Response, flash, render_template, url_for, session
from flask.templating import render_template
from flask_sqlalchemy import SQLAlchemy
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
    url = db.Column(db.String(150), nullable=False, unique=True)

    def __repr__(self):
        return f"Store Name : {self.store_name}, URL: {self.url}"

class PricingInfo(db.Model):
    __tablename__ = "Pricing_Info"
    id = db.Column(db.Integer, primary_key=True, nullable=False, unique=True)
    product_id = db.Column(db.Integer, unique=False)
    item_name = db.Column(db.String(50), unique=False)
    zipcode = db.Column(db.String(5), unique=False)
    unit = db.Column(db.String(20), unique=False)
    store_id = db.Column(db.Integer, unique=False)
    price = db.Column(db.Float, unique=False)
    created_date = db.Column(db.String(20), unique=False)
    image_url = db.Column(db.String(75), unique=False)
    pre_price_text = db.Column(db.String(20), unique=False)
    post_price_text = db.Column(db.String(20), unique=False)

    def __repr__(self):
        return f"Product ID: {self.product_id}, Item Name: {self.item_name}, Store ID: {self.store_id}, Zip Code: {self.zipcode}, Price: {self.price}, Unit: {self.unit}, Date of Creation: {self.created_date}, Image URL: {self.image_url}, Pre Price Text: {self.pre_price_text}, Post Price Text: {self.post_price_text}"

class User(db.Model):
    __tablename__ = "Users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(5), nullable=False)

# displayed on the home page
@app.route('/')
def index():
    return render_template('index.html')

# @app.route('/zipcodes')
# def listZipCodes():
#     # from models.zipcodes import ZipCode
#     zipcodes = ZipCode.query.all()
#     return render_template('index.html', zipcodes=zipcodes)

@app.route('/zipcode', methods=['POST'])
def searchZipCode():
    # from models.zipcodes import ZipCode
    USER_ZIPCODE = request.form.get("user_zipcode")

    if USER_ZIPCODE and len(USER_ZIPCODE) == 5 and USER_ZIPCODE.isnumeric():
        zipcode = ZipCode.query.get(USER_ZIPCODE)
        pricingInfo = PricingInfo.query.all()
        return render_template('index.html', zipcode=zipcode, pricingInfo=pricingInfo)
    return redirect('/')

# main admin page
@app.route('/admin')
def adminPage():
    user = User.query.filter_by(username=session['GCusername']).first()
    if user.role == "admin":
        return render_template('admin.html')
    return redirect('/')

# displays store options and refreshes the content of that specific store (i.e. imagescrapes from that store)
@app.route('/admin/refresh')
def refresh():
    # from models.stores import Stores
    stores = Stores.query.all()
    return render_template('refreshList.html', stores=stores)

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
    
    db.session.commit()
    print("Refreshed information in the database")
    return redirect('/admin/refresh')

    # import imagescraperv1
    # images_path = imagescraperv1.scrape(store_id, store.url)
    # return redirect('/admin/refresh') # placeholder for now

@app.route('/admin/reports')
def displayReports():
    pricingInfo = PricingInfo.query.all()
    return render_template('reports.html', pricingInfo=pricingInfo)

@app.route('/admin/download')
def download():
    pricingInfo = PricingInfo.query.all()

    # store princingInfo data in a CSV string
    csv_data = "ID,Product ID,Item Name,Store ID,Zip Code,Price,Unit,Date of Creation\n"
    for item in pricingInfo:
        csv_data += f"{item.id},{item.product_id},{item.item_name},{item.store_id},{item.zipcode},{item.price},{item.unit},{item.created_date}\n"
    
    # create a direct download response with the CSV data and appropriate headers
    response = Response(csv_data, content_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=priceInfo.csv"

    return response

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

# if __name__ == "__main__":
app.debug = True # turns on debugger mode
app.run()
