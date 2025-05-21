from flask import Flask, request, redirect, flash, render_template, url_for, session, send_file
from flask.templating import render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_migrate import Migrate, migrate
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import requests
import re
from emailsender import sendEmail
from io import BytesIO
from pdfGenerator import generate_pdf_from_data

USER_ZIPCODE = "22312"

categories = [r"\bapples?\b(?!\s*sauce)",
              r"grape(?!fruit)",
              r"onion(?! ring)",
              r"oranges",
              r"tomato(?! )"]

states = {
        "AL": "Alabama", "AK": "Alaska", "AS": "American Samoa", "AZ": "Arizona",
        "AR": "Arkansas", "CA": "California", "CO": "Colorado", "CT": "Connecticut",
        "DE": "Delaware", "DC": "District of Columbia", "FM": "Federated States of Micronesia", "FL": "Florida",
        "GA": "Georgia", "GU": "Guam", "HI": "Hawaii", "ID": "Idaho",
        "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
        "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
        "MH": "Marshall Islands", "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota",
        "MS": "Mississippi", "MO": "Missouri", "MT": "Montana", "NE": "Nebraska",
        "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico",
        "NY": "New York", "NC": "North Carolina", "ND": "North Dakota", "MP": "Northern Mariana Islands",
        "OH": "Ohio", "OK": "Oklahoma", "OR": "Oregon", "PW": "Palau",
        "PA": "Pennsylvania", "PR": "Puerto Rico", "RI": "Rhode Island", "SC": "South Carolina",
        "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
        "VT": "Vermont", "VI": "Virgin Islands", "VA": "Virginia", "WA": "Washington",
        "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming"
    }

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
    return render_template('index.html', stores=Stores.query.all(), states=states)

@app.route('/test')
def test():
    return render_template('test.html')

@app.route('/zipcode', methods=['GET', 'POST'])
def searchZipCode():
    user_zipcode = request.form.get("user_zipcode") or request.args.get("zipcode")
    item_name = request.form.get("user_itemName") or request.args.get("itemName")
    store_id = request.form.get("user_store") or request.args.get("store_id")
    user_state = request.form.get("user_state") or request.args.get("user_state")
    page = request.args.get("page", 1, type=int)
    per_page = 9
    query = PricingInfo.query
    if user_zipcode:
        if len(user_zipcode) != 5 or not user_zipcode.isnumeric():
            flash('Invalid zip code', 'danger')
            return redirect('/')
        query = query.filter(PricingInfo.zipcode == user_zipcode)
    if item_name and item_name != "None":
        query = query.filter(PricingInfo.item_name.ilike(f"%{item_name}%"))
    if store_id and store_id != "None":
        query = query.filter(PricingInfo.store_id == store_id)
    
    if user_state and not user_zipcode:
        zipcode_user_state = ZipCode.query.filter(ZipCode.state == user_state).all()
        zipcodes = [zipcode.zipcode for zipcode in zipcode_user_state]
        query = query.filter(PricingInfo.zipcode.in_(zipcodes))
        
    pricingInfo = query.paginate(page=page, per_page=per_page)
    zipcode = ZipCode.query.get(user_zipcode) if user_zipcode else None
    stores = Stores.query.all()
    
    return render_template('index.html', zipcode=zipcode, pricingInfo=pricingInfo, itemName=item_name,stores=stores, selected_store_id=str(store_id), user_state=user_state, states=states)
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

    alerts = Alerts.query.all()
    for alert in alerts:
        searchTerm, priceThreshold = alert.item_name, alert.price_threshold
        entries = PricingInfo.query.filter_by(store_id=alert.store.store_id, zipcode=alert.zipcode)
        for entry in entries:
            if searchTerm in entry.item_name and (currentPrice := entry.price) < priceThreshold:
                username = alert.user.username
                print(f"Sending email to {username}")
                htmlContent = f"""\
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="UTF-8">
                        <meta name="viewport" content="width=device-width, initial-scale=1.0">
                        <title>Price Alert - GroceryCheck</title>
                        <style>
                            body {{
                                font-family: Arial, sans-serif;
                                background-color: #f8f9fa;
                                margin: 0;
                                padding: 0;
                            }}
                            .container {{
                                max-width: 600px;
                                margin: 20px auto;
                                background: #ffffff;
                                padding: 20px;
                                border-radius: 10px;
                                box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                                text-align: center;
                            }}
                            h1 {{
                                color: #2c3e50;
                            }}
                            .content {{
                                text-align: left;
                                font-size: 16px;
                                color: #333;
                            }}
                            .highlight {{
                                font-weight: bold;
                                color: #0d6efd;
                            }}
                            .cta-button {{
                                display: inline-block;
                                margin: 20px 0;
                                padding: 12px 20px;
                                background-color: #0d6efd;
                                color: #ffffff !important;
                                text-decoration: none;
                                font-size: 18px;
                                border-radius: 5px;
                                border: none;
                                cursor: pointer;
                            }}
                            .cta-button:hover {{
                                background-color: #218838;
                            }}
                            .footer {{
                                font-size: 14px;
                                color: #777;
                                margin-top: 20px;
                            }}
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <h1>🚨 Price Alert Triggered!</h1>
                            <div class="content">
                                <p>Hi { username },</p>
                                <p>Great news! One of your GroceryCheck alerts just triggered:</p>
                                <ul>
                                    <li><strong>Item:</strong> <span class="highlight">{ alert.item_name }</span></li>
                                    <li><strong>Store:</strong> <span class="highlight">{ alert.store.store_name }</span></li>
                                    <li><strong>ZIP Code:</strong> <span class="highlight">{ alert.zipcode }</span></li>
                                    <li><strong>Your Price Threshold:</strong> <span class="highlight">${ '%0.2f' % priceThreshold }</span></li>
                                    <li><strong>Current Price:</strong> <span class="highlight">${ '%0.2f' % currentPrice }</span></li>
                                </ul>
                                <p>Click below to view the latest deal and see more details:</p>
                                <p><a href="http://localhost:5000/alerts" class="cta-button">View My Alerts</a></p>
                            </div>
                            <div class="footer">
                                <p>Happy saving!<br><strong>The GroceryCheck Team</strong></p>
                            </div>
                        </div>
                    </body>
                    </html>
                    """
                sendEmail(username, alert.user.email, f"Deal found! {alert.item_name} at {alert.store.store_name} is below your price threshold!", htmlContent)

    flash(f'Refreshed information for {store.store_name}', 'success')
    return redirect('/admin/refresh')

