from flask import Flask, request, redirect, Response
from flask.templating import render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, migrate

app = Flask(__name__) # creates a new Flask app
app.debug = True # turns on debugger mode

# link the database to the Flask app's config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///SRdata.db'

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
    store_id = db.Column(db.Integer, primary_key=True, nullable=False, unique=True)
    store_name = db.Column(db.String(20), nullable=False, unique=False)
    url = db.Column(db.String(150), nullable=False, unique=True)

    def __repr__(self):
        return f"Store Name : {self.store_name}, URL: {self.url}"

class PricingInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False, unique=True)
    product_id = db.Column(db.Integer, unique=False)
    item_name = db.Column(db.String(50), unique=False)
    zipcode = db.Column(db.String(5), unique=False)
    unit = db.Column(db.String(20), unique=False)
    store_id = db.Column(db.Integer, unique=False)
    price = db.Column(db.Float, unique=False)
    created_date = db.Column(db.String(20), unique=False)

    def __repr__(self):
        return f"Product ID: {self.product_id}, Item Name: {self.item_name}, Store ID: {self.store_id}, Zip Code: {self.zipcode}, Price: {self.price}, Unit: {self.unit}, Date of Creation: {self.created_date}"

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
    user_zipcode = request.form.get("user_zipcode")

    if user_zipcode and len(user_zipcode) == 5 and user_zipcode.isnumeric():
        zipcode = ZipCode.query.get(user_zipcode)
        return render_template('index.html', zipcode=zipcode)
    return redirect('/')

# main admin page
@app.route('/admin')
def adminPage():
    return render_template('admin.html')

# displays store options and refreshes the content of that specific store (i.e. imagescrapes from that store)
@app.route('/admin/refresh')
def refresh():
    # from models.stores import Stores
    stores = Stores.query.all()
    return render_template('refreshList.html', stores=stores)

@app.route('/admin/reports')
def displayReports():
    pricingInfo = PricingInfo.query.all()
    return render_template('reports.html', pricingInfo=pricingInfo)

@app.route('/download')
def download():
    pricingInfo = PricingInfo.query.all()

    # store princingInfo data in a CSV string
    csv_data = "ID,Product ID,Item Name,Store ID,Zip Code,Price,Unit,Date of Creation\n"
    for item in pricingInfo:
        csv_data += f"{item.id},{item.product_id},{item.item_name},{item.store_id},{item.zipcode},{item.price},{item.unit},{item.created_date}\n"
    
    # Create a direct download response with the CSV data and appropriate headers
    response = Response(csv_data, content_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=priceInfo.csv"

    return response

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run()