@app.route('/admin/reports')
def displayReports():
    pricingInfo = PricingInfo.query.all()
    return render_template('reports.html', pricingInfo=pricingInfo)

@app.route('/admin/download')
def download():
    results = PricingInfo.query.join(PricingInfo.store).with_entities(
        PricingInfo.item_name,
        Stores.store_name,
        PricingInfo.zipcode,
        PricingInfo.price
    ).all()
    results = [(item, storeName, zipcode, '%0.2f' % price) for item, storeName, zipcode, price in results]
    columns = ['Item Name', 'Store', 'ZIP Code', 'Price']

    buffer = BytesIO()
    generate_pdf_from_data(results, columns, buffer)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name='sample_report.pdf', mimetype='application/pdf')

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
    user_state = ZipCode.query.get(zipcode).state
    price_threshold = request.form.get("price-threshold")
    page = request.form.get("current_page")
    current_item_name = request.form.get("current_item_name")
    store_id = request.form.get("store-id")

    newAlert = Alerts(item_name=item_name, user_id=session['GCuser_id'], store_id=store_id, zipcode=zipcode, price_threshold=price_threshold, timestamp=datetime.now().strftime("%Y-%m-%d %I:%M:%S %p"))
    db.session.add(newAlert)
    db.session.commit()
    flash(f'Added alert for {item_name}', 'success')
    return redirect(url_for('searchZipCode',zipcode=zipcode, page=page, itemName=current_item_name, user_state=user_state)) if current_item_name != "None" else redirect(url_for('searchZipCode',zipcode=zipcode, page=page, user_state=user_state))

@app.route('/deleteAlert', methods=['POST'])
def deleteAlert():
    alert_id = request.form.get("alert_id")
    alert = Alerts.query.get(alert_id)
    item_name = alert.item_name

    Alerts.query.filter_by(alert_id=alert_id).delete()
    db.session.commit()

    flash(f'Deleted alert for {item_name}', 'success')
    return redirect(url_for('displayAlerts'))

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

        htmlContent = f"""\
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Welcome to GroceryCheck</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        background-color: #f8f9fa;
                        margin: 0;
                        padding: 0;
                    }}
                    .container {{
                        max-width: 600px;
                        margin: 20px auto;
                        background: #ffffff;
                        padding: 20px;
                        border-radius: 10px;
                        box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                        text-align: center;
                    }}
                    h1 {{
                        color: #2c3e50;
                    }}
                    .content {{
                        text-align: left;
                        font-size: 16px;
                        color: #333;
                    }}
                    .cta-button {{
                        display: inline-block;
                        margin: 20px 0;
                        padding: 12px 20px;
                        background-color: #0d6efd;
                        color: #ffffff !important;
                        text-decoration: none;
                        font-size: 18px;
                        border-radius: 5px;
                        border: none;
                        cursor: pointer;
                    }}
                    .cta-button:hover {{
                        background-color: #218838;
                    }}
                    .footer {{
                        font-size: 14px;
                        color: #777;
                        margin-top: 20px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Welcome to GroceryCheck! 🎉</h1>
                    <div class="content">
                        <p>Hi { username },</p>
                        <p>We're excited to help you find the best grocery deals and make shopping easier than ever.</p>
                        <p>With GroceryCheck, you can:</p>
                        <ul>
                            <li> Compare weekly ads from top stores</li>
                            <li> Search a variety of grocery products at numerous locations</li>
                            <li> Download weekly grocery retail reports</li>
                        </ul>
                        <p><a href="http://localhost:5000/" class="cta-button">Get Started</a></p>
                        <!-- <p>Need help? Visit our <a href="https://google.com">Help Center</a>.</p> -->
                    </div>
                    <div class="footer">
                        <p>Happy shopping!<br><strong>The GroceryCheck Team</strong></p>
                    </div>
                </div>
            </body>
            </html>
            """
        sendEmail(username, email, f"Welcome to GroceryCheck, {username}!", htmlContent)  # send welcome email (usually goes to spam folder)

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
            flash('Invalid username or password', 'danger')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/forgotPassword', methods=['POST'])
def forgotPassword():
    # check if user with email exists
    email = request.form.get("email-address")
    user = User.query.filter_by(email=email).first()
    if not user:
        flash('User with this email does not exist. Please enter a different email.', 'danger')
        return redirect(url_for('login'))

    # create and save new password
    newPassword = "gC999$2o25"
    user.password = generate_password_hash(newPassword, method='pbkdf2:sha256')
    db.session.commit()

    # send email with new password
    username = user.username
    htmlContent = f"""\
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Password Reset - GroceryCheck</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #f8f9fa;
                    margin: 0;
                    padding: 0;
                }}
                .container {{
                    max-width: 600px;
                    margin: 20px auto;
                    background: #ffffff;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                    text-align: center;
                }}
                h1 {{
                    color: #2c3e50;
                }}
                .content {{
                    text-align: left;
                    font-size: 16px;
                    color: #333;
                }}
                .password-box {{
                    background-color: #f1f1f1;
                    padding: 10px;
                    font-size: 18px;
                    font-weight: bold;
                    color: #000;
                    border-radius: 5px;
                    text-align: center;
                    margin: 20px 0;
                }}
                .cta-button {{
                    display: inline-block;
                    margin: 20px 0;
                    padding: 12px 20px;
                    background-color: #0d6efd;
                    color: #ffffff !important;
                    text-decoration: none;
                    font-size: 18px;
                    border-radius: 5px;
                    border: none;
                    cursor: pointer;
                }}
                .cta-button:hover {{
                    background-color: #218838;
                }}
                .footer {{
                    font-size: 14px;
                    color: #777;
                    margin-top: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Password Reset Successful</h1>
                <div class="content">
                    <p>Hi { username },</p>
                    <p>You recently requested to reset your password. Here's your new password:</p>
                    <div class="password-box">{ newPassword }</div>
                    <p>Use the button below to log back into your account:</p>
                    <p><a href="http://localhost:5000/login" class="cta-button">Log In</a></p>
                    <p>If you didn't request this change, please contact us immediately.</p>
                </div>
                <div class="footer">
                    <p>Stay secure!<br><strong>The GroceryCheck Team</strong></p>
                </div>
            </div>
        </body>
        </html>
        """
    sendEmail(username, email, f"Your New GroceryCheck Password", htmlContent)
    flash(f'An email containing your new password was sent to {email}. Please check your inbox and log in.', 'success')
    return redirect(url_for('login'))

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
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

with app.app_context():
    db.create_all()

# if __name__ == "__main__":
app.debug = True # turns on debugger mode
app.run()
